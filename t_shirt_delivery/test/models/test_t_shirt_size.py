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


class TestMethods(TestCase):

    def test_str(self):
        """ Test __str__() """
        t_shirt_size = mommy.make(
            "TShirtSize",
            price=0,
            name="Foo size",
        )
        self.assertEqual(str(t_shirt_size), "Foo size")

    def test_str_price(self):
        """ Test __str__() """
        t_shirt_size = mommy.make(
            "TShirtSize",
            price=10,
            name="Foo size",
        )
        self.assertEqual(str(t_shirt_size), "Foo size (10 Kč navíc)")
