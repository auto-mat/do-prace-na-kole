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
from django.test.utils import override_settings

from dpnk import models

from model_mommy import mommy


class TestGetColumns(TestCase):
    def test_single_length_competition(self):
        """
        Test that get_columns works properly
        """
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type='single_user',
            competition_type='length',
        )
        columns = competition.get_columns()
        expected_columns = [
            ('result_order', 'get_sequence_range', 'Po&shy;řa&shy;dí'),
            ('result_value', 'get_result', 'Ki&shy;lo&shy;me&shy;trů'),
            ('competitor', 'user_attendance', 'Sou&shy;tě&shy;ží&shy;cí'),
            ('team', 'get_team_name', 'Tým'),
            ('company', 'get_company', 'Spo&shy;leč&shy;nost'),
            ('occupation', 'get_occupation', 'Pro&shy;fe&shy;se'),
            ('sex', 'get_sex', 'Po&shy;hla&shy;ví'),
            ('city', 'get_city', 'Měs&shy;to'),
        ]
        self.assertListEqual(columns, expected_columns)

    def test_single_frequency_competition(self):
        """
        Test that get_columns works properly for frequency competition
        """
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type='single_user',
            competition_type='frequency',
        )
        columns = competition.get_columns()
        expected_columns = [
            ('result_order', 'get_sequence_range', 'Po&shy;řa&shy;dí'),
            ('result_value', 'get_result_percentage', '% jízd'),
            ('result_divident', 'get_result_divident', 'Po&shy;čet za&shy;po&shy;čí&shy;ta&shy;ných jí&shy;zd'),
            ('result_divisor', 'get_result_divisor', 'Cel&shy;ko&shy;vý po&shy;čet cest'),
            ('competitor', 'user_attendance', 'Sou&shy;tě&shy;ží&shy;cí'),
            ('team', 'get_team_name', 'Tým'),
            ('company', 'get_company', 'Spo&shy;leč&shy;nost'),
            ('occupation', 'get_occupation', 'Pro&shy;fe&shy;se'),
            ('sex', 'get_sex', 'Po&shy;hla&shy;ví'),
            ('city', 'get_city', 'Měs&shy;to'),
        ]
        self.assertListEqual(columns, expected_columns)

    def test_team_frequency_competition(self):
        """
        Test that get_columns works properly for team competition
        """
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type='team',
            competition_type='frequency',
        )
        columns = competition.get_columns()
        expected_columns = [
            ('result_order', 'get_sequence_range', 'Po&shy;řa&shy;dí'),
            ('result_value', 'get_result_percentage', '% jízd prů&shy;měr&shy;ně'),
            ('result_divident', 'get_result_divident', 'Po&shy;čet za&shy;po&shy;čí&shy;ta&shy;ných jí&shy;zd'),
            ('result_divisor', 'get_result_divisor', 'Cel&shy;ko&shy;vý po&shy;čet cest'),
            ('member_count', 'team__member_count', 'Po&shy;čet sou&shy;tě&shy;ží&shy;cí&shy;ch v&nbsp;tý&shy;mu'),
            ('competitor', 'get_team_name', 'Sou&shy;tě&shy;ží&shy;cí'),
            ('company', 'get_company', 'Spo&shy;leč&shy;nost'),
            ('city', 'get_city', 'Měs&shy;to'),
        ]
        self.assertListEqual(columns, expected_columns)

    def test_single_questionnaire_competition(self):
        """
        Test that get_columns works properly for frequency competition
        """
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type='single_user',
            competition_type='questionnaire',
        )
        columns = competition.get_columns()
        expected_columns = [
            ('result_order', 'get_sequence_range', 'Po&shy;řa&shy;dí'),
            ('result_value', 'get_result', 'Bo&shy;dů'),
            ('competitor', 'user_attendance', 'Sou&shy;tě&shy;ží&shy;cí'),
            ('team', 'get_team_name', 'Tým'),
            ('company', 'get_company', 'Spo&shy;leč&shy;nost'),
            ('occupation', 'get_occupation', 'Pro&shy;fe&shy;se'),
            ('sex', 'get_sex', 'Po&shy;hla&shy;ví'),
            ('city', 'get_city', 'Měs&shy;to'),
        ]
        self.assertListEqual(columns, expected_columns)

    def test_company_length_competition(self):
        """
        Test that get_columns works properly for frequency competition
        """
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type='company',
            competition_type='length',
        )
        columns = competition.get_columns()
        expected_columns = [
            ('result_order', 'get_sequence_range', 'Po&shy;řa&shy;dí'),
            ('result_value', 'get_result', 'Ki&shy;lo&shy;me&shy;trů prů&shy;měr&shy;ně'),
            ('competitor', 'get_company', 'Sou&shy;tě&shy;ží&shy;cí'),
        ]
        self.assertListEqual(columns, expected_columns)

    def test_team_length(self):
        """
        Test that get_columns works properly for team length competition
        """
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type='team',
            competition_type='length',
        )
        columns = competition.get_columns()
        expected_columns = [
            ('result_order', 'get_sequence_range', 'Po&shy;řa&shy;dí'),
            ('result_value', 'get_result', 'Ki&shy;lo&shy;me&shy;trů prů&shy;měr&shy;ně'),
            ('result_divident', 'get_result_divident', 'Po&shy;čet za&shy;po&shy;čí&shy;ta&shy;ných ki&shy;lo&shy;me&shy;trů'),
            ('member_count', 'team__member_count', 'Po&shy;čet sou&shy;tě&shy;ží&shy;cí&shy;ch v&nbsp;tý&shy;mu'),
            ('competitor', 'get_team_name', 'Sou&shy;tě&shy;ží&shy;cí'),
            ('company', 'get_company', 'Spo&shy;leč&shy;nost'),
            ('city', 'get_city', 'Měs&shy;to'),
        ]
        self.assertListEqual(columns, expected_columns)


