# -*- coding: utf-8 -*-
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2017 o.s. Auto*Mat
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
from __future__ import absolute_import

from datetime import timedelta

from celery import shared_task

import denorm

from django.contrib import contenttypes

from . import email, mailing, util
from .models import Campaign, Company, Competition, Invoice, Team, UserAttendance, payments_to_invoice
from .statement import parse


@shared_task(bind=True)
def recalculate_competitor_task(self, user_attendance_pk):
    from . import results
    user_attendance = UserAttendance.objects.get(pk=user_attendance_pk)
    if user_attendance.team is not None:
        util.rebuild_denorm_models([user_attendance.team])
    denorm.flush()
    results.recalculate_result_competitor_nothread(user_attendance)


@shared_task(bind=True)
def recalculate_competitions_results(self, pks=None, campaign_slug=''):
    if not pks:
        queryset = Competition.objects.filter(campaign__slug=campaign_slug)
    else:
        queryset = Competition.objects.filter(pk__in=pks)
    for competition in queryset:
        competition.recalculate_results()
    return len(queryset)


@shared_task(bind=True)
def update_mailing(self, user_attendance_pks):
    user_attendances = UserAttendance.objects.filter(pk__in=user_attendance_pks)
    for user_attendance in user_attendances:
        mailing.add_or_update_user_synchronous(user_attendance, ignore_hash=True)


@shared_task(bind=True)
def touch_items(self, pks, object_app_label, object_model_name):
    for pk in pks:
        content_type = contenttypes.models.ContentType.objects.get(app_label=object_app_label, model=object_model_name)
        denorm.models.DirtyInstance.objects.create(
            content_type=content_type,
            object_id=pk,
        )
        denorm.flush()
    return len(pks)


@shared_task(bind=True)
def touch_user_attendances(self, campaign_slug=''):
    queryset = UserAttendance.objects.filter(campaign__slug=campaign_slug)
    util.rebuild_denorm_models(queryset)
    return len(queryset)


@shared_task(bind=True)
def touch_teams(self, campaign_slug=''):
    queryset = Team.objects.filter(campaign__slug=campaign_slug)
    util.rebuild_denorm_models(queryset)
    return len(queryset)


@shared_task(bind=True)
def parse_statement(self, days_back=7):
    parse(days_back=days_back)


def get_notification_queryset(model, days_between_notifications, pks=None, campaign_slug=''):
    campaign = Campaign.objects.get(slug=campaign_slug)
    queryset = model.get_stale_objects(days_between_notifications * 24 * 60 * 60)
    if not pks:
        return queryset.filter(campaign=campaign)
    else:
        return queryset.filter(pk__in=pks, campaign=campaign)


@shared_task(bind=True)
def send_unfilled_rides_notification(self, pks=None, campaign_slug=''):
    campaign = Campaign.objects.get(slug=campaign_slug)
    days_unfilled = campaign.days_active - 2
    date = util.today()
    min_trip_date = date - timedelta(days=days_unfilled)
    queryset = get_notification_queryset(
        UserAttendance,
        days_unfilled,
        pks=pks,
        campaign_slug=campaign_slug,
    )
    queryset = queryset.filter(
        payment_status__in=('done', 'no_admission'),
        approved_for_team='approved',
    ).exclude(
        user_trips__date__gte=min_trip_date,
    )
    for user_attendance in queryset:
        email.unfilled_rides_mail(user_attendance, days_unfilled)
    len_queryset = len(queryset)
    UserAttendance.update_sync_time(queryset)
    return len_queryset


@shared_task(bind=True)
def send_unpaid_invoice_notification(self, pks=None, campaign_slug=''):
    days_unpaid = 14
    queryset = get_notification_queryset(
        Invoice,
        days_unpaid,
        pks=pks,
        campaign_slug=campaign_slug,
    )
    for invoice in queryset:
        email.unpaid_invoice_mail(invoice)
    len_queryset = len(queryset)
    Invoice.update_sync_time(queryset)
    return len_queryset


@shared_task(bind=True)
def send_new_invoice_notification(self, pks=None, campaign_slug=''):
    campaign = Campaign.objects.get(slug=campaign_slug)
    queryset = Invoice.objects.filter(pk__in=pks, campaign=campaign)
    for invoice in queryset:
        email.new_invoice_mail(invoice)
    Invoice.update_sync_time(queryset)


@shared_task(bind=True)
def create_invoice_if_needed(self, pk=None, campaign_slug=''):
    company = Company.objects.get(pk=pk)
    campaign = Campaign.objects.get(slug=campaign_slug)
    payments = payments_to_invoice(company, campaign)
    if payments:
        Invoice.objects.create(
            company=company,
            campaign=campaign,
        )
