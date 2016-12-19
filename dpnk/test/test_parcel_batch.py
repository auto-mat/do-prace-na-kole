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

from PyPDF2 import PdfFileReader

from django.test import TestCase

from dpnk.models import DeliveryBatch, PackageTransaction


class TestParcelBatch(TestCase):
    fixtures = ['campaign', 'auth_user', 'users', 'transactions', 'batches']

    def tearDown(self):
        PackageTransaction.objects.all().delete()

    def test_parcel_batch(self):
        delivery_batch = DeliveryBatch.objects.get(pk=1)
        pdf = PdfFileReader(delivery_batch.customer_sheets)
        pdf_string = pdf.pages[0].extractText()
        self.assertTrue("Testing campaign" in pdf_string)
        self.assertTrue("1-151112-" in pdf_string)
        self.assertTrue("Testing t-shirt size" in pdf_string)
        self.assertTrue("1111111" in pdf_string)
        self.assertTrue("Testing company," in pdf_string)
        self.assertTrue("Testing User 1" in pdf_string)
        self.assertTrue("U•ivatelsk† jm†no: test" in pdf_string)

    def test_avfull(self):
        delivery_batch = DeliveryBatch.objects.get(pk=1)
        avfull_string = delivery_batch.tnt_order.read().decode("utf-8")
        self.assertTrue("testing-campaign1" in avfull_string)
        self.assertTrue("1-151112-" in avfull_string)
        lines = avfull_string.split("\r\n")
        self.assertEquals(lines[0][54:84], "OP Automat                    ")
        self.assertEquals(lines[0][31:38], "1111111")
        self.assertEquals(lines[0][321:351], "Testing company,              ")
        self.assertEquals(lines[0][503:525], "Testing User 1        ")
        self.assertEquals(lines[0][381:411], "Testing User 1                ")
