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

from celery import shared_task

from django.conf import settings

import tablib

from .models import DeliveryBatch, SubsidiaryBox


@shared_task(bind=True)
def update_dispatched_boxes(self):
    my_env = os.environ.copy()
    my_env["password"] = settings.GLS_PASSWORD
    my_env["username"] = settings.GLS_USERNAME

    subprocess.call("scripts/batch_generation/download_dispatched_subsidiary_boxes.sh", env=my_env)
    dataset = tablib.Dataset().load(open("dispatched_subsidiary_boxes.csv").read())
    for carrier_identification, box_id, dispatched in dataset:
        update_info = {}
        update_info['carrier_identification'] = carrier_identification
        if dispatched:
            update_info['dispatched'] = dispatched
        try:
            box_filter = {'id': int(box_id)}
        except ValueError:
            box_filter = {'carrier_identification': carrier_identification}
        SubsidiaryBox.objects.filter(**box_filter).update(**update_info)


@shared_task(bind=True)
def delivery_batch_generate_pdf(self, ids):
    batches = DeliveryBatch.objects.filter(pk__in=ids)
    for batch in batches:
        batch.submit_gls_order_pdf()


def save_filefield(filefield, directory):
    filename = directory + "/" + os.path.basename(filefield.name)
    with open(filename, "wb+") as f:
        f.write(filefield.read())
    return filename


@shared_task(bind=True)
def delivery_batch_generate_pdf_for_opt(self, ids):
    batches = DeliveryBatch.objects.filter(pk__in=ids)
    for batch in batches:
        subprocess.call(["rm", "tmp_pdf/", "-r"])
        subprocess.call(["mkdir", "tmp_pdf/output", "--parents"])
        pdf_files = []
        for subsidiary_box in batch.subsidiarybox_set.all():
            filename = save_filefield(subsidiary_box.customer_sheets, "tmp_pdf/output")
            pdf_files.append(filename)

        order_pdf_filename = save_filefield(batch.order_pdf, "tmp_pdf")
        tnt_order_filename = save_filefield(batch.tnt_order, "tmp_pdf")
        subprocess.call(["scripts/batch_generation/generate_delivery_batch_pdf.sh", order_pdf_filename, tnt_order_filename])

        with open("tmp_pdf/combined_sheets-rotated.pdf", "rb+") as f:
            batch.combined_opt_pdf.save("tmp_pdf/combined_sheets_rotated_%s.pdf" % batch.pk, f)
        subprocess.call(["rm", "tmp_pdf/", "-r"])
