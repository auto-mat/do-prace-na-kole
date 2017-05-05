# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2015 o.s. Auto*Mat
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
import datetime

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from . import mailing, models, results, tasks, views


def recalculate_competitions_results(modeladmin, request, queryset):
    tasks.recalculate_competitions_results.apply_async(args=(list(queryset.values_list('pk', flat=True)),))
    if request:
        modeladmin.message_user(request, _(u"Zadáno přepočítání %s výsledků" % (queryset.count())))


recalculate_competitions_results.short_description = _(u"Přepočítat výsledku vybraných soutěží")


def normalize_questionnqire_admissions(modeladmin, request, queryset):
    queryset = queryset.filter(competition_type='questionnaire', competitor_type='single_user')
    for competition in queryset.all():
        competition.user_attendance_competitors.clear()
        for question in competition.question_set.all():
            for answer in question.answer_set.all():
                if answer.has_any_answer():
                    competition.user_attendance_competitors.add(answer.user_attendance)
        competition.save()
    if request:
        modeladmin.message_user(request, _(u"Úspěšně obnoveno %s přihlášek podle odpovědí na dotazník" % (queryset.count())))


normalize_questionnqire_admissions.short_description = _(u"Obnovit přihlášky podle odpovědí na dotazník")


# ---- USER_ATTENDANCE -----

def touch_items(modeladmin, request, queryset):
    tasks.touch_items.apply_async(
        kwargs={
            'pks': list(queryset.values_list('pk', flat=True)),
            'object_app_label': queryset.model._meta.app_label,
            'object_model_name': queryset.model.__name__.lower(),
        },
    )
    modeladmin.message_user(request, _("Obnova %s denormalizovaných položek byla zadána ke zpracování" % queryset.count()))


touch_items.short_description = _("Obnovit denormalizované sloupce")


def recalculate_results(modeladmin, request, queryset):
    for user_attendance in queryset.all():
        results.recalculate_result_competitor_nothread(user_attendance)
    modeladmin.message_user(request, _(u"Výsledky přepočítány"))


recalculate_results.short_description = _(u"Přepočítat výsledky soutěží pro vybrané účasti v kampani")


def show_distance(modeladmin, request, queryset):
    trips_query = models.Trip.objects.filter(user_attendance__in=queryset, commute_mode__in=('bicycle', 'by_foot'))
    length = views.distance(trips_query)
    trips = views.trips(trips_query)
    modeladmin.message_user(request, "Ujetá vzdálenost: %s Km v %s jízdách" % (length, trips))


show_distance.short_description = _(u"Ukázat ujetou vzdálenost")


def assign_vouchers(modeladmin, request, queryset):
    count = queryset.count()
    vouchers = models.Voucher.objects.filter(
        user_attendance=None,
        campaign__slug=request.subdomain,
    ).all()[:count]
    if vouchers.count() != count:
        messages.error(request, _(u"Není dost volných voucherů"))
        return
    for user_attendance, voucher in zip(queryset, vouchers):
        voucher.user_attendance = user_attendance
        voucher.save()
    modeladmin.message_user(request, _(u"Úspěšně přiřazeno %s voucherů" % (count)))


assign_vouchers.short_description = _(u"Přiřadit vouchery")


def update_mailing(modeladmin, request, queryset):
    pk_list = list(queryset.values_list('pk', flat=True))
    tasks.update_mailing.apply_async(args=(pk_list,))
    modeladmin.message_user(request, _("Aktualizace mailing listu byla úspěšne zadána pro %s uživatelů") % queryset.count())


update_mailing.short_description = _(u"Aktualizovat mailing list")


def approve_am_payment(modeladmin, request, queryset):
    for user_attendance in queryset:
        payment = user_attendance.representative_payment
        payment_description = "\nPayment realized by %s\n" % request.user.username
        if payment:
            payment.status = models.Status.DONE
            payment.description += payment_description
            payment.save()
        else:
            models.Payment.objects.create(
                user_attendance=user_attendance,
                status=models.Status.DONE,
                description=payment_description,
                amount=0,
            )
    modeladmin.message_user(request, _(u"Platby potvrzeny"))


approve_am_payment.short_description = _(u"Potvrdit platbu")


def remove_mailing_id(modeladmin, request, queryset):
    for userprofile in queryset:
        userprofile.mailing_id = None
        userprofile.mailing_hash = None
        userprofile.save()
    modeladmin.message_user(request, _(u"Mailing ID a hash byl úspěšne odebrán %s profilům") % queryset.count())


remove_mailing_id.short_description = _(u"Odstranit mailing ID a hash")


def show_distance_trips(modeladmin, request, queryset):
    length = views.distance(queryset)
    trips = views.trips(queryset)
    modeladmin.message_user(request, "Ujetá vzdálenost: %s Km v %s jízdách" % (length, trips))


show_distance_trips.short_description = _(u"Ukázat ujetou vzdálenost")


def update_mailing_coordinator(modeladmin, request, queryset):
    for company_admin in queryset:
        user_attendance = company_admin.user_attendance()
        if user_attendance:
            mailing.add_or_update_user_synchronous(user_attendance, ignore_hash=True)
        else:
            mailing.add_or_update_user_synchronous(company_admin, ignore_hash=True)

    modeladmin.message_user(request, _("Úspěšně aktualizován mailing pro %s koordinátorů") % queryset.count())


update_mailing_coordinator.short_description = _(u"Aktualizovat mailing list")


def mark_invoices_paid(modeladmin, request, queryset):
    for invoice in queryset.all():
        invoice.paid_date = datetime.date.today()
        invoice.save()
    modeladmin.message_user(request, _("%s faktur označeno jako 'zaplaceno'") % queryset.count())


mark_invoices_paid.short_description = _("Označit faktury jako zaplacené")


def send_notifications(modeladmin, request, queryset):
    tasks.send_unfilled_rides_notification.apply_async(
        kwargs={
            'pks': list(queryset.values_list('pk', flat=True)),
            'campaign_slug': request.subdomain,
        },
    )
    modeladmin.message_user(request, _("Odeslání %s notifikačních emailů bylo zadáno" % queryset.count()))


send_notifications.short_description = _("Odeslat notifikaci nevyplněných jízd")
