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
from itertools import cycle

from django.test import TestCase
from django.test.utils import override_settings

from dpnk import models, results, util
from dpnk.test.util import ClearCacheMixin, DenormMixin
from dpnk.test.util import print_response  # noqa

from model_mommy import mommy

from .mommy_recipes import UserAttendanceRecipe, testing_campaign


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
            'payment_status__in': ('done', 'no_admission'),
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


@override_settings(
    FAKE_DATE=datetime.date(year=2017, month=5, day=5),
)
class ResultsTests(DenormMixin, ClearCacheMixin, TestCase):
    def setUp(self):
        super().setUp()
        team = mommy.make('Team', campaign=testing_campaign)
        UserAttendanceRecipe.make(
            approved_for_team='approved',
            team=team,
        )
        self.user_attendance = UserAttendanceRecipe.make(
            approved_for_team='approved',
            team=team,
        )
        mommy.make(
            'Trip',
            commute_mode_id=1,
            distance='1',
            direction='trip_to',
            user_attendance=self.user_attendance,
            date='2017-05-01',
        )
        mommy.make(
            'Trip',
            commute_mode_id=1,
            distance='3',
            direction='trip_from',
            date='2017-05-01',
            user_attendance=self.user_attendance,
        )
        mommy.make(
            'Trip',
            commute_mode_id=4,
            direction=cycle(['trip_to', 'trip_from']),
            date='2017-05-02',
            user_attendance=self.user_attendance,
            _quantity=2,
        )
        mommy.make(
            'Trip',
            commute_mode_id=2,
            distance='1',
            direction='trip_from',
            date='2017-05-03',
            user_attendance=self.user_attendance,
        )
        self.user_attendance.campaign.phase_set.filter(
            phase_type='competition',
        ).update(
            date_from=datetime.date(2017, 4, 2),
            date_to=datetime.date(2017, 5, 20),
        )
        self.user_attendance.campaign.phase('competition').refresh_from_db()
        self.user_attendance.team.campaign.phase('competition').refresh_from_db()

    def test_get_userprofile_length(self):
        competition = mommy.make(
            'Competition',
            competition_type='length',
            competitor_type='single_user',
            campaign=testing_campaign,
            date_from=datetime.date(2017, 4, 3),
            date_to=datetime.date(2017, 5, 23),
            commute_modes=models.CommuteMode.objects.filter(slug__in=('bicycle', 'by_foot')),
        )
        result = results.get_userprofile_length([self.user_attendance], competition)
        self.assertEquals(result, 5.0)

        util.rebuild_denorm_models([self.user_attendance])
        self.user_attendance.refresh_from_db()

        result = self.user_attendance.trip_length_total
        self.assertEquals(result, 5.0)

    def test_get_userprofile_frequency(self):
        competition = mommy.make(
            'Competition',
            competition_type='frequency',
            competitor_type='team',
            campaign=testing_campaign,
            date_from=datetime.date(2017, 4, 3),
            date_to=datetime.date(2017, 5, 23),
            commute_modes=models.CommuteMode.objects.filter(slug__in=('bicycle', 'by_foot')),
        )

        util.rebuild_denorm_models([self.user_attendance])
        self.user_attendance.refresh_from_db()
        self.user_attendance.team.refresh_from_db()

        result = self.user_attendance.get_rides_count_denorm
        self.assertEquals(result, 3)

        result = self.user_attendance.get_working_rides_base_count()
        self.assertEquals(result, 48)

        result = self.user_attendance.frequency
        self.assertEquals(result, 0.0625)

        result = self.user_attendance.team.frequency
        self.assertEquals(result, 0.03125)

        result = self.user_attendance.team.get_rides_count_denorm
        self.assertEquals(result, 3)

        result = self.user_attendance.team.get_working_trips_count()
        self.assertEquals(result, 96)

        result = results.get_working_trips_count(self.user_attendance, competition)
        self.assertEquals(result, 48)

        result = results.get_userprofile_frequency(self.user_attendance, competition)
        self.assertEquals(result, (3, 48, 3 / 48.0))

        result = results.get_team_frequency(self.user_attendance.team.members(), competition)
        self.assertEquals(result, (3, 96, 3 / 96.0))

    def test_get_userprofile_length_by_foot(self):
        competition = mommy.make(
            'Competition',
            competition_type='length',
            competitor_type='single_user',
            campaign=testing_campaign,
            date_from=datetime.date(2017, 4, 1),
            date_to=datetime.date(2017, 5, 31),
            commute_modes=models.CommuteMode.objects.filter(slug__in=('by_foot',)),
        )
        result = results.get_userprofile_length([self.user_attendance], competition)
        self.assertEquals(result, 1.0)
