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
from collections import Counter
import datetime

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from . import mailing, models, results, tasks, views


def recalculate_competitions_results(modeladmin, request, queryset):
    tasks.recalculate_competitions_results.apply_async(
        args=(list(queryset.values_list("pk", flat=True)),)
    )
    if request:
        modeladmin.message_user(
            request, _("Zadáno přepočítání %s výsledků" % (queryset.count()))
        )


recalculate_competitions_results.short_description = _(
    "Přepočítat výsledku vybraných soutěží"
)


def batch_download_action_generator(field):
    def batch_download(modeladmin, request, queryset):
        links = []
        for q in queryset:
            file_field = getattr(q, field)
            if file_field:
                links.append(file_field.url)
        return HttpResponse("\n".join(links), content_type="text/plain")

    return batch_download


invoice_pdf_batch_download = batch_download_action_generator("invoice_pdf")
invoice_pdf_batch_download.short_description = _("Hromadně stáhnout PDF")
invoice_pdf_batch_download.__name__ = (
    "invoice_pdf_batch_download"  # to distingush it for Django admin
)

invoice_xml_batch_download = batch_download_action_generator("invoice_xml")
invoice_xml_batch_download.short_description = _("Hromadně stáhnout XML")


# ---- USER_ATTENDANCE -----


def touch_items(modeladmin, request, queryset):
    tasks.touch_items.apply_async(
        kwargs={
            "pks": list(queryset.values_list("pk", flat=True)),
            "object_app_label": queryset.model._meta.app_label,
            "object_model_name": queryset.model.__name__.lower(),
        },
    )
    modeladmin.message_user(
        request,
        _(
            "Obnova %s denormalizovaných položek byla zadána ke zpracování"
            % queryset.count()
        ),
    )


touch_items.short_description = _("Obnovit denormalizované sloupce")


def recalculate_results(modeladmin, request, queryset):
    for user_attendance in queryset.all():
        results.recalculate_result_competitor_nothread(user_attendance)
    modeladmin.message_user(request, _("Výsledky přepočítány"))


recalculate_results.short_description = _(
    "Přepočítat výsledky soutěží pro vybrané účasti v kampani"
)


def show_distance(modeladmin, request, queryset):
    trips_query = models.Trip.objects.filter(
        user_attendance__in=queryset, commute_mode__slug__in=("bicycle", "by_foot")
    )
    length = views.results_and_competitions.distance(trips_query)
    trips = views.results_and_competitions.trips(trips_query)
    modeladmin.message_user(
        request, "Ujetá vzdálenost: %s Km v %s jízdách" % (length, trips)
    )


show_distance.short_description = _("Ukázat ujetou vzdálenost")


def assign_vouchers(modeladmin, request, queryset):
    voucher_counter = Counter()
    for user_attendance in queryset:
        voucher_counter.update(user_attendance.assign_vouchers())
    if len(voucher_counter) == 0:
        modeladmin.message_user(request, _("Nejsou žádné vouchery k přiřazení"))
    else:
        voucher_counter_description = ", ".join(
            ["%s: %s" % (key, val) for (key, val) in voucher_counter.items()]
        )
        modeladmin.message_user(
            request,
            _(
                "Přiřazeno vouchery k {users} uživatelům: {vouchers}".format(
                    users=queryset.count(), vouchers=voucher_counter_description
                )
            ),
        )


assign_vouchers.short_description = _("Přiřadit vouchery")


def update_mailing(modeladmin, request, queryset):
    pk_list = list(queryset.values_list("pk", flat=True))
    tasks.update_mailing(
        pk_list,
    )
    modeladmin.message_user(
        request,
        _("Aktualizace mailing listu byla úspěšne zadána pro %s uživatelů")
        % queryset.count(),
    )


update_mailing.short_description = _("Aktualizovat mailing list")


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
    modeladmin.message_user(request, _("Platby potvrzeny"))


approve_am_payment.short_description = _("Potvrdit platbu")


