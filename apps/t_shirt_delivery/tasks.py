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


import io
import os
import re
import subprocess

from celery import shared_task
from celery.utils.log import get_task_logger

from django.conf import settings
from django.utils import timezone

import pandas
import tablib

from dpnk.models import Campaign, UserAttendance

from .gls.mygls import MyGLS


logger = get_task_logger(__name__)


@shared_task(bind=True)
def update_dispatched_boxes(self):
    from .models import SubsidiaryBox

    my_env = os.environ.copy()
    my_env["password"] = settings.GLS_PASSWORD
    my_env["username"] = settings.GLS_USERNAME

    subprocess.call(
        "scripts/batch_generation/download_dispatched_subsidiary_boxes.sh", env=my_env
    )
    dataset = tablib.Dataset().load(open("dispatched_subsidiary_boxes.csv").read())
    for carrier_identification, box_id, dispatched in dataset:
        update_info = {}
        update_info["carrier_identification"] = carrier_identification
        if dispatched:
            update_info["dispatched"] = dispatched
        try:
            box_filter = {"id": int(box_id)}
        except ValueError:
            box_filter = {"carrier_identification": carrier_identification}
        SubsidiaryBox.objects.filter(**box_filter).update(**update_info)


@shared_task(bind=True)
def delivery_batch_generate_pdf(self, ids):
    from .models import DeliveryBatch

    batches = DeliveryBatch.objects.filter(pk__in=ids)
    for batch in batches:
        batch.submit_gls_order_pdf()


def save_filefield(filefield, directory):
    filename = directory + "/" + os.path.basename(filefield.name)
    with open(filename, "wb+") as f:
        if filefield.field.name == "tnt_order":
            csv_sep = ";"
            col = "GLS tracking ID"
            csv_content = pandas.read_csv(
                io.StringIO(filefield.read().decode()),
                sep=csv_sep,
            )
            if col in csv_content.columns:
                csv_content.drop(col, inplace=True, axis=1)
            f.write(csv_content.to_csv(sep=csv_sep, index=False).encode())
        else:
            f.write(filefield.read())
        filefield.close()
    return filename


@shared_task(bind=True)
def create_batch(self, campaign_slug, ids):
    from .models import DeliveryBatch

    delivery_batch = DeliveryBatch()
    delivery_batch.campaign = Campaign.objects.get(slug=campaign_slug)
    delivery_batch.add_packages_on_save = False
    delivery_batch.save()
    uas = UserAttendance.objects.filter(pk__in=ids)
    delivery_batch.add_packages(user_attendances=uas)
    delivery_batch.add_packages_on_save = True
    delivery_batch.save()


@shared_task(bind=True)
def delivery_batch_generate_pdf_for_opt(self, ids):
    from .models import DeliveryBatch

    batches = DeliveryBatch.objects.filter(pk__in=ids)
    for batch in batches:
        subprocess.call(["rm", "tmp_pdf/", "-r"])
        subprocess.call(["mkdir", "tmp_pdf/output", "--parents"])
        pdf_files = []
        for subsidiary_box in batch.subsidiarybox_set.all():
            filename = save_filefield(subsidiary_box.customer_sheets, "tmp_pdf/output")
            pdf_files.append(filename)

        order_pdf_filename = save_filefield(batch.order_pdf, "tmp_pdf")
        subprocess.call(
            [
                "scripts/batch_generation/generate_delivery_batch_pdf.sh",
                order_pdf_filename,
            ]
        )

        with open("tmp_pdf/combined_sheets-rotated.pdf", "rb+") as f:
            filename = "tmp_pdf/combined_sheets_rotated_%s_%s.pdf" % (
                batch.pk,
                timezone.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            )
            batch.combined_opt_pdf.save(os.path.basename(filename), f)
            batch.save()
        subprocess.call(["rm", "tmp_pdf/", "-r"])


