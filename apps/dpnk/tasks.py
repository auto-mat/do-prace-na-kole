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
from urllib.parse import urlparse
from urllib.request import urlopen

import redis
from celery import shared_task

import denorm

from dj_fiobank_payments.statement import parse

from django.conf import settings
from django.contrib import contenttypes
from django.urls import reverse
from django.utils import translation
from django.utils.translation import ugettext as _

from notifications.signals import notify

from celery.utils.log import get_task_logger

import smmapdfs.email
import smmapdfs.tasks

from . import email, mailing, util
from .models import (
    Campaign,
    CityInCampaign,
    Company,
    Competition,
    Invoice,
    Team,
    UserAttendance,
    Voucher,
    payments_to_invoice,
)

logger = get_task_logger(__name__)


@shared_task(bind=True)
def recalculate_competitor_task(self, user_attendance_pk):
    from . import results

    user_attendance = UserAttendance.objects.get(pk=user_attendance_pk)
    if user_attendance.team is not None:
        util.rebuild_denorm_models([user_attendance.team])
    denorm.flush()
    results.recalculate_result_competitor_nothread(user_attendance)


@shared_task(bind=True)
def recalculate_competitions_results(self, pks=None, campaign_slug=""):
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
        content_type = contenttypes.models.ContentType.objects.get(
            app_label=object_app_label, model=object_model_name
        )
        denorm.models.DirtyInstance.objects.create(
            content_type=content_type,
            object_id=pk,
        )
        denorm.flush()
    return len(pks)


@shared_task(bind=True)
def touch_user_attendances(self, campaign_slug=""):
    queryset = UserAttendance.objects.filter(campaign__slug=campaign_slug)
    util.rebuild_denorm_models(queryset)
    return len(queryset)


@shared_task(bind=True)
def touch_teams(self, campaign_slug=""):
    queryset = Team.objects.filter(campaign__slug=campaign_slug)
    util.rebuild_denorm_models(queryset)
    return len(queryset)


@shared_task(bind=True)
def parse_statement(self, days_back=7):
    parse(days_back=days_back)


def get_notification_queryset(
    model, days_between_notifications, pks=None, campaign_slug=""
):
    campaign = Campaign.objects.get(slug=campaign_slug)
    queryset = model.get_stale_objects(days_between_notifications * 24 * 60 * 60)
    q = {}
    if issubclass(model, Invoice):
        from django.conf import settings

        date_from_create_invoices = settings.FAKTUROID["date_from_create_invoices"]
        if date_from_create_invoices:
            q = {"created__lt": date_from_create_invoices}
    if not pks:
        return queryset.filter(campaign=campaign, **q)
    else:
        return queryset.filter(pk__in=pks, campaign=campaign, **q)


@shared_task(bind=True)
def send_unfilled_rides_notification(self, pks=None, campaign_slug=""):
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
        payment_status__in=("done", "no_admission"),
        approved_for_team="approved",
    ).exclude(
        user_trips__date__gte=min_trip_date,
    )
    for user_attendance in queryset:
        email.unfilled_rides_mail(user_attendance, days_unfilled)
    len_queryset = len(queryset)
    UserAttendance.update_sync_time(queryset)
    return len_queryset


@shared_task(bind=True)
def send_unpaid_invoice_notification(self, pks=None, campaign_slug="", days_unpaid=7):
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
def send_new_invoice_notification(self, pks=None, campaign_slug=""):
    campaign = Campaign.objects.get(slug=campaign_slug)
    queryset = Invoice.objects.filter(pk__in=pks, campaign=campaign)
    for invoice in queryset:
        email.new_invoice_mail(invoice)
    Invoice.update_sync_time(queryset)


@shared_task(bind=True)
def create_invoice_if_needed(self, pks=[], campaign_slug=""):
    for pk in pks:
        company = Company.objects.get(pk=pk)
        campaign = Campaign.objects.get(slug=campaign_slug)
        logger.info(f"Company name: {company}")
        logger.info(f"Campaign: {campaign}")
        payments = payments_to_invoice(company, campaign)
        logger.info(f"Number of payments: {payments.count()}")
        if payments:
            Invoice.objects.create(
                company=company,
                campaign=campaign,
            )


@shared_task(bind=True)
def request_page(self, page):
    urlopen(page)


@shared_task(bind=True)
def assign_voucher(self, voucher_pk, userattendance_pk):
    current_language = translation.get_language()
    # Assign voucher
    voucher = Voucher.objects.get(pk=voucher_pk)
    user_attendance = UserAttendance.objects.get(pk=userattendance_pk)
    voucher.user_attendance = user_attendance
    voucher.save()
    translation.activate(user_attendance.userprofile.language)
    # Send notification
    notify.send(
        user_attendance,
        recipient=user_attendance.userprofile.user,
        verb=_("{name}: Byl vám přiřazen nový voucher s kódem {token}").format(
            name=voucher.voucher_type1.name, token=voucher.token
        ),
        url=reverse("profil") + "#third-party-vouchers",
        icon=voucher.voucher_type1.teaser_img.url,
    )
    # Send email
    base_url = util.get_base_url(slug=user_attendance.campaign.slug)

    def continuation(sandwich):
        try:
            smmapdfs.email.send_pdfsandwich(sandwich, base_url)
        except smmapdfs.models.pdfsandwich_email.PdfSandwichEmail.DoesNotExist:
            pass

    content_type = contenttypes.models.ContentType.objects.get_for_model(voucher)
    smmapdfs.tasks.make_pdfsandwich(
        content_type.app_label,
        content_type.model,
        voucher.pk,
        continuation,
    )
    translation.activate(current_language)


