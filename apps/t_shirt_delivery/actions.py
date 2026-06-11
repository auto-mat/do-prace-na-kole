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
from django.utils.translation import gettext_lazy as _

from dpnk import actions
from dpnk.models import Campaign

from t_shirt_delivery import tasks
from t_shirt_delivery.models import DeliveryBatch, TShirtSize


def create_batch(modeladmin, request, queryset):
    campaign = Campaign.objects.get(slug=request.subdomain)
    ids = [ua.pk for ua in queryset.all()]
    tasks.create_batch.delay(campaign_slug=request.subdomain, ids=ids)
    modeladmin.message_user(
        request,
        _("Požadavek na tvorbu dávku %s položek byl poslan do celery")
        % queryset.count(),
    )


create_batch.short_description = _("Vytvořit dávku z vybraných uživatelů")

delivery_box_batch_download = actions.batch_download_action_generator("customer_sheets")
delivery_box_batch_download.short_description = _("Hromadně stáhnout PDF")


def delivery_batch_generate_pdf(modeladmin, request, queryset):
    for batch in queryset.all():
        if not batch.tnt_order or batch.tnt_order.name == "":
            modeladmin.message_user(request, _("Chybí CSV soubor objednávky"))
            return
        if batch.t_shirt_count() <= 0:
            modeladmin.message_user(
                request, _("V jedné z dávek chybí trika k odeslání")
            )
            return
    ids = [batch.pk for batch in queryset.all()]
    tasks.delivery_batch_generate_pdf.delay(ids)


delivery_batch_generate_pdf.short_description = _(
    "1) Nahrát data do GLS a vytvořit PDF"
)


def delivery_batch_generate_pdf_for_opt(modeladmin, request, queryset):
    for batch in queryset.all():
        if not batch.order_pdf or batch.order_pdf.name == "":
            modeladmin.message_user(request, _("Chybí PDF z objednávky GLS"))
            return
        if not batch.tnt_order or batch.tnt_order.name == "":
            modeladmin.message_user(request, _("Chybí CSV soubor objednávky"))
            return
    ids = [batch.pk for batch in queryset.all()]
    tasks.delivery_batch_generate_pdf_for_opt.delay(ids)


delivery_batch_generate_pdf_for_opt.short_description = _(
    "2) Vytvořit kombinované PDF pro OPT"
)


def regenerate_all_box_pdfs(modeladmin, request, queryset):
    for batch in queryset.all():
        for box in batch.subsidiarybox_set.all():
            box.customer_sheets = None
            box.save()
    ids = [batch.pk for batch in queryset.all()]
    tasks.delivery_batch_generate_pdf_for_opt.delay(ids)


regenerate_all_box_pdfs.short_description = _(
    "Přegenerovat všechna PDF všech krabic u vybraných dávek"
)


def recreate_delivery_csv(modeladmin, request, queryset):
    for batch in queryset.all():
        batch.tnt_order = None
        batch.save()
    ids = [batch.pk for batch in queryset.all()]
    tasks.delivery_batch_generate_pdf_for_opt.delay(ids)


recreate_delivery_csv.short_description = _("Přegenerovat CSV u vybraných dávek")


def send_tshirt_size_not_avail_notif(modeladmin, request, queryset):
    from django.contrib.contenttypes.models import ContentType

    from dpnk.models import UserAttendance
    from dpnk.models.transactions import Status

    campaign = request.user_attendance.campaign
    exclude_tshirts_code = ["nic", ""]
    package_transaction_content_type = ContentType.objects.get(
        model="packagetransaction",
        app_label="t_shirt_delivery",
    )
    payment_content_type = ContentType.objects.get(
        model="payment",
        app_label="dpnk",
    )
    campaign_tshirts = (
        TShirtSize.objects.filter(
            campaign=campaign,
            available=True,
        )
        .exclude(t_shirt_preview=None)
        .exclude(code__in=exclude_tshirts_code)
        .values_list("name", flat=True)
    )
    users_with_tshirts = (
        UserAttendance.objects.filter(
            campaign=campaign,
            t_shirt_size__isnull=False,
        )
        .exclude(
            t_shirt_size__code__in=exclude_tshirts_code,
        )
        .values_list("t_shirt_size__name", flat=True)
    )
    if campaign_tshirts and users_with_tshirts:
        tshirts_diffs = list(
            set(users_with_tshirts) - set(campaign_tshirts),
        )
        if tshirts_diffs:
            users_without_avail_tshirt = (
                UserAttendance.objects.filter(
                    campaign=campaign,
                    t_shirt_size__name__in=tshirts_diffs,
                )
                .exclude(
                    transactions__polymorphic_ctype_id__in=[
                        package_transaction_content_type.id,
                    ],
                )
                .exclude(
                    transactions__polymorphic_ctype_id__in=[
                        payment_content_type.id,
                    ],
                    payment__status=Status.DONE,
                )
            )
            tasks.send_tshirt_size_not_avail_notif(users_without_avail_tshirt)

            modeladmin.message_user(
                request,
                _("Odeslání {} notifikačních emailů bylo zadáno.").format(
                    users_without_avail_tshirt.count(),
                ),
            )
        else:
            modeladmin.message_user(
                request,
                _(
                    "Odeslání notifikačních emailů nebylo zadáno."
                    " Žádný uživatel nemá nedostupnou velikost trika."
                ),
            )


send_tshirt_size_not_avail_notif.short_description = _(
    "Odeslat notifikační email nedostupných velikostí triček"
)
