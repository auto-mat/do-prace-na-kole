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

from django.test import Client, RequestFactory, TestCase

from dpnk.test.util import print_response  # noqa
from dpnk.views_results import CompetitionResultListJson

from model_mommy import mommy


class CompetitionResultListJsonTeamTests(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.example.com", HTTP_REFERER="test-referer")
        self.factory = RequestFactory()
        self.campaign = mommy.make(
            'dpnk.Campaign',
            slug="testing-campaign",
        )
        team_length_competition = mommy.make(
            'dpnk.Competition',
            campaign=self.campaign,
            competition_type='length',
            competitor_type='team',
            slug="competition",
        )
        mommy.make(
            'dpnk.CompetitionResult',
            result="1",
            result_divident="1.2",
            result_divisor="1.1",
            competition=team_length_competition,
            team__campaign=self.campaign,
            team__member_count=1,
            team__subsidiary__city__name="foo city",
            team__subsidiary__company__name="bar company",
            team__name="foo team",
        )
        mommy.make(
            'dpnk.CompetitionResult',
            result="0.5",
            result_divident="0.5",
            result_divisor="1.0",
            competition=team_length_competition,
            team__campaign=self.campaign,
            team__member_count=1,
            team__subsidiary__city__name="a city",
            team__subsidiary__company__name="a company",
            team__name="a team",
        )

    def test_team_length(self):
        """ Test if team length competition result JSON is returned """
        request = self.factory.get('')
        request.subdomain = "testing-campaign"
        response = CompetitionResultListJson.as_view()(request, competition_slug='competition')
        expected_json = {
            "recordsTotal": 2,
            "data": [
                ["1.", "1.0", 1.2, "0", "foo team", "bar company", "foo city"],
                ["2.", "0.5", 0.5, "0", "a team", "a company", "a city"],
            ],
            "draw": 0,
            "result": "ok",
            "recordsFiltered": 2,
        }
        self.assertJSONEqual(response.content.decode(), expected_json)

    def test_team_length_search(self):
        """ Test if searching by string works """
        get_params = {'search[value]': 'oo cit'}
        request = self.factory.get('', get_params)
        request.subdomain = "testing-campaign"
        response = CompetitionResultListJson.as_view()(request, competition_slug='competition')
        expected_json = {
            "recordsTotal": 2,
            "data": [
                ["1.", "1.0", 1.2, "0", "foo team", "bar company", "foo city"],
            ],
            "draw": 0,
            "result": "ok",
            "recordsFiltered": 1,
        }
        self.assertJSONEqual(response.content.decode(), expected_json)

    def test_team_length_company_search(self):
        """ Test if searching by company name works """
        get_params = {'columns[0][search][value]': 'company'}
        request = self.factory.get('', get_params)
        request.subdomain = "testing-campaign"
        response = CompetitionResultListJson.as_view()(request, competition_slug='competition')
        expected_json = {
            "recordsTotal": 2,
            "data": [
                ["1.", "1.0", 1.2, "0", "foo team", "bar company", "foo city"],
                ["2.", "0.5", 0.5, "0", "a team", "a company", "a city"],
            ],
            "draw": 0,
            "result": "ok",
            "recordsFiltered": 2,
        }
        self.assertJSONEqual(response.content.decode(), expected_json)

    def test_team_length_company_search_quotes(self):
        """ Test if searching by exact company name works """
        get_params = {'columns[0][search][value]': '"bar company"'}
        request = self.factory.get('', get_params)
        request.subdomain = "testing-campaign"
        response = CompetitionResultListJson.as_view()(request, competition_slug='competition')
        expected_json = {
            "recordsTotal": 2,
            "data": [
                ["1.", "1.0", 1.2, "0", "foo team", "bar company", "foo city"],
            ],
            "draw": 0,
            "result": "ok",
            "recordsFiltered": 1,
        }
        self.assertJSONEqual(response.content.decode(), expected_json)


class CompetitionResultListJsonSingleTests(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.example.com", HTTP_REFERER="test-referer")
        self.factory = RequestFactory()
        self.campaign = mommy.make(
            'dpnk.Campaign',
            slug="testing-campaign",
        )
        mommy.make(
            "dpnk.Phase",
            phase_type="competition",
            campaign=self.campaign,
            date_from=datetime.date(year=2010, month=1, day=1),
            date_to=datetime.date(year=2019, month=12, day=12),
        )
        single_frequency_competition = mommy.make(
            'dpnk.Competition',
            campaign=self.campaign,
            competition_type='frequency',
            competitor_type='single_user',
            slug="competition",
        )
        mommy.make(
            'dpnk.CompetitionResult',
            result="1",
            result_divident="1.3",
            result_divisor="1.1",
            competition=single_frequency_competition,
            user_attendance__userprofile__nickname="foo user",
            user_attendance__userprofile__user__first_name="Adam",
            user_attendance__userprofile__user__last_name="Rosa",
            user_attendance__campaign=self.campaign,
            user_attendance__team__campaign=self.campaign,
            user_attendance__team__member_count=1,
            user_attendance__team__subsidiary__city__name="foo city",
            user_attendance__team__subsidiary__company__name="foo company",
            user_attendance__team__name="foo team",
        )
        mommy.make(
            'dpnk.CompetitionResult',
            result="1",
            result_divident="1.2",
            result_divisor="1.1",
            competition=single_frequency_competition,
            user_attendance__userprofile__nickname=None,
            user_attendance__userprofile__user__first_name="Jan",
            user_attendance__userprofile__user__last_name="Novák",
            user_attendance__campaign=self.campaign,
            user_attendance__team__campaign=self.campaign,
            user_attendance__team__member_count=1,
            user_attendance__team__subsidiary__city__name="bar city",
            user_attendance__team__subsidiary__company__name="bar company",
            user_attendance__team__name="bar team",
        )

    def test_get(self):
        """ Test if single user frequency competition result JSON is returned """
        request = self.factory.get('')
        request.subdomain = "testing-campaign"
        response = CompetitionResultListJson.as_view()(request, competition_slug='competition')
        expected_json = {
            "recordsTotal": 2,
            "data": [
                ["1.&nbsp;-&nbsp;2.", "100.0", 1.3, 1.1, "foo user", "foo team", "foo company", "foo city"],
                ["1.&nbsp;-&nbsp;2.", "100.0", 1.2, 1.1, "Jan Novák", "bar team", "bar company", "bar city"],
            ],
            "draw": 0,
            "result": "ok",
            "recordsFiltered": 2,
        }
        self.assertJSONEqual(response.content.decode(), expected_json)

    def test_search_user_nickname(self):
        """ Test if searching by user nickname field works """
        get_params = {'search[value]': 'oo user'}
        request = self.factory.get('', get_params)
        request.subdomain = "testing-campaign"
        response = CompetitionResultListJson.as_view()(request, competition_slug='competition')
        expected_json = {
            "recordsTotal": 2,
            "data": [
                ["1.&nbsp;-&nbsp;2.", "100.0", 1.3, 1.1, "foo user", "foo team", "foo company", "foo city"],
            ],
            "draw": 0,
            "result": "ok",
            "recordsFiltered": 1,
        }
        self.assertJSONEqual(response.content.decode(), expected_json)

    def test_search_user_name(self):
        """ Test if searching by user name field works """
        get_params = {'search[value]': 'Novak Jan'}
        request = self.factory.get('', get_params)
        request.subdomain = "testing-campaign"
        response = CompetitionResultListJson.as_view()(request, competition_slug='competition')
        expected_json = {
            "recordsTotal": 2,
            "data": [
                ["1.&nbsp;-&nbsp;2.", "100.0", 1.2, 1.1, "Jan Novák", "bar team", "bar company", "bar city"],
            ],
            "draw": 0,
            "result": "ok",
            "recordsFiltered": 1,
        }
        self.assertJSONEqual(response.content.decode(), expected_json)

    def test_search_user_name_not_found(self):
        """
        If the user has nickname, we can't find by his name,
        otherwise the name can reverse engeneered.
        """
        get_params = {'search[value]': 'Rosa'}
        request = self.factory.get('', get_params)
        request.subdomain = "testing-campaign"
        response = CompetitionResultListJson.as_view()(request, competition_slug='competition')
        expected_json = {
            "recordsTotal": 2,
            "data": [],
            "draw": 0,
            "result": "ok",
            "recordsFiltered": 0,
        }
        self.assertJSONEqual(response.content.decode(), expected_json)
