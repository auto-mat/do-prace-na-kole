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
import os
import subprocess

from django.utils.translation import ugettext_lazy as _

from dpnk import actions
from dpnk.models import Campaign

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
    modeladmin.message_user(request, _(u"Vytvořena nová dávka obsahující %s položek") % queryset.count())


create_batch.short_description = _(u"Vytvořit dávku z vybraných uživatelů")

delivery_box_batch_download = actions.batch_download_action_generator("customer_sheets")
delivery_box_batch_download.short_description = _("Hromadně stáhnout PDF")


def delivery_batch_generate_pdf(modeladmin, request, queryset):
    for batch in queryset.all():
        batch.submit_gls_order_pdf()


delivery_batch_generate_pdf.short_description = _("Nahrát data do GLS a vytvořit PDF")


def save_filefield(filefield, directory):
    filename = directory + "/" + os.path.basename(filefield.name)
    with open(filename, "wb+") as f:
        f.write(filefield.read())
    return filename


def delivery_batch_generate_pdf_for_opt(modeladmin, request, queryset):
    for batch in queryset.all():
        subprocess.call(["rm", "tmp_pdf/output", "-r"])
        subprocess.call(["rm", "tmp_pdf/combined_sheets.pdf"])
        subprocess.call(["rm", "tmp_pdf/combined_sheets-rotated.pdf"])
        subprocess.call(["mkdir", "tmp_pdf/output", "--parents"])
        pdf_files = []
        for subsidiary_box in batch.subsidiarybox_set.all():
            filename = save_filefield(subsidiary_box.customer_sheets, "tmp_pdf/output")
            pdf_files.append(filename)

        order_pdf_filename = save_filefield(batch.order_pdf, "tmp_pdf")
        tnt_order_filename = save_filefield(batch.tnt_order, "tmp_pdf")
        subprocess.call(["scripts/batch_generation/generate_delivery_batch_pdf.sh", order_pdf_filename, tnt_order_filename])

        with open("tmp_pdf/combined_sheets-rotated.pdf", "rb+") as f:
            batch.combined_opt_pdf.save("tmp_pdf/combined_sheets-rotated.pdf", f)


delivery_batch_generate_pdf_for_opt.short_description = _("Nahrát vytvořit PDF pro OPT")
