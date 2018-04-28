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
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from dpnk import models, util
from dpnk.models import Team, UserAttendance
from dpnk.test.util import print_response  # noqa

from freezegun import freeze_time

from model_mommy import mommy

from rest_framework.test import APIClient

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
        self.client = APIClient(HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer")
        self.client.force_login(User.objects.get(pk=1128), settings.AUTHENTICATION_BACKENDS[0])
        util.rebuild_denorm_models(Team.objects.filter(pk=1))
        util.rebuild_denorm_models(UserAttendance.objects.filter(pk=1115))

    def test_dpnk_rest_gpx_gz_no_login(self):
        post_data = {
            'trip_date': '2010-11-01',
            'sourceApplication': 'test_app',
            'direction': 'trip_to',
        }
        self.client.logout()
        response = self.client.post('/rest/gpx/', post_data, format='multipart', follow=True)
        self.assertJSONEqual(response.content.decode(), {'detail': 'Nebyly zadány přihlašovací údaje.'})
        self.assertEqual(response.status_code, 401)

    def test_dpnk_rest_gpx_gz_parse_error(self):
        with open('dpnk/test_files/DSC00002.JPG', 'rb') as gpxfile:
            post_data = {
                'trip_date': '2010-11-15',
                'direction': 'trip_to',
                'sourceApplication': 'test_app',
                'file': gpxfile,
            }
            response = self.client.post('/rest/gpx/', post_data, format='multipart', follow=True)
            self.assertJSONEqual(response.content.decode(), {"detail": "Can't parse GPX file"})
            self.assertEqual(response.status_code, 400)

    def test_gpx_get101(self):
        address = reverse("gpxfile-detail", kwargs={'pk': 101})
        response = self.client.get(address)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "id": 101,
                "trip_date": "2010-11-01",
                "direction": "trip_to",
                "file": None,
                "commuteMode": "by_foot",
                "durationSeconds": None,
                "distanceMeters": 5000,
                "track": None,
                "sourceApplication": None,
            },
        )

    def test_gpx_get2(self):
        address = reverse("gpxfile-detail", kwargs={'pk': 2})
        response = self.client.get(address)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "id": 2,
                "trip_date": "2010-11-14",
                "direction": "trip_from",
                "file": "http://testing-campaign.testserver%smodranska-rokle.gpx" % settings.MEDIA_URL,
                "commuteMode": "bicycle",
                "durationSeconds": None,
                "distanceMeters": 156900,
                'track': {
                    'coordinates': [[[0.0, 0.0], [-1.0, 1.0]]],
                    'type': 'MultiLineString',
                },
                "sourceApplication": None,
            },
        )

    def test_gpx_post(self):
        address = reverse("gpxfile-list")
        with open('dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                'trip_date': "2010-11-19",
                'direction': 'trip_to',
                'sourceApplication': 'test_app',
                'file': gpxfile,
            }
            response = self.client.post(address, post_data)
            self.assertEquals(response.status_code, 201)
            trip = models.Trip.objects.get(date=datetime.date(2010, 11, 19))
            self.assertJSONEqual(
                response.content.decode(),
                {
                    "id": trip.id,
                    "distanceMeters": 13320,
                    "durationSeconds": None,
                    "sourceApplication": 'test_app',
                    "trip_date": "2010-11-19",
                    "direction": "trip_to",
                    "commuteMode": "bicycle",
                    "file": "http://testing-campaign.testserver%s%s" % (
                        settings.MEDIA_URL,
                        trip.gpx_file.name,
                    ),
                },
            )
            self.assertEquals(trip.direction, "trip_to")

    def test_dpnk_rest_gpx_gz(self):
        with open('dpnk/test_files/modranska-rokle.gpx.gz', 'rb') as gpxfile:
            post_data = {
                'trip_date': '2010-11-17',
                'direction': 'trip_to',
                'sourceApplication': 'test_app',
                'file': gpxfile,
            }
            response = self.client.post("/rest/gpx/", post_data, format='multipart', follow=True)
        self.assertEquals(response.status_code, 201)
        trip = models.Trip.objects.get(date=datetime.date(year=2010, month=11, day=17))
        self.assertEquals(trip.direction, 'trip_to')
        self.assertEquals(trip.distance, 13.32)

    def test_gpx_unknown_campaign(self):
        self.client = APIClient(HTTP_HOST="testing-campaign-unknown.testserver", HTTP_REFERER="test-referer")
        self.client.force_login(User.objects.get(pk=1128), settings.AUTHENTICATION_BACKENDS[0])
        address = reverse("gpxfile-list")
        with open('dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                'trip_date': "2010-11-19",
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
            trip_date=datetime.date(2010, 11, 19),
            direction="trip_to",
            user_attendance=UserAttendance.objects.get(pk=1115),
        )
        with open('dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                'trip_date': "2010-11-19",
                'direction': 'trip_to',
                'sourceApplication': 'test_app',
                'file': gpxfile,
            }
            response = self.client.post(reverse("gpxfile-list"), post_data)
            self.assertJSONEqual(
                response.content.decode(),
                {"detail": "GPX for this day and trip already uploaded"},
            )
            self.assertEqual(response.status_code, 409)

    def test_gpx_put(self):
        trip = mommy.make(
            'Trip',
            date=datetime.date(2010, 11, 19),
            direction="trip_to",
            user_attendance=UserAttendance.objects.get(pk=1115),
        )
        with open('dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                "file": gpxfile,
                'sourceApplication': 'test_app',
            }
            address = reverse("gpxfile-detail", kwargs={'pk': trip.id})
            response = self.client.put(address, post_data)
        self.assertEqual(response.status_code, 200)
        trip.refresh_from_db()
        self.assertEqual(trip.distance, 13.32)

    def test_gpx_inactive(self):
        with open('dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                'trip_date': "2010-11-10",
                'direction': 'trip_to',
                'sourceApplication': 'test_app',
                'file': gpxfile,
            }
            response = self.client.post(reverse("gpxfile-list"), post_data)
            self.assertJSONEqual(
                response.content.decode(),
                {"detail": "Trip for this day cannot be created/updated. This day is not active for edition"},
            )
            self.assertEqual(response.status_code, 410)


@override_settings(
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class TokenAuthenticationTests(TestCase):

    def setUp(self):
        self.user_attendance = UserAttendanceRecipe.make()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.example.com",
            HTTP_REFERER="test-referer",
            HTTP_AUTHORIZATION="Token %s" % self.user_attendance.userprofile.user.auth_token,
        )

    def test_track_post(self):
        response = self.client.post(
            reverse("gpxfile-list"),
            {
                'trip_date': "2010-11-20",
                'direction': 'trip_to',
                'sourceApplication': 'test_app',
                "track": '{"type": "MultiLineString", "coordinates": [[[14.0, 50.0], [14.0, 51.0]]]}',
            },
        )
        self.assertEquals(response.status_code, 201)
        trip = models.Trip.objects.get(date=datetime.date(2010, 11, 20))
        self.assertEquals(trip.distance, 111.24)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "id": trip.id,
                "trip_date": "2010-11-20",
                "direction": "trip_to",
                "file": None,
                "commuteMode": "bicycle",
                "durationSeconds": None,
                "distanceMeters": 111240,
                "sourceApplication": 'test_app',
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
