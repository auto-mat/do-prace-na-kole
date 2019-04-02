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

from .models import SubsidiaryBox


@shared_task(bind=True)
def update_dispatched_boxes(self):
    my_env = os.environ.copy()
    my_env["password"] = settings.GLS_PASSWORD
    my_env["username"] = settings.GLS_USERNAME

    subprocess.call("scripts/download_dispatched_subsidiary_boxes.sh", env=my_env)
    dataset = tablib.Dataset().load(open("dispatched_subsidiary_boxes.csv").read())
    for carrier_identification, box_id, dispatched in dataset:
        update_info = {}
        update_info['carrier_identification'] = carrier_identification
        if dispatched:
            update_info['dispatched'] = dispatched
        SubsidiaryBox.objects.filter(id=box_id).update(**update_info)
