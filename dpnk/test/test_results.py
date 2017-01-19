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


class GetCompetitorsWithoutAdmissionTests(TestCase):
    def setUp(self):
        self.campaign = mommy.make(
            'dpnk.Campaign',
            name="Foo campaign",
        )

    def test_single_user_frequency(self):
        """ Test if _filter_query_single_user function returns correct filter_query dict. """
        competition = mommy.make(
            "dpnk.Competition",
            competition_type="frequency",
            competitor_type="single_user",
            campaign=self.campaign,
            sex='male',
            company__name="Foo company",
        )
        filter_query = results._filter_query_single_user(competition)
        expected_dict = {
            'approved_for_team': 'approved',
            'campaign': self.campaign,
            'userprofile__user__is_active': True,
            'team__subsidiary__company': competition.company,
            'userprofile__sex': 'male',
        }
        self.assertDictEqual(filter_query, expected_dict)

    def test_single_user_frequency_city(self):
        """ Test if _filter_query_single_user function returns correct filter_query dict with city filter. """
        city = mommy.make('dpnk.City', name="City 1")
        competition = mommy.make(
            "dpnk.Competition",
            competition_type="frequency",
            competitor_type="single_user",
            campaign=self.campaign,
            city=[city],
        )
        filter_query = results._filter_query_single_user(competition)
        self.assertQuerysetEqual(
            filter_query['team__subsidiary__city__in'],
            ['<City: City 1>'],
        )

    def test_team_frequency(self):
        """ Test if _filter_query_team function returns correct filter_query dict. """
        competition = mommy.make(
            "dpnk.Competition",
            competition_type="frequency",
            competitor_type="team",
            campaign=self.campaign,
            company__name="Foo company",
        )
        filter_query = results._filter_query_team(competition)
        expected_dict = {
            'campaign': self.campaign,
            'subsidiary__company': competition.company,
        }
        self.assertDictEqual(filter_query, expected_dict)

    def test_team_frequency_city(self):
        """ Test if _filter_query_team function returns correct filter_query dict with city filter. """
        city = mommy.make('dpnk.City', name="City 1")
        competition = mommy.make(
            "dpnk.Competition",
            competition_type="frequency",
            competitor_type="team",
            campaign=self.campaign,
            city=[city],
        )
        filter_query = results._filter_query_team(competition)
        self.assertQuerysetEqual(
            filter_query['subsidiary__city__in'],
            ['<City: City 1>'],
        )

    def test_company_frequency(self):
        """ Test if _filter_query_company function returns correct filter_query dict. """
        competition = mommy.make(
            "dpnk.Competition",
            competition_type="frequency",
            competitor_type="company",
            campaign=self.campaign,
            company__name="Foo company",
        )
        filter_query = results._filter_query_company(competition)
        expected_dict = {
            'pk': competition.company.pk,
        }
        self.assertDictEqual(filter_query, expected_dict)

    def test_company_frequency_city(self):
        """ Test if _filter_query_company function returns correct filter_query dict with city filter. """
        city = mommy.make('dpnk.City', name="City 1")
        competition = mommy.make(
            "dpnk.Competition",
            competition_type="frequency",
            competitor_type="company",
            campaign=self.campaign,
            city=[city],
        )
        filter_query = results._filter_query_company(competition)
        self.assertQuerysetEqual(
            filter_query['subsidiaries__city__in'],
            ['<City: City 1>'],
        )


class GetCompetitorsTests(TestCase):
    def setUp(self):
        self.campaign = mommy.make(
            'dpnk.Campaign',
            name="Foo campaign",
        )
        mommy.make(
            "dpnk.Phase",
            phase_type="competition",
            date_from=datetime.date(year=2010, month=11, day=1),
            date_to=datetime.date(year=2010, month=11, day=30),
            campaign=self.campaign,
        )

    def test_get_competitors(self):
        team = mommy.make(
            "dpnk.Team",
            name="Foo team",
            campaign=self.campaign,
        )
        for name in ["Foo user", "Bar user"]:
            mommy.make(
                "dpnk.UserAttendance",
                userprofile__nickname=name,
                team=team,
                campaign=self.campaign,
                approved_for_team='approved',
            )
        team.save()
        competition = mommy.make(
            "dpnk.Competition",
            competitor_type="team",
            without_admission=True,
            campaign=self.campaign,
        )
        query = results.get_competitors(competition)
        self.assertQuerysetEqual(query.all(), ['<Team: Foo team (Foo user, Bar user)>'])

    def test_get_competitors_with_admission_single(self):
        user_attendance = mommy.make(
            "dpnk.UserAttendance",
            userprofile__nickname="Foo user",
            campaign=self.campaign,
        )
        competition = mommy.make(
            "dpnk.Competition",
            competitor_type="single_user",
            without_admission=False,
            campaign=self.campaign,
            user_attendance_competitors=[user_attendance],
        )
        query = results.get_competitors(competition)
        self.assertQuerysetEqual(query.all(), ['<UserAttendance: Foo user>'])

    def test_get_competitors_with_admission_team(self):
        team = mommy.make(
            "dpnk.Team",
            name="Foo team",
            campaign=self.campaign,
        )
        for name in ["Foo user", "Bar user"]:
            mommy.make(
                "dpnk.UserAttendance",
                userprofile__nickname=name,
                team=team,
                campaign=self.campaign,
                approved_for_team='approved',
            )
        team.save()
        competition = mommy.make(
            "dpnk.Competition",
            competitor_type="team",
            without_admission=False,
            campaign=self.campaign,
            team_competitors=[team],
        )
        query = results.get_competitors(competition)
        self.assertQuerysetEqual(query.all(), ['<Team: Foo team (Foo user, Bar user)>'])

    def test_get_competitors_with_admission_company(self):
        company = mommy.make(
            "dpnk.Company",
            name="Foo company",
        )
        competition = mommy.make(
            "dpnk.Competition",
            competitor_type="company",
            without_admission=False,
            campaign=self.campaign,
            company_competitors=[company],
        )
        query = results.get_competitors(competition)
        self.assertQuerysetEqual(query.all(), ['<Company: Foo company>'])

    def test_get_competitors_liberos(self):
        team = mommy.make(
            "dpnk.Team",
            name="Foo team",
            campaign=self.campaign,
        )
        mommy.make(
            "dpnk.UserAttendance",
            userprofile__nickname="Foo user",
            team=team,
            campaign=self.campaign,
            approved_for_team='approved',
        )
        team.save()
        competition = mommy.make(
            "dpnk.Competition",
            competitor_type="liberos",
            without_admission=True,
            campaign=self.campaign,
        )
        query = results.get_competitors(competition)
        self.assertQuerysetEqual(query.all(), ['<UserAttendance: Foo user>'])


class ResultsTests(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'test_results_data', 'trips']

    def setUp(self):
        super().setUp()
        util.rebuild_denorm_models(models.Team.objects.filter(pk=1))
        util.rebuild_denorm_models(models.UserAttendance.objects.filter(pk=1115))

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
