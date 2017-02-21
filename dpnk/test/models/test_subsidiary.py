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
from django.test import TestCase

from model_mommy import mommy


class TestSubsidiaryMethods(TestCase):
    def test_str(self):
        """
        Test that __str__ works properly
        """
        subsidiary = mommy.make(
            "Subsidiary",
            address_recipient=None,
            address_street="Foo street",
            city__name="Foo city",
        )
        self.assertEqual(
            str(subsidiary),
            "Foo street - Foo city",
        )

    def test_str_full(self):
        """
        Test that __str__ works properly
        """
        subsidiary = mommy.make(
            "Subsidiary",
            address_recipient="Foo recipient",
            address_street="Foo street",
            address_street_number="12",
            address_psc="12345",
            address_city="Bar city",
            city__name="Foo city",
        )
        self.assertEqual(
            str(subsidiary),
            "Foo recipient, Foo street 12, 123 45 Bar city - Foo city",
        )

    def test_name(self):
        """
        Test that name works properly
        """
        subsidiary = mommy.make(
            "Subsidiary",
            address_street="Foo street",
        )
        self.assertEqual(
            subsidiary.name(),
            "Foo street",
        )

    def test_get_recipient_string_equals(self):
        """
        Test that get_recipient_string function works properly when it equals with company name
        """
        subsidiary = mommy.make(
            "Subsidiary",
            address_recipient=" foo RECIpient",
            company__name="FOo recipient ",
        )
        self.assertEqual(
            subsidiary.get_recipient_string(),
            " foo RECIpient",
        )

    def test_get_recipient_string_not_equals(self):
        """
        Test that get_recipient_string function works properly when it does not equal with company name
        """
        subsidiary = mommy.make(
            "Subsidiary",
            address_recipient="Foo recipient",
            company__name="Foo company",
        )
        self.assertEqual(
            subsidiary.get_recipient_string(),
            "Foo recipient; Foo company",
        )

    def test_get_recipient_string_recipient_blank(self):
        """
        Test that get_recipient_string function works properly when address_recipient is blank
        """
        subsidiary = mommy.make(
            "Subsidiary",
            address_recipient="",
            company__name="Foo company",
        )
        self.assertEqual(
            subsidiary.get_recipient_string(),
            "Foo company",
        )
