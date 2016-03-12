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
from dpnk.models import DeliveryBatch, PackageTransaction
from PyPDF2 import PdfFileReader
import datetime


class TestParcelBatch(TestCase):
    fixtures = ['campaign', 'users', 'transactions', 'batches']

    def tearDown(self):
        PackageTransaction.objects.all().delete()

    def get_key_string(self):
        return "1-%s-" % datetime.date.today().strftime("%y%m%d")

    def test_parcel_batch(self):
        delivery_batch = DeliveryBatch.objects.get(pk=1)
        pdf = PdfFileReader(delivery_batch.customer_sheets)
        pdf_string = pdf.pages[0].extractText()
        self.assertTrue("Testing campaign" in pdf_string)
        self.assertTrue(self.get_key_string() in pdf_string)
        self.assertTrue("Testing t-shirt size" in pdf_string)
        self.assertTrue("1111111" in pdf_string)
        self.assertTrue("Testing company," in pdf_string)
        self.assertTrue("Testing User 1" in pdf_string)
        self.assertTrue("U•ivatelsk† jm†no: test" in pdf_string)

    def test_avfull(self):
        delivery_batch = DeliveryBatch.objects.get(pk=1)
        avfull_string = delivery_batch.tnt_order.read()
        self.assertTrue(b"testing-campaign1" in avfull_string)
        self.assertTrue(bytes(self.get_key_string(), "utf-8") in avfull_string)
        self.assertTrue(b"OP Automat" in avfull_string)
        self.assertTrue(b"1111111" in avfull_string)
        self.assertTrue(b"Testing company," in avfull_string)
        self.assertTrue(b"Testing User 1" in avfull_string)
