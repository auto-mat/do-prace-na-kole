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
from django.test.utils import override_settings

from dpnk import models, results, util
from dpnk.test.util import print_response  # noqa
from dpnk.test.util import ClearCacheMixin, DenormMixin

from model_mommy import mommy


class RidesBaseTests(TestCase):
    def test_get_minimum_rides_base_proportional(self):
        competition = mommy.make(
            "dpnk.Competition",
            competition_type="frequency",
            competitor_type="team",
            date_from=datetime.date(year=2010, month=11, day=1),
            date_to=datetime.date(year=2010, month=11, day=15),
            minimum_rides_base=23,
        )

        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 1)), 1)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 7)), 10)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 15)), 23)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 30)), 23)

    def test_get_minimum_rides_base_proportional_phase(self):
        competition = mommy.make(
            "dpnk.Phase",
            phase_type="competition",
            date_from=datetime.date(year=2010, month=11, day=1),
            date_to=datetime.date(year=2010, month=11, day=30),
        )
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 1)), 0)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 7)), 5)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 15)), 12)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 30)), 25)


class ResultsTests(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'test_results_data', 'trips']

    def setUp(self):
        super().setUp()
        util.rebuild_denorm_models(models.Team.objects.filter(pk=1))
        util.rebuild_denorm_models(models.UserAttendance.objects.filter(pk=1115))

    def test_get_competitors(self):
        team = models.Team.objects.get(id=1)
        query = results.get_competitors(models.Competition.objects.get(id=0))
        self.assertListEqual(list(query.all()), [team])

    def test_get_userprofile_length(self):
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        competition = models.Competition.objects.get(id=5)
        result = results.get_userprofile_length([user_attendance], competition)
        self.assertEquals(result, 5.0)

        result = user_attendance.trip_length_total
        self.assertEquals(result, 5.0)

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=11, day=20),
    )
    def test_get_userprofile_frequency(self):
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        competition = models.Competition.objects.get(id=3)

        result = user_attendance.get_rides_count_denorm
        self.assertEquals(result, 1)

        result = user_attendance.get_working_rides_base_count()
        self.assertEquals(result, 31)

        result = user_attendance.frequency
        self.assertEquals(result, 0.0222222222222222)

        result = user_attendance.team.frequency
        self.assertEquals(result, 0.0075187969924812)

        result = user_attendance.team.get_rides_count_denorm
        self.assertEquals(result, 1)

        result = user_attendance.team.get_working_trips_count()
        self.assertEquals(result, 91)

        result = results.get_working_trips_count(user_attendance, competition)
        self.assertEquals(result, 23)

        result = results.get_userprofile_frequency(user_attendance, competition)
        self.assertEquals(result, (1, 23, 1 / 23.0))

        result = results.get_team_frequency(user_attendance.team.members(), competition)
        self.assertEquals(result, (1, 69, 1 / 69.0))