class TestGetCompanyQuerystring(TestCase):
    def test_company(self):
        """
        Test that get_company_querystring works properly for company competition
        """
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type='company',
        )
        self.assertEqual(competition.get_company_querystring(), "company")

    def test_team(self):
        """
        Test that get_company_querystring works properly for team competition
        """
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type='team',
        )
        self.assertEqual(competition.get_company_querystring(), "team__subsidiary__company")

    def test_single_user(self):
        """
        Test that get_company_querystring works properly for single_user competition
        """
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type='single_user',
        )
        self.assertEqual(competition.get_company_querystring(), "user_attendance__team__subsidiary__company")


class TestHasEntryNotOpened(TestCase):
    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=11, day=19),
    )
    def test_true(self):
        """
        Test that has_entry_not_opened function returns true
        """
        competition = mommy.make(
            'dpnk.Competition',
            entry_after_beginning_days=0,
            date_from=datetime.date(year=2010, month=11, day=19),
            date_to=datetime.date(year=2010, month=11, day=21),
        )
        self.assertEqual(competition.has_entry_not_opened(), True)

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=11, day=18),
    )
    def test_false(self):
        """
        Test that has_entry_not_opened function returns false
        """
        competition = mommy.make(
            'dpnk.Competition',
            entry_after_beginning_days=0,
            date_from=datetime.date(year=2010, month=11, day=19),
            date_to=datetime.date(year=2010, month=11, day=21),
        )
        self.assertEqual(competition.has_entry_not_opened(), False)

    def test_not_fail(self):
        """
        Test that has_entry_not_opened function doesn't fail if date is not set
        """
        competition = mommy.make(
            'dpnk.Competition',
            entry_after_beginning_days=0,
        )
        self.assertEqual(competition.has_entry_not_opened(), False)


class TestTypeString(TestCase):
    def setUp(self):
        self.city = mommy.make('dpnk.City', name="Testing city")

    def test_team_frequency(self):
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type="team",
            competition_type="frequency",
        )
        self.assertEquals(str(competition.type_string()), " soutěž na pravidelnost týmů   ")

    def test_single_questionnaire(self):
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type="single_user",
            competition_type="questionnaire",
        )
        self.assertEquals(str(competition.type_string()), " dotazník jednotlivců   ")

    def test_single_length_city_sex(self):
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type="single_user",
            competition_type="length",
            city=[self.city],
            sex="male",
        )
        self.assertEquals(str(competition.type_string()), " soutěž na vzdálenost jednotlivců  ve městě Testing city pro muže")

    def test_single_length_city(self):
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type="single_user",
            competition_type="length",
            city=[self.city],
        )
        self.assertEquals(str(competition.type_string()), " soutěž na vzdálenost jednotlivců  ve městě Testing city ")

    def test_team_frequency_company(self):
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type="team",
            competition_type="frequency",
            company__name="Testing company",
        )
        self.assertEquals(str(competition.type_string()), "vnitrofiremní soutěž na pravidelnost týmů organizace Testing company  ")

    def test_team_frequency_commute_modes(self):
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type="team",
            competition_type="frequency",
            commute_modes=models.CommuteMode.objects.filter(slug__in=('bicycle', 'by_foot')),
        )
        self.assertEquals(str(competition.type_string()), " soutěž na pravidelnost týmů    pro cesty s prostředky Kolo, Chůze/běh")

    def test_company_length_city(self):
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type="company",
            competition_type="length",
            city=[self.city],
        )
        self.assertEquals(str(competition.type_string()), " soutěž na vzdálenost organizací  ve městě Testing city ")

    def test_team_length_city_sex(self):
        competition = mommy.make(
            'dpnk.Competition',
            competitor_type="team",
            competition_type="length",
            city=[self.city],
            sex="male",
        )
        self.assertEquals(str(competition.type_string()), " soutěž na vzdálenost týmů  ve městě Testing city pro muže")


