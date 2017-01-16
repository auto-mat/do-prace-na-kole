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
            ('team', 'get_team', 'Tým'),
            ('company', 'get_company', 'Spo&shy;leč&shy;nost'),
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
            ('result_divident', 'result_divident', 'Po&shy;čet za&shy;po&shy;čí&shy;ta&shy;ných jí&shy;zd'),
            ('result_divisor', 'result_divisor', 'Cel&shy;ko&shy;vý po&shy;čet cest'),
            ('competitor', 'user_attendance', 'Sou&shy;tě&shy;ží&shy;cí'),
            ('team', 'get_team', 'Tým'),
            ('company', 'get_company', 'Spo&shy;leč&shy;nost'),
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
            ('result_divident', 'result_divident', 'Po&shy;čet za&shy;po&shy;čí&shy;ta&shy;ných jí&shy;zd'),
            ('result_divisor', 'result_divisor', 'Cel&shy;ko&shy;vý po&shy;čet cest'),
            ('member_count', 'team__member_count', 'Po&shy;čet sou&shy;tě&shy;ží&shy;cí&shy;ch v&nbsp;tý&shy;mu'),
            ('competitor', 'get_team', 'Sou&shy;tě&shy;ží&shy;cí'),
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
            ('team', 'get_team', 'Tým'),
            ('company', 'get_company', 'Spo&shy;leč&shy;nost'),
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
            ('city', 'get_city', 'Měs&shy;to'),
        ]
        self.assertListEqual(columns, expected_columns)
