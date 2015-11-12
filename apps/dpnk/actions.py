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
#import results
from . import models, mailing
from django.contrib import messages


def recalculate_competitions_results(modeladmin, request, queryset):
    for competition in queryset.all():
        competition.recalculate_results()
recalculate_competitions_results.short_description = _(u"Přepočítat výsledku vybraných soutěží")


def normalize_questionnqire_admissions(modeladmin, request, queryset):
    for competition in queryset.all():
        if competition.type != 'questionnaire' or competition.competitor_type != 'single_user':
            continue
        competition.user_attendance_competitors.clear()
        for question in competition.question_set.all():
            for answer in question.answer_set.all():
                if answer.has_any_answer():
                    competition.user_attendance_competitors.add(answer.user_attendance)
        competition.save()
normalize_questionnqire_admissions.short_description = _(u"Obnovit přihlášky podle odpovědí na dotazník")


# ---- USER_ATTENDANCE -----

def touch_user_attendance(modeladmin, request, queryset):
    for user_attendance in queryset.all():
        user_attendance.save()
    modeladmin.message_user(request, _(u"Touch proběhl úspěšně"))
touch_user_attendance.short_description = _(u"Touch vybrané účastníky v kampani")


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
        payment = user_attendance.payment()['payment']
        if payment and payment.status == models.Payment.Status.NEW:
            payment.status = models.Payment.Status.DONE
            payment.description += "\nPayment realized by %s\n" % request.user.username
            payment.save()
    modeladmin.message_user(request, _(u"Platby potvrzeny"))
approve_am_payment.short_description = _(u"Potvrdit platbu")
