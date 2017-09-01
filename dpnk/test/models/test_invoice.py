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

from django.core import mail
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings

from model_mommy import mommy

from ..mommy_recipes import PhaseRecipe, testing_campaign


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


class TestClean(TestCase):
    def test_clean_exception(self):
        invoice = mommy.prepare("Invoice", campaign=testing_campaign)
        with self.assertRaisesRegexp(Exception, "Neexistuje žádná nefakturovaná platba"):
            invoice.clean()


class TestSave(TransactionTestCase):
    # This is here, because creating Payment messes up with indexes and other subsequent tests will fail.
    reset_sequences = True

    def test_change_invoice_payments_status(self):
        invoice = mommy.make("Invoice", campaign=testing_campaign)
        payment = mommy.make(
            "Payment",
            user_attendance__campaign=testing_campaign,
            user_attendance__team__campaign=testing_campaign,
            invoice=invoice,
            user_attendance__team__name="Foo team",
            user_attendance__userprofile__user__email="test@email.cz",
        )
        mail.outbox = []
        PhaseRecipe.make()
        self.assertEquals(invoice.payment_set.get().status, 0)
        invoice.paid_date = datetime.date(year=2010, month=11, day=20)
        invoice.save()
        self.assertEquals(invoice.payment_set.get().status, 1007)
        invoice.delete()
        payment.refresh_from_db()
        self.assertEquals(payment.status, 1005)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test@email.cz'])
        self.assertEqual(str(msg.subject), 'Testing campaign - přijetí platby')

    def test_invoice_raises_sequence_number_overrun(self):
        campaign = mommy.make(
            "Campaign",
            invoice_sequence_number_first=1,
            invoice_sequence_number_last=2,
            slug="camp",
        )
        mommy.make(
            "Phase",
            phase_type="competition",
            campaign=campaign,
            date_from="2016-1-1",
            date_to="2016-1-1",
        )
        company = mommy.make("Company")
        invoice = mommy.make(
            "Invoice",
            campaign=campaign,
            company=company,
            sequence_number=None,
            _quantity=2,
        )
        self.assertEqual(invoice[0].sequence_number, 1)
        self.assertEqual(invoice[1].sequence_number, 2)
        with self.assertRaisesRegexp(Exception, "Došla číselná řada faktury"):
            mommy.make(
                "Invoice",
                campaign=campaign,
                company=company,
                sequence_number=None,
            )
