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

from django.utils.translation import ugettext_lazy as _
from . import results, views, models, mailing, util
from django.contrib import messages
import datetime


def recalculate_competitions_results(modeladmin, request, queryset):
    for competition in queryset.all():
        competition.recalculate_results()
    if request:
        modeladmin.message_user(request, _(u"Úspěšně přepočítáno %s výsledků" % (queryset.count())))
recalculate_competitions_results.short_description = _(u"Přepočítat výsledku vybraných soutěží")


def normalize_questionnqire_admissions(modeladmin, request, queryset):
    queryset = queryset.filter(type='questionnaire', competitor_type='single_user')
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
    util.rebuild_denorm_models(queryset)
    modeladmin.message_user(request, _("Obnova denormalizovaných sloupců proběhla úspěšně"))
touch_items.short_description = _("Obnovit denormalizované sloupce")


def recalculate_results(modeladmin, request, queryset):
    for user_attendance in queryset.all():
        results.recalculate_result_competitor_nothread(user_attendance)
    modeladmin.message_user(request, _(u"Výsledky přepočítány"))
recalculate_results.short_description = _(u"Přepočítat výsledky soutěží pro vybrané účasti v kampani")


def show_distance(modeladmin, request, queryset):
    trips_query = models.Trip.objects.filter(user_attendance__in=queryset)
    length = views.distance(trips_query)
    trips = views.trips(trips_query)
    modeladmin.message_user(request, "Ujetá vzdálenost: %s Km v %s jízdách" % (length, trips))
show_distance.short_description = _(u"Ukázat ujetou vzdálenost")


def assign_vouchers(modeladmin, request, queryset):
    count = queryset.count()
    vouchers = models.Voucher.objects.filter(user_attendance=None).all()[:count]
    if vouchers.count() != count:
        messages.error(request, _(u"Není dost volných voucherů"))
        return
    for user_attendance, voucher in zip(queryset, vouchers):
        voucher.user_attendance = user_attendance
        voucher.save()
    modeladmin.message_user(request, _(u"Úspěšně přiřazeno %s voucherů" % (count)))
assign_vouchers.short_description = _(u"Přiřadit vouchery")


def add_trips(modeladmin, request, queryset):
    count = queryset.count()
    for user_attendance in queryset.all():
        user_attendance.get_all_trips()
    modeladmin.message_user(request, _(u"Úspěšně přiřazeno %s cest" % (count)))
add_trips.short_description = _(u"Vytvořit cesty")


def update_mailing(modeladmin, request, queryset):
    for user_attendance in queryset:
        mailing.add_or_update_user_synchronous(user_attendance, ignore_hash=True)
    modeladmin.message_user(request, _(u"Mailing list byl úspěšne aktualizován %s uživatelům") % queryset.count())
update_mailing.short_description = _(u"Aktualizovat mailing list")


def approve_am_payment(modeladmin, request, queryset):
    for user_attendance in queryset:
        payment = user_attendance.representative_payment
        if payment and payment.status == models.Status.NEW:
            payment.status = models.Status.DONE
            payment.description += "\nPayment realized by %s\n" % request.user.username
            payment.save()
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

    modeladmin.message_user(request, _(u"Úspěšně aktualiován mailing pro %s koordinátorů") % queryset.count())
update_mailing_coordinator.short_description = _(u"Aktualizovat mailing list")


def create_batch(modeladmin, request, queryset):
    campaign = models.Campaign.objects.get(slug=request.subdomain)
    delivery_batch = models.DeliveryBatch()
    delivery_batch.campaign = campaign
    delivery_batch.add_packages_on_save = False
    delivery_batch.save()
    delivery_batch.add_packages(user_attendances=queryset)
    delivery_batch.add_packages_on_save = True
    delivery_batch.save()
    modeladmin.message_user(request, _(u"Vytvořena nová dávka obsahující %s položek") % queryset.count())
create_batch.short_description = _(u"Vytvořit dávku z vybraných uživatelů")


def mark_invoices_paid(modeladmin, request, queryset):
    for invoice in queryset.all():
        invoice.paid_date = datetime.date.today()
        invoice.save()
    modeladmin.message_user(request, _("%s faktur označeno jako 'zaplaceno'") % queryset.count())
mark_invoices_paid.short_description = _("Označit faktury jako zaplacené")
