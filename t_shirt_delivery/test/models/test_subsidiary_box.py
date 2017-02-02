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


class TestSubsidiaryBox(TestCase):
    def test_str(self):
        """
        Test that __str__ returns SubsidiaryBox string
        """
        subsidiary_box = mommy.make(
            'SubsidiaryBox',
            subsidiary__address_street="Foo street",
            subsidiary__address_street_number="7",
            subsidiary__address_recipient="Foo recipient",
            subsidiary__address_city="Foo city",
            subsidiary__address_psc="12345",
            subsidiary__company__name="Foo company",
            subsidiary__city__name="Foo city",
        )
        self.assertEqual(
            str(subsidiary_box),
            "Krabice pro pobočku Foo recipient, Foo street 7, 123 45 Foo city - Foo city",
        )
