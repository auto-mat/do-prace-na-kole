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


class TestTeamPackage(TestCase):
    def test_str(self):
        """
        Test that __str__ returns TeamPackage string
        """
        team_package = mommy.make(
            'TeamPackage',
            team__name="Foo team",
            team__campaign__slug="foo_slug",
        )
        self.assertEqual(
            str(team_package),
            "Balíček pro tým Foo team",
        )

    def test_str_noteam(self):
        """
        Test that __str__ returns TeamPackage string
        when team is None
        """
        team_package = mommy.make(
            'TeamPackage',
            team=None,
        )
        self.assertEqual(
            str(team_package),
            "Balíček bez týmu",
        )
