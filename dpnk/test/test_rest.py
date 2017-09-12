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

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from django.test.utils import override_settings

from dpnk import models, util
from dpnk.models import Team, UserAttendance
from dpnk.test.util import print_response  # noqa

from freezegun import freeze_time

from model_mommy import mommy

import settings

from .mommy_recipes import UserAttendanceRecipe


@freeze_time("2016-01-14")
@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class RestTests(TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches', 'trips']

    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer")
        self.client.force_login(User.objects.get(pk=1128), settings.AUTHENTICATION_BACKENDS[0])
        util.rebuild_denorm_models(Team.objects.filter(pk=1))
        util.rebuild_denorm_models(UserAttendance.objects.filter(pk=1115))

    def test_gpx_get(self):
        address = reverse("gpxfile-list")
        response = self.client.get(address)
        self.assertContains(
            response,
            '{"id":1,"trip_date":"2010-11-01","direction":"trip_to","file":null,"commuteMode":"bicycle",'
            '"durationSeconds":null,"distanceMeters":null,"sourceApplication":null}',
        )
        self.assertContains(
            response,
            '{"id":2,"trip_date":"2010-11-14","direction":"trip_from","file":"http://testing-campaign.testserver%smodranska-rokle.gpx",'
            '"commuteMode":"bicycle","durationSeconds":null,"distanceMeters":null,"sourceApplication":null}' % settings.MEDIA_URL,
        )

    def test_gpx_post(self):
        address = reverse("gpxfile-list")
        with open('dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                'trip_date': "2010-12-02",
                'direction': 'trip_to',
                'file': gpxfile,
            }
            response = self.client.post(address, post_data)
            self.assertContains(
                response,
                '"trip_date":"2010-12-02",'
                '"direction":"trip_to",'
                '"file":"http://testing-campaign.testserver%sgpx_tracks/dpnk-%s/track-2016-01-14-modranska-rokle' % (
                    settings.MEDIA_URL,
                    models.Campaign.objects.get(slug="testing-campaign").pk,
                ),
                status_code=201,
            )
            gpx_file = models.GpxFile.objects.get(trip_date=datetime.date(2010, 12, 2))
            self.assertEquals(gpx_file.direction, "trip_to")

    def test_gpx_unknown_campaign(self):
        self.client = Client(HTTP_HOST="testing-campaign-unknown.testserver", HTTP_REFERER="test-referer")
        self.client.force_login(User.objects.get(pk=1128), settings.AUTHENTICATION_BACKENDS[0])
        address = reverse("gpxfile-list")
        with open('dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                'trip_date': "2010-12-02",
                'direction': 'trip_to',
                'file': gpxfile,
            }
            response = self.client.post(address, post_data)
            self.assertContains(
                response,
                '<div class="alert alert-danger">Kampaň s identifikátorem testing-campaign-unknown neexistuje. Zadejte prosím správnou adresu.</div>',
                html=True,
                status_code=404,
            )

    def test_gpx_duplicate_gpx(self):
        mommy.make(
            'GpxFile',
            trip_date=datetime.date(2010, 12, 1),
            direction="trip_to",
            user_attendance=UserAttendance.objects.get(pk=1115),
        )
        with open('dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                'trip_date': "2010-12-01",
                'direction': 'trip_to',
                'file': gpxfile,
            }
            response = self.client.post(reverse("gpxfile-list"), post_data)
            self.assertJSONEqual(
                response.content.decode(),
                {"detail": "GPX for this day and trip already uploaded"},
            )
            self.assertEqual(response.status_code, 409)


@override_settings(
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class TokenAuthenticationTests(TestCase):

    def setUp(self):
        self.user_attendance = UserAttendanceRecipe.make()
        self.client = Client(
            HTTP_HOST="testing-campaign.example.com",
            HTTP_REFERER="test-referer",
            HTTP_AUTHORIZATION="Token %s" % self.user_attendance.userprofile.user.auth_token,
        )

    def test_track_post(self):
        response = self.client.post(
            reverse("gpxfile-list"),
            {
                'trip_date': "2010-12-02",
                'direction': 'trip_to',
                "track": '{"type": "MultiLineString", "coordinates": [[[14.0, 50.0], [14.0, 51.0]]]}',
            },
        )
        self.assertEquals(response.status_code, 201)
        gpx_file = models.GpxFile.objects.get(trip_date=datetime.date(2010, 12, 2))
        self.assertEquals(gpx_file.length(), 111.24)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "id": gpx_file.id,
                "trip_date": "2010-12-02",
                "direction": "trip_to",
                "file": None,
                "commuteMode": "bicycle",
                "durationSeconds": None,
                "distanceMeters": None,
                "sourceApplication": None,
            },
        )

# @override_settings(
#     SITE_ID=2,
#     FAKE_DATE=datetime.date(year=2010, month=11, day=20),
# )
# class RestTestsLogout(DenormMixin, TestCase):
#     fixtures = ['sites', 'campaign', 'auth_user', 'users']
#
#     def setUp(self):
#         super().setUp()
#         self.client = Client(HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer")
#         util.rebuild_denorm_models(Team.objects.filter(pk=1))
#         util.rebuild_denorm_models(UserAttendance.objects.filter(pk=1115))
#
#     def test_competition_get(self):
#         address = reverse("competition-list")
#         response = self.client.get(address)
#         self.assertContains(response, '"slug":"FQ-LB"')
#         self.assertContains(response, '"name":"Pravidelnost týmů"')
#         self.assertContains(response, '"results":"http://testing-campaign.testserver/rest/result/FQ-LB/"')
#
#     def test_competitionresults_get(self):
#         address = reverse("result-list", kwargs={"competition_slug": "FQ-LB"})
#         response = self.client.get(address)
#         self.assertContains(response, '"team":"http://testing-campaign.testserver/rest/team/1/"')
#         self.assertContains(response, '"result":"100.000000"')
#
#     def test_competitionresults_get_unknown_competition(self):
#         address = reverse("result-list", kwargs={"competition_slug": "unknown"})
#         response = self.client.get(address)
#         self.assertContains(response, '{"detail":"Competition with this slug not found"}', status_code=405)
