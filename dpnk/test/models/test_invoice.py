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

from django.test import TestCase
from django.test.utils import override_settings

from model_mommy import mommy


class TestDates(TestCase):
    def setUp(self):
        self.competition_phase = mommy.make(
            "Phase",
            phase_type="competition",
            date_to="2010-05-31",
        )

    @override_settings(
        FAKE_DATE=datetime.date(2010, 5, 20),
    )
    def test_dates_before_end(self):
        """
        Test that dates are set correctly before end competition date
        """
        invoice = mommy.make(
            "Invoice",
            campaign__slug="test_campaign",
            campaign__phase_set=[self.competition_phase],
            sequence_number=666,
        )
        self.assertEqual(str(invoice.taxable_date), "2010-05-20")
        self.assertEqual(str(invoice.payback_date), "2010-06-03")
        self.assertEqual(str(invoice.exposure_date), "2010-05-20")
        self.assertEqual(str(invoice.variable_symbol), "2010666")

    @override_settings(
        FAKE_DATE=datetime.date(2010, 6, 1),
    )
    def test_dates_after_end(self):
        """
        Test that dates are set correctly after end competition date
        """
        invoice = mommy.make(
            "Invoice",
            campaign__slug="test_campaign",
            campaign__phase_set=[self.competition_phase],
        )
        self.assertEqual(str(invoice.taxable_date), "2010-05-31")
        self.assertEqual(str(invoice.payback_date), "2010-06-15")
        self.assertEqual(str(invoice.exposure_date), "2010-06-01")

    @override_settings(
        FAKE_DATE=datetime.date(2010, 6, 20),
    )
    def test_dates_long_after_end(self):
        """
        Test that dates are set correctly more than 14 days after end competition date
        """
        invoice = mommy.make(
            "Invoice",
            campaign__slug="test_campaign",
            campaign__phase_set=[self.competition_phase],
        )
        self.assertEqual(str(invoice.taxable_date), "2010-05-31")
        self.assertEqual(str(invoice.payback_date), "2010-07-04")
        self.assertEqual(str(invoice.exposure_date), "2010-06-14")

    @override_settings(
        FAKE_DATE=datetime.date(2010, 6, 20),
    )
    def test_dates_doesnt_change(self):
        """
        Test that dates doesnt change when they are already set
        """
        invoice = mommy.make(
            "Invoice",
            campaign__slug="test_campaign",
            campaign__phase_set=[self.competition_phase],
            taxable_date=datetime.date(2010, 1, 1),
            payback_date=datetime.date(2010, 1, 1),
            exposure_date=datetime.date(2010, 1, 1),
        )
        self.assertEqual(str(invoice.taxable_date), "2010-01-01")
        self.assertEqual(str(invoice.payback_date), "2010-01-01")
        self.assertEqual(str(invoice.exposure_date), "2010-01-01")
