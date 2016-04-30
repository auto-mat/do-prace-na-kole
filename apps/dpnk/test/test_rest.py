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
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from django.test.utils import override_settings
from dpnk import util, models
from dpnk.models import UserAttendance, Team
from dpnk.test.util import DenormMixin
from dpnk.test.util import print_response  # noqa
from freezegun import freeze_time
import datetime
import settings


@freeze_time("2016-01-14")
@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class RestTests(DenormMixin, TestCase):
    fixtures = ['campaign', 'auth_user', 'users', 'transactions', 'batches', 'trips']

    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer")
        self.client.force_login(User.objects.get(pk=1128), settings.AUTHENTICATION_BACKENDS[0])
        util.rebuild_denorm_models(Team.objects.filter(pk=1))
        util.rebuild_denorm_models(UserAttendance.objects.filter(pk=1115))

    def test_gpx_get(self):
        address = reverse("gpxfile-list")
        response = self.client.get(address)
        self.assertContains(response, '{"id":1,"trip_date":"2010-11-01","direction":"trip_to","file":null}')
        self.assertContains(response, '{"id":2,"trip_date":"2010-11-14","direction":"trip_from","file":"http://testing-campaign.testserver/media/modranska-rokle.gpx"}')

    def test_gpx_post(self):
        address = reverse("gpxfile-list")
        with open('apps/dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                'trip_date': "2010-12-02",
                'direction': 'trip_to',
                'file': gpxfile,
            }
            response = self.client.post(address, post_data)
            print_response(response)
            self.assertContains(
                response,
                '"trip_date":"2010-12-02","direction":"trip_to","file":"http://testing-campaign.testserver/media/gpx_tracks/track-2016-01-14-modranska-rokle',
                status_code=201
            )
            gpx_file = models.GpxFile.objects.get(trip_date=datetime.date(2010, 12, 2))
            self.assertEquals(gpx_file.direction, "trip_to")

    def test_gpx_unknown_campaign(self):
        self.client = Client(HTTP_HOST="testing-campaign-unknown.testserver", HTTP_REFERER="test-referer")
        self.client.force_login(User.objects.get(pk=1128), settings.AUTHENTICATION_BACKENDS[0])
        address = reverse("gpxfile-list")
        with open('apps/dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                'trip_date': "2010-12-02",
                'direction': 'trip_to',
                'file': gpxfile,
            }
            response = self.client.post(address, post_data)
            self.assertContains(response, '{"detail":"Campaign with this slug not found"}', status_code=404)

    # TODO: make this working
    # def test_gpx_duplicate_gpx(self):
    #     address = reverse("gpxfile-list")
    #     with open('apps/dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
    #         post_data = {
    #             'trip_date': "2010-12-01",
    #             'direction': 'trip_to',
    #             'file': gpxfile,
    #         }
    #         response = self.client.post(address, post_data)
    #         self.assertContains(response, '{"detail":"GPX for this day and trip already uploaded"}', status_code=409)


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class RestTestsLogout(DenormMixin, TestCase):
    fixtures = ['campaign', 'auth_user', 'users']

    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer")
        util.rebuild_denorm_models(Team.objects.filter(pk=1))
        util.rebuild_denorm_models(UserAttendance.objects.filter(pk=1115))

    def test_competition_get(self):
        address = reverse("competition-list")
        response = self.client.get(address)
        self.assertContains(response, '"slug":"FQ-LB"')
        self.assertContains(response, '"name":"Pravidelnost"')
        self.assertContains(response, '"results":"http://testing-campaign.testserver/rest/result/FQ-LB/"')

    def test_competitionresults_get(self):
        address = reverse("result-list", kwargs={"competition_slug": "FQ-LB"})
        response = self.client.get(address)
        self.assertContains(response, '"team":"http://testing-campaign.testserver/rest/team/1/"')
        self.assertContains(response, '"result":100.0')

    def test_competitionresults_get_unknown_competition(self):
        address = reverse("result-list", kwargs={"competition_slug": "unknown"})
        response = self.client.get(address)
        self.assertContains(response, '{"detail":"Competition with this slug not found"}', status_code=405)