class GetResultsIdRankDictTests(TestCase):
    def test_dict(self):
        competition = mommy.make('dpnk.Competition')
        mommy.make('dpnk.CompetitionResult', result="3", competition=competition, id=1),
        mommy.make('dpnk.CompetitionResult', result="3", competition=competition, id=2),
        mommy.make('dpnk.CompetitionResult', result="2", competition=competition, id=3),
        mommy.make('dpnk.CompetitionResult', result="2", competition=competition, id=4),
        mommy.make('dpnk.CompetitionResult', result="2", competition=competition, id=5),
        mommy.make('dpnk.CompetitionResult', result="1", competition=competition, id=6),
        expected_dict = {
            1: (1, 2),
            2: (1, 2),
            3: (3, 5),
            4: (3, 5),
            5: (3, 5),
            6: (6, 6),
        }
        results = competition.annotate_results_rank(competition.results)
        self.assertDictEqual(competition.get_result_id_rank_dict(results), expected_dict)


class SelectRelatedResultsTests(TestCase):
    def test_single(self):
        """ Test if selecting related on single user competition doesn't fail """
        competition = mommy.make('dpnk.Competition', competitor_type='single_user')
        mommy.make('dpnk.CompetitionResult', competition=competition),
        qs = competition.select_related_results(competition.results)
        expected_qs = ['<CompetitionResult: >']
        self.assertQuerysetEqual(qs, expected_qs)

    def test_team(self):
        """ Test if selecting related on team competition doesn't fail """
        competition = mommy.make('dpnk.Competition', competitor_type='team')
        mommy.make('dpnk.CompetitionResult', competition=competition),
        qs = competition.select_related_results(competition.results)
        expected_qs = ['<CompetitionResult: >']
        self.assertQuerysetEqual(qs, expected_qs)

    def test_company(self):
        """ Test if selecting related on company competition doesn't fail """
        competition = mommy.make('dpnk.Competition', competitor_type='company')
        mommy.make('dpnk.CompetitionResult', competition=competition),
        qs = competition.select_related_results(competition.results)
        expected_qs = ['<CompetitionResult: >']
        self.assertQuerysetEqual(qs, expected_qs)


class TestHasStarted(TestCase):
    def test_no_date_from(self):
        competition = mommy.make('dpnk.Competition')
        self.assertEqual(competition.has_started(), True)

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=11, day=21),
    )
    def test_no_true(self):
        competition = mommy.make(
            'dpnk.Competition',
            date_from=datetime.date(year=2010, month=11, day=21),
        )
        self.assertEqual(competition.has_started(), True)

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=11, day=20),
    )
    def test_no_false(self):
        competition = mommy.make(
            'dpnk.Competition',
            date_from=datetime.date(year=2010, month=11, day=21),
        )
        self.assertEqual(competition.has_started(), False)


class TestHasFinished(TestCase):
    def test_no_date_from(self):
        competition = mommy.make('dpnk.Competition')
        self.assertEqual(competition.has_finished(), False)

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=11, day=22),
    )
    def test_no_true(self):
        competition = mommy.make(
            'dpnk.Competition',
            date_to=datetime.date(year=2010, month=11, day=21),
        )
        self.assertEqual(competition.has_finished(), True)

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=11, day=21),
    )
    def test_no_false(self):
        competition = mommy.make(
            'dpnk.Competition',
            date_to=datetime.date(year=2010, month=11, day=21),
        )
        self.assertEqual(competition.has_finished(), False)
