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
import datetime

from django.test import TestCase

from dpnk import models, results
from dpnk.test.util import print_response  # noqa


class RidesBaseTests(TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users']

    def test_get_minimum_rides_base_proportional(self):
        competition = models.Competition.objects.get(slug="FQ-LB")
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 1)), 1)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 7)), 10)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 15)), 23)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 30)), 23)

    def test_get_minimum_rides_base_proportional_phase(self):
        competition = models.Phase.objects.get(pk=2)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 1)), 0)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 7)), 5)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 15)), 12)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 30)), 25)
