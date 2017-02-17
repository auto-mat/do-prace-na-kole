# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
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
import datetime
import os

from django.test import TestCase, override_settings

from model_mommy import mommy


class TestDeliveryBatch(TestCase):
    def test_str(self):
        """
        Test that __str__ returns DeliveryBatch string
        """
        delivery_batch = mommy.make(
            'DeliveryBatch',
            id=11,
            created=datetime.datetime(year=2016, month=1, day=1, hour=1, minute=1, second=1),
        )
        self.assertEqual(
            str(delivery_batch),
            "id 11 vytvořená 2016-01-01 01:01:01",
        )

    @override_settings(MEDIA_ROOT='/tmp/django_test')
    def test_batch_csv_sheets(self):
        """
        Test that batch CSV is created
        """
        os.system("rm -f /tmp/django_test/csv_delivery/delivery_batch_123_2010-11-20.csv")
        delivery_batch = mommy.make(
            'DeliveryBatch',
            created=datetime.date(year=2010, month=11, day=20),
            id=123,
        )
        self.assertEqual(
            delivery_batch.tnt_order.name,
            "csv_delivery/delivery_batch_123_2010-11-20.csv",
        )