def remove_mailing_id(modeladmin, request, queryset):
    for userprofile in queryset:
        userprofile.mailing_id = None
        userprofile.mailing_hash = None
        userprofile.save()
    modeladmin.message_user(
        request,
        _("Mailing ID a hash byl úspěšne odebrán %s profilům") % queryset.count(),
    )


remove_mailing_id.short_description = _("Odstranit mailing ID a hash")


def show_distance_trips(modeladmin, request, queryset):
    length = views.results_and_competitions.distance(queryset)
    trips = views.results_and_competitions.trips(queryset)
    modeladmin.message_user(
        request, "Ujetá vzdálenost: %s Km v %s jízdách" % (length, trips)
    )


show_distance_trips.short_description = _("Ukázat ujetou vzdálenost")


def update_mailing_coordinator(modeladmin, request, queryset):
    for company_admin in queryset:
        user_attendance = company_admin.user_attendance()
        if user_attendance:
            mailing.add_or_update_user_synchronous(user_attendance, ignore_hash=True)
        else:
            mailing.add_or_update_user_synchronous(company_admin, ignore_hash=True)

    modeladmin.message_user(
        request,
        _("Úspěšně aktualizován mailing pro %s koordinátorů") % queryset.count(),
    )


update_mailing_coordinator.short_description = _("Aktualizovat mailing list")


def mark_invoices_paid(modeladmin, request, queryset):
    for invoice in queryset.all():
        invoice.paid_date = datetime.date.today()
        invoice.save()
    modeladmin.message_user(
        request, _("%s faktur označeno jako 'zaplaceno'") % queryset.count()
    )


mark_invoices_paid.short_description = _("Označit faktury jako zaplacené")


def send_invoice_notifications(modeladmin, request, queryset):
    tasks.send_unpaid_invoice_notification.apply_async(
        kwargs={
            "pks": list(queryset.values_list("pk", flat=True)),
            "campaign_slug": request.subdomain,
        },
    )
    modeladmin.message_user(
        request, _("Odeslání %s notifikačních emailů bylo zadáno" % queryset.count())
    )


send_invoice_notifications.short_description = _(
    "Odeslat notifikaci nezaplacených faktur"
)


def create_invoices(modeladmin, request, queryset, celery=True):
    campaign = request.user_attendance.campaign
    company_pk = list(queryset.values_list("pk", flat=True))
    if celery:
        tasks.create_invoice_if_needed.delay(company_pk, campaign.slug)
    else:
        tasks.create_invoice_if_needed(company_pk, campaign.slug)


create_invoices.short_description = _("Vytvořit faktury pro neplacené platby")


def build_table_and_create_shape_files_for_cities(
    modeladmin, request, queryset, celery=True
):
    city_pks = [c.pk for c in queryset]
    if celery:
        tasks.generate_anonymized_trips_table.delay(
            cities_to_export=city_pks, rebuild_anon_table=True
        )
    else:
        tasks.generate_anonymized_trips_table(
            cities_to_export=city_pks, rebuild_anon_table=True
        )


build_table_and_create_shape_files_for_cities.short_description = _(
    "Vygenerovat tabulka anonymních jízd a vytvořit .shp soubor pro export GIS data"
)


def create_shape_files_for_cities(modeladmin, request, queryset, celery=True):
    city_pks = [c.pk for c in queryset]
    if celery:
        tasks.generate_anonymized_trips_table.delay(cities_to_export=city_pks)
    else:
        tasks.generate_anonymized_trips_table(cities_to_export=city_pks)


create_shape_files_for_cities.short_description = _(
    "Vytvořit .shp soubor pro export GIS data"
)


def send_notifications(modeladmin, request, queryset):
    tasks.send_unfilled_rides_notification.apply_async(
        kwargs={
            "pks": list(queryset.values_list("pk", flat=True)),
            "campaign_slug": request.subdomain,
        },
    )
    modeladmin.message_user(
        request, _("Odeslání %s notifikačních emailů bylo zadáno" % queryset.count())
    )


send_notifications.short_description = _("Odeslat notifikaci nevyplněných jízd")
