# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2016 o.s. Auto*Mat
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

from django.test import TestCase
from dpnk.models import DeliveryBatch, Campaign
from .parcel_batch import make_customer_sheets_pdf
from django.core.files.temp import NamedTemporaryFile

class TestParcelBatch(TestCase):
    fixtures = ['campaign', 'users', 'batches']

    def test_parcel_batch(self):
        delivery_batch = DeliveryBatch.objects.get(pk=1)
        print(delivery_batch.packagetransaction_set())
        temp = NamedTemporaryFile()
        make_customer_sheets_pdf(temp, delivery_batch)
        print(str(temp.read()))
