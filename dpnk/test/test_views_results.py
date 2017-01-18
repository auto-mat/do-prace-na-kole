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

from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from model_mommy import mommy

from dpnk.test.util import print_response  # noqa


class CompetitionResultListJsonTests(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.example.com", HTTP_REFERER="test-referer")

    def test_team_length(self):
        campaign = mommy.make(
            'dpnk.Campaign',
            slug="testing-campaign",
        )
        mommy.make(
            'dpnk.CompetitionResult',
            competition__campaign=campaign,
            competition__competition_type='length',
            competition__competitor_type='team',
            competition__slug="competition",
            result="1",
            result_divident="1.2",
            result_divisor="1.1",
            team__campaign=campaign,
            team__member_count=1,
            team__subsidiary__city__name="foo city",
            team__subsidiary__company__name="bar company",
            team__name="foo team",
        )
        address = reverse('competition_result_list_json', kwargs={'competition_slug': 'competition'})
        response = self.client.get(address)
        expected_json = {
            "recordsTotal": 1,
            "data": [["1.", "1.0", 1.2, "0", "foo team", "bar company", "foo city"]],
            "draw": 0,
            "result": "ok",
            "recordsFiltered": 1,
        }
        self.assertJSONEqual(response.content.decode(), expected_json)