@shared_task(bind=True)
def send_tshirt_size_not_avail_notif(self, user_attendances):
    from dpnk.email import tshirt_size_not_avail

    for user_attendance in user_attendances:
        tshirt_size_not_avail(user_attendance)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={
        "max_retries": 3,
        "countdown": 60 * 5,
    },
)
def update_subsidiary_box(self, print_from=None, print_to=None, campaign_slug="dpnk"):
    """Update subsidiaty box by MyGLS parcel status which was
    printed (by printed date time range)

    :param datetime print_from: Date time timestamp printed labels from,
                                with default None value (value is assigned
                                from the actual campaign date from competition
                                phase)
    :param datetime print_to: Date time timestamp printed labels to,
                              with default None value (value is assigned
                              from the actual campaign date to competition
                              phase)
    :param str campaign_slug: Actual campaing slug, with default "dpnk" value

    :return None
    """
    from .models import SubsidiaryBox

    campaign = Campaign.objects.filter(slug=campaign_slug)
    if campaign:
        campaign = campaign[0]
        competition_phase = campaign.phase(phase_type="competition")

    if not print_from:
        if campaign:
            print_from = timezone.datetime.combine(
                competition_phase.date_from,
                timezone.datetime.min.time(),
            )
        else:
            print_from = timezone.datetime.now()
    else:
        print_from = timezone.datetime.fromtimestamp(print_from)
    if not print_to:
        if campaign:
            print_to = timezone.datetime.combine(
                competition_phase.date_to,
                timezone.datetime.min.time(),
            )
        else:
            print_to = timezone.datetime.now()
    else:
        print_to = timezone.datetime.fromtimestamp(print_to)

    logger.debug(f"Get parcels printed from <{print_from}>.")
    logger.debug(f"Get parcels printed to <{print_to}>.")
    mygls = MyGLS()
    parcels = mygls.get_parcels(
        print_from=print_from,
        print_to=print_to,
    )
    logger.debug(f"Number of parcels <{len(parcels.PrintDataInfoList)}>.")
    # Update subsidiary boxes carrier_identification field value
    sub_box_ids = []
    last_parcel_status_idx = -1
    for parcel in parcels.PrintDataInfoList:
        parcel_status = mygls.parcel_status(parcel_number=parcel.ParcelNumber)
        if parcel_status.GetParcelStatusErrors:
            raise Exception("Getting parcel number <{parcel.ParcelNumber}> fail.")
        status_datetime = parcel_status.ParcelStatusList[
            last_parcel_status_idx
        ].StatusDate
        timestamp = re.search(r"([0-9]*)[\+|)]", status_datetime)
        if timestamp:
            status_datetime = timezone.datetime.fromtimestamp(
                int(timestamp.group(1)) // 1000,
            )

        sub_box_ids.append(
            {
                "id": int(parcel.Parcel.ClientReference),
                "carrier_identification": str(int(parcel.ParcelNumber)),
                "status_code": int(
                    parcel_status.ParcelStatusList[last_parcel_status_idx].StatusCode
                ),
                "status_description": parcel_status.ParcelStatusList[
                    last_parcel_status_idx
                ].StatusDescription,
                "status_datetime": status_datetime,
            }
        )

    sub_boxes = SubsidiaryBox.objects.filter(
        id__in=[sub_box["id"] for sub_box in sub_box_ids]
    )
    update_sub_boxes = []
    for sub_box in sub_boxes:
        for box in sub_box_ids:
            if box["id"] == sub_box.id:
                break
        sub_box.carrier_identification = box["carrier_identification"]
        sub_box.status_code = box["status_code"]
        sub_box.status_description = box["status_description"]
        sub_box.status_datetime = box["status_datetime"]

        update_sub_boxes.append(sub_box)

    logger.debug(f"Number of updated subsidiary boxes <{len(update_sub_boxes)}>.")
    SubsidiaryBox.objects.bulk_update(
        update_sub_boxes,
        fields=[
            "carrier_identification",
            "status_code",
            "status_description",
            "status_datetime",
        ],
    )
    logger.info("Updated subsidiary boxes was successful.")
