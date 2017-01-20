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

from model_mommy import mommy


class TestCompetitionResult(TestCase):
    def setUp(self):
        self.campaign = mommy.make(
            'dpnk.Campaign',
        )
        mommy.make(
            "dpnk.Phase",
            phase_type="competition",
            campaign=self.campaign,
            date_from=datetime.date(year=2010, month=1, day=1),
            date_to=datetime.date(year=2019, month=12, day=12),
        )

    def test_str_team(self):
        """
        Test that __str__ returns CompetitionResult correct string if competition is for teams
        """
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__competitor_type="team",
            competition__campaign=self.campaign,
            team__name="Foo team",
            team__campaign=self.campaign,
        )
        self.assertEqual(str(competition_result), "Foo team")

    def test_str_team_none(self):
        """
        Test that __str__ returns CompetitionResult correct string if competition is for teams
        """
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__competitor_type="team",
            competition__campaign=self.campaign,
        )
        self.assertEqual(str(competition_result), "")

    def test_str_user(self):
        """
        Test that __str__ returns CompetitionResult correct string if competition is for users
        """
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__competitor_type="single_user",
            competition__campaign=self.campaign,
            user_attendance__userprofile__nickname="Foo user",
            user_attendance__campaign=self.campaign,
        )
        self.assertEqual(str(competition_result), "Foo user")

    def test_str_user_none(self):
        """
        Test that __str__ returns CompetitionResult correct string if competition is for users
        """
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__competitor_type="single_user",
            competition__campaign=self.campaign,
        )
        self.assertEqual(str(competition_result), "")

    def test_str_company(self):
        """
        Test that __str__ returns CompetitionResult correct string if competition is for companies
        """
        company = mommy.make(
            'dpnk.Company',
            name="Foo company",
        )
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__competitor_type="company",
            competition__campaign=self.campaign,
            company=company,
        )
        self.assertEqual(str(competition_result), "Foo company")

    def test_str_company_none(self):
        """
        Test that __str__ returns CompetitionResult correct string if competition is for companies without company
        """
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__competitor_type="company",
            competition__campaign=self.campaign,
        )
        self.assertEqual(str(competition_result), "")

    def test_get_result(self):
        """
        Test that get_result function works correctly
        """
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__campaign=self.campaign,
            result=0.345,
        )
        self.assertEqual(competition_result.get_result(), 0.3)

    def test_get_result_percentage(self):
        """
        Test that get_result_percentage function works correctly
        """
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__campaign=self.campaign,
            result=0.345,
        )
        self.assertEqual(competition_result.get_result_percentage(), 34.5)

    def test_get_result_percentage_none(self):
        """
        Test that get_result_percentage function works correctly if result is none.
        """
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__campaign=self.campaign,
        )
        self.assertEqual(competition_result.get_result_percentage(), 0)

    def test_get_team(self):
        """
        Test that get_team function works correctly
        """
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__competitor_type="team",
            competition__campaign=self.campaign,
            team__name="Foo team",
            team__campaign=self.campaign,
        )
        self.assertEqual(competition_result.get_team().name, "Foo team")

    def test_get_team_liberos(self):
        """
        Test that get_team function works correctly for liberos competition
        """
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__competitor_type="liberos",
            competition__campaign=self.campaign,
            user_attendance__team__name="Foo team",
            user_attendance__team__campaign=self.campaign,
            user_attendance__campaign=self.campaign,
        )
        self.assertEqual(competition_result.get_team().name, "Foo team")

    def test_get_city(self):
        """
        Test that get_city function works correctly
        """
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__campaign=self.campaign,
            competition__competitor_type="team",
            team__subsidiary__city__name="Foo city",
            team__campaign=self.campaign,
        )
        self.assertEqual(competition_result.get_city().name, "Foo city")

    def test_get_street(self):
        """
        Test that get_street function works correctly
        """
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__campaign=self.campaign,
            competition__competitor_type="team",
            team__subsidiary__address_street="Foo street",
            team__campaign=self.campaign,
        )
        self.assertEqual(competition_result.get_street(), "Foo street")

    def test_get_company(self):
        """
        Test that get_company function works correctly
        """
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__campaign=self.campaign,
            competition__competitor_type="team",
            team__subsidiary__company__name="Foo company",
            team__campaign=self.campaign,
        )
        self.assertEqual(competition_result.get_company().name, "Foo company")

    def test_get_company_company(self):
        """
        Test that get_company function works correctly for company competition
        """
        company = mommy.make(
            'dpnk.Company',
            name="Foo company",
        )
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__campaign=self.campaign,
            competition__competitor_type="company",
            company=company,
        )
        self.assertEqual(competition_result.get_company().name, "Foo company")

    def test_get_subsidiary(self):
        """
        Test that get_subsidiary function works correctly
        """
        company = mommy.make(
            'dpnk.Company',
            name="Foo company",
        )
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__campaign=self.campaign,
            competition__competitor_type="team",
            team__subsidiary__address_street="Foo street",
            team__campaign=self.campaign,
            team__subsidiary__company=company,
        )
        self.assertEqual(competition_result.get_subsidiary(), "Foo street / Foo company")

    def test_get_sequence_range(self):
        """
        Test that get_sequence_range function works correctly
        """
        competition = mommy.make(
            'dpnk.Competition',
            campaign=self.campaign,
        )
        mommy.make(
            'dpnk.CompetitionResult',
            competition=competition,
            result=1,
        )
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition=competition,
            result=1,
        )
        self.assertEqual(competition_result.get_sequence_range(), (1, 2))

    def test_get_sequence_range_same(self):
        """
        Test that get_sequence_range function works correctly.
        Case when both ranges are same.
        """
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__campaign=self.campaign,
            result=1,
        )
        self.assertEqual(competition_result.get_sequence_range(), (1, 1))

    def test_user_attendances_single_user(self):
        """
        Test that user_attendances function works correctly for single_user competition.
        """
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__competitor_type="single_user",
            competition__campaign=self.campaign,
            user_attendance__userprofile__nickname="Foo user",
            user_attendance__campaign=self.campaign,
        )
        self.assertListEqual(competition_result.user_attendances(), [competition_result.user_attendance])

    def test_user_attendances_team(self):
        """
        Test that user_attendances function works correctly for team competition.
        """
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__competitor_type="team",
            competition__campaign=self.campaign,
            team__name="Foo team",
            team__campaign=self.campaign,
        )
        user_attendance = mommy.make(
            'dpnk.UserAttendance',
            team=competition_result.team,
            campaign=self.campaign,
            approved_for_team="approved",
        )
        self.assertListEqual(list(competition_result.user_attendances()), [user_attendance])

    def test_user_attendances_company(self):
        """
        Test that user_attendances function works correctly for company competition.
        """
        company = mommy.make(
            'dpnk.Company',
            name="Foo company",
        )
        competition_result = mommy.make(
            'dpnk.CompetitionResult',
            competition__competitor_type="company",
            competition__campaign=self.campaign,
            company=company,
        )
        user_attendance = mommy.make(
            'dpnk.UserAttendance',
            team__subsidiary__company=company,
            team__campaign=self.campaign,
            campaign=self.campaign,
        )
        self.assertListEqual(list(competition_result.user_attendances()), [user_attendance])
