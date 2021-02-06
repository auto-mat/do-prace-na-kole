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
from django.utils.translation import ugettext_lazy as _

from dpnk import actions
from dpnk.models import Campaign

from t_shirt_delivery import tasks
from t_shirt_delivery.models import DeliveryBatch


def create_batch(modeladmin, request, queryset):
    campaign = Campaign.objects.get(slug=request.subdomain)
    delivery_batch = DeliveryBatch()
    delivery_batch.campaign = campaign
    delivery_batch.add_packages_on_save = False
    delivery_batch.save()
    delivery_batch.add_packages(user_attendances=queryset)
    delivery_batch.add_packages_on_save = True
    delivery_batch.save()
    modeladmin.message_user(
        request, _(u"Vytvořena nová dávka obsahující %s položek") % queryset.count()
    )


create_batch.short_description = _(u"Vytvořit dávku z vybraných uživatelů")

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