@shared_task
def flush_denorm():
    denorm.flush()


@shared_task
def generate_anonymized_trips_table(cities_to_export=None, rebuild_anon_table=False):
    from django.db import connection

    sql = """
CREATE OR REPLACE FUNCTION has_longer_section_than(line geometry, max_length integer) RETURNS boolean as $$
    DECLARE
       cur_length integer;
    BEGIN
    FOR i IN 1..ST_NPoints(line)-1
    LOOP
       cur_length := ST_distance(ST_PointN(line, i)::geography, ST_PointN(line, i+1)::geography);
       IF cur_length>max_length THEN
           RETURN True;
       END IF;
    END LOOP;
    RETURN False;
END;
$$ LANGUAGE plpgsql;

drop table if exists dpnk_trip_anonymized;
CREATE TABLE dpnk_trip_anonymized as select * from (
   select a.id, a.campaign_id, age_group, sex, commute_mode, city, occupation_id, ST_LineSubstring(a.track, 100/st_length(a.track::geography), 1 - 100/st_length(a.track::geography)) as the_geom from (
   SELECT dpnk_trip.id, dpnk_userattendance.campaign_id, dpnk_userprofile.age_group, dpnk_userprofile.sex, dpnk_commutemode.slug as commute_mode, dpnk_city.slug as city, dpnk_userprofile.occupation_id, (ST_Dump(dpnk_trip.track::geometry)).geom AS track from dpnk_trip
      join dpnk_userattendance on (dpnk_trip.user_attendance_id = dpnk_userattendance.id)
      join dpnk_userprofile on (dpnk_userattendance.userprofile_id = dpnk_userprofile.id)
      join dpnk_team on (dpnk_userattendance.team_id = dpnk_team.id)
      join dpnk_subsidiary on (dpnk_team.subsidiary_id = dpnk_subsidiary.id)
      join dpnk_city on (dpnk_subsidiary.city_id = dpnk_city.id)
      join dpnk_commutemode on (dpnk_trip.commute_mode_id = dpnk_commutemode.id)
   ) as a
      where a.track is not null and st_numpoints(a.track::geometry) > 15 and st_length(a.track::geography)<100000 and st_length(a.track::geography)>200 and not has_longer_section_than(a.track::geometry, 1000)
) as b where st_numpoints(b.the_geom)>15;
GRANT ALL PRIVILEGES ON TABLE dpnk_trip_anonymized TO dpnk;
CREATE INDEX dpnk_trip_anonymized_idx ON dpnk_trip_anonymized USING GIST (the_geom);
    """

    if rebuild_anon_table:
        with connection.cursor() as cursor:
            cursor.execute(sql)

    if cities_to_export:
        from uuid import uuid4
        from subprocess import check_output, STDOUT, CalledProcessError
        from django.conf import settings
        from django.core.files.base import File
        import tempfile
        import os

        for city_pk in cities_to_export:
            city = CityInCampaign.objects.get(pk=city_pk)
            city.data_export_password = str(uuid4())[:30]
            db_settings = settings.DATABASES["default"]

            with tempfile.TemporaryDirectory() as tmpdirname:
                os.chdir(tmpdirname)
                try:
                    check_output(
                        [
                            "pgsql2shp",
                            "-f",
                            city.city.slug + ".shp",
                            "-h",
                            db_settings["HOST"],
                            "-p",
                            db_settings["PORT"],
                            "-u",
                            db_settings["USER"],
                            "-P",
                            db_settings["PASSWORD"],
                            db_settings["NAME"],
                            "SELECT * FROM dpnk_trip_anonymized WHERE city = '"
                            + city.city.slug
                            + "'",
                        ],
                        stderr=STDOUT,
                    )
                except CalledProcessError:
                    pass
                check_output(
                    [
                        "zip",
                        city.city.slug + ".zip",
                        "-e",
                        "-P",
                        city.data_export_password,
                    ]
                    + [f for f in os.listdir(tmpdirname)],
                    stderr=STDOUT,
                )
                with open(city.city.slug + ".zip", "rb") as fd:
                    city.data_export.save(
                        city.city.slug + "-" + city.campaign.slug_identifier + ".zip",
                        File(fd),
                    )
            city.save()


@shared_task()
def check_celerybeat_liveness(set_key=True):
    """Check Celery Beat liveness with setting Redis key"""
    parsed_redis_url = urlparse(settings.BROKER_URL)
    redis_instance = redis.StrictRedis(
        host=parsed_redis_url.hostname,
        port=parsed_redis_url.port if parsed_redis_url.port else 6379,
        db=0,
    )
    if set_key:
        redis_instance.set(
            settings.CELERYBEAT_LIVENESS_REDIS_UNIQ_KEY,
            settings.CELERYBEAT_LIVENESS_REDIS_UNIQ_KEY,
            ex=120,
        )
    else:
        return redis_instance.get(settings.CELERYBEAT_LIVENESS_REDIS_UNIQ_KEY)


@shared_task(bind=True)
def refresh_materialized_view(materialized_view):
    from django.db import connection

    with connection.cursor() as cursor:
        if isinstance(materialized_view, (list, tuple, set)):
            for view in materialized_view:
                cursor.execute("REFRESH MATERIALIZED VIEW %s", [view])
        else:
            cursor.execute("REFRESH MATERIALIZED VIEW %s", [materialized_view])
