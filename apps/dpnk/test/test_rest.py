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

from django.conf import settings
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

from .mommy_recipes import UserAttendanceRecipe

import photologue
from django.core.files import File
import io
import json
import re
import os
from django.core.files.uploadedfile import SimpleUploadedFile


@freeze_time("2016-01-14")
@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class GPXTests(TestCase):
    fixtures = ["dump"]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        # util.rebuild_denorm_models(Team.objects.filter(pk=1))
        # util.rebuild_denorm_models(UserAttendance.objects.filter(pk=1115))

    def test_dpnk_rest_gpx_gz_no_login(self):
        post_data = {
            "trip_date": "2010-11-01",
            "sourceApplication": "test_app",
            "direction": "trip_to",
        }
        self.client.logout()
        response = self.client.post(
            "/rest/gpx/", post_data, format="multipart", follow=True
        )
        self.assertJSONEqual(
            response.content.decode(), {"detail": "Nebyly zadány přihlašovací údaje."}
        )
        self.assertEqual(response.status_code, 401)

    def test_dpnk_rest_gpx_gz_parse_error(self):
        with open("apps/dpnk/test_files/DSC00002.JPG", "rb") as gpxfile:
            post_data = {
                "trip_date": "2010-11-15",
                "direction": "trip_to",
                "sourceApplication": "test_app",
                "file": gpxfile,
            }
            response = self.client.post(
                "/rest/gpx/", post_data, format="multipart", follow=True
            )
            self.assertJSONEqual(
                response.content.decode(), {"file": "Can't parse GPX file"}
            )
            self.assertEqual(response.status_code, 400)

    def test_gpx_get1(self):
        address = reverse("gpxfile-detail", kwargs={"pk": 1})
        response = self.client.get(address)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "id": 1,
                "track": {
                    "coordinates": [[[15.567627, 50.680797], [14.710693, 50.212064]]],
                    "type": "MultiLineString",
                },
                "trip_date": "2024-08-04",
                "direction": "trip_to",
                "file": None,
                "commuteMode": "bicycle",
                "durationSeconds": None,
                "distanceMeters": 80150,
                "sourceApplication": None,
                "sourceId": None,
                "description": "",
            },
        )

    def test_gpx_post(self):
        address = reverse("gpxfile-list")
        with open("apps/dpnk/test_files/modranska-rokle.gpx", "rb") as gpxfile:
            post_data = {
                "trip_date": "2010-11-19",
                "direction": "trip_to",
                "sourceApplication": "test_app",
                "file": gpxfile,
            }
            response = self.client.post(address, post_data)
            self.assertEqual(response.status_code, 201)
            trip = models.Trip.objects.get(date=datetime.date(2010, 11, 19))
            self.assertJSONEqual(
                response.content.decode(),
                {
                    "id": trip.id,
                    "distanceMeters": 13320,
                    "durationSeconds": None,
                    "sourceApplication": "test_app",
                    "trip_date": "2010-11-19",
                    "sourceId": None,
                    "direction": "trip_to",
                    "commuteMode": "bicycle",
                    "description": "",
                    "file": "http://testing-campaign.testserver%s%s"
                    % (
                        settings.MEDIA_URL,
                        trip.gpx_file.name,
                    ),
                },
            )
            self.assertEqual(trip.direction, "trip_to")

    def test_dpnk_rest_gpx_gz(self):
        with open("apps/dpnk/test_files/modranska-rokle.gpx.gz", "rb") as gpxfile:
            post_data = {
                "trip_date": "2010-11-17",
                "direction": "trip_to",
                "sourceApplication": "test_app",
                "file": gpxfile,
            }
            response = self.client.post(
                "/rest/gpx/", post_data, format="multipart", follow=True
            )
        self.assertEqual(response.status_code, 201)
        trip = models.Trip.objects.get(date=datetime.date(year=2010, month=11, day=17))
        self.assertEqual(trip.direction, "trip_to")
        self.assertEqual(trip.distance, 13.32)

    def test_gpx_unknown_campaign(self):
        self.client = APIClient(
            HTTP_HOST="testing-campaign-unknown.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        address = reverse("gpxfile-list")
        with open("apps/dpnk/test_files/modranska-rokle.gpx", "rb") as gpxfile:
            post_data = {
                "trip_date": "2010-11-19",
                "direction": "trip_to",
                "file": gpxfile,
            }
            response = self.client.post(address, post_data)
            self.assertContains(
                response,
                "<title>Do Práce! ..stránka nenalezena - 404</title>",
                html=True,
                status_code=404,
            )

    def test_gpx_duplicate_gpx(self):
        """Test, that if trip exists, it gets modified"""
        trip = mommy.make(
            "Trip",
            date=datetime.date(2010, 11, 19),
            direction="trip_to",
            user_attendance=UserAttendance.objects.get(pk=1),
        )
        with open("apps/dpnk/test_files/modranska-rokle.gpx", "rb") as gpxfile:
            post_data = {
                "trip_date": "2010-11-19",
                "direction": "trip_to",
                "sourceApplication": "test_app",
                "file": gpxfile,
            }
            response = self.client.post(reverse("gpxfile-list"), post_data)
            trip = models.Trip.objects.get(date=datetime.date(2010, 11, 19))
            self.assertJSONEqual(
                response.content.decode(),
                {
                    "commuteMode": "bicycle",
                    "description": "",
                    "direction": "trip_to",
                    "distanceMeters": 13320,
                    "durationSeconds": None,
                    "file": "http://testing-campaign.testserver%s%s"
                    % (
                        settings.MEDIA_URL,
                        trip.gpx_file.name,
                    ),
                    "id": trip.id,
                    "sourceApplication": "test_app",
                    "sourceId": None,
                    "trip_date": "2010-11-19",
                },
            )
            self.assertEqual(response.status_code, 201)

    def test_gpx_put(self):
        trip = mommy.make(
            "Trip",
            date=datetime.date(2010, 11, 19),
            direction="trip_to",
            user_attendance=UserAttendance.objects.get(pk=1),
        )
        with open("apps/dpnk/test_files/modranska-rokle.gpx", "rb") as gpxfile:
            post_data = {
                "file": gpxfile,
                "sourceApplication": "test_app",
            }
            address = reverse("gpxfile-detail", kwargs={"pk": trip.id})
            response = self.client.put(address, post_data)
        self.assertEqual(response.status_code, 200)
        trip.refresh_from_db()
        self.assertEqual(trip.distance, 13.32)

    def test_gpx_inactive(self):
        with open("apps/dpnk/test_files/modranska-rokle.gpx", "rb") as gpxfile:
            post_data = {
                "trip_date": "2010-11-10",
                "direction": "trip_to",
                "sourceApplication": "test_app",
                "file": gpxfile,
            }
            response = self.client.post(reverse("gpxfile-list"), post_data)
            self.assertJSONEqual(
                response.content.decode(),
                {
                    "date": [
                        "Trip for this day cannot be created/updated. This day is not active for edition"
                    ]
                },
            )
            self.assertEqual(response.status_code, 400)


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class TokenAuthenticationTests(TestCase):
    fixtures = ["dump"]

    def setUp(self):
        self.user_attendance = UserAttendance.objects.get(pk=1)
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver",
            HTTP_REFERER="test-referer",
            HTTP_AUTHORIZATION="Token %s"
            % self.user_attendance.userprofile.user.auth_token,
        )

    def test_track_post(self):
        response = self.client.post(
            reverse("gpxfile-list"),
            {
                "trip_date": "2010-11-20",
                "direction": "trip_to",
                "sourceApplication": "test_app",
                "track": '{"type": "MultiLineString", "coordinates": [[[14.0, 50.0], [14.0, 51.0]]]}',
            },
        )
        self.assertEqual(response.status_code, 201)
        trip = models.Trip.objects.get(date=datetime.date(2010, 11, 20))
        self.assertEqual(trip.distance, 111.24)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "id": trip.id,
                "trip_date": "2010-11-20",
                "direction": "trip_to",
                "description": "",
                "file": None,
                "commuteMode": "bicycle",
                "durationSeconds": None,
                "distanceMeters": 111240,
                "sourceApplication": "test_app",
                "sourceId": None,
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class CommuteModeTest(TestCase):
    fixtures = ["dump"]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )

    def test_get(self):
        address = reverse("commute_mode-detail", kwargs={"pk": 4})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "id": 4,
                "slug": "no_work",
                "does_count": False,
                "eco": True,
                "distance_important": True,
                "duration_important": True,
                "minimum_distance": 0.0,
                "minimum_duration": 0,
                "description_en": None,
                "description_cs": None,
                "icon": None,
                "name_en": "No trip",
                "name_cs": "Žádná cesta",
                "points": 0,
            },
        )

    def test_no_login(self):
        self.client.logout()
        address = reverse("commute_mode-detail", kwargs={"pk": 4})
        response = self.client.get(address)

        self.assertEqual(response.status_code, 401)
        self.assertJSONEqual(
            response.content.decode(), {"detail": "Nebyly zadány přihlašovací údaje."}
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
    MEDIA_ROOT=os.path.join(os.path.dirname(__file__), "test_media"),
)
class PhotoTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )

    def test_post(self):
        with open("apps/dpnk/test_files/DSC00002.JPG", "rb") as photofile:
            post_data = {
                "caption": "masozravka",
                "image": photofile,
            }
            response = self.client.post(
                reverse("photo-list"), post_data, format="multipart", follow=True
            )

        self.assertEqual(response.status_code, 201)

        photo_count = photologue.models.Photo.objects.count()
        self.assertEqual(photo_count, 2)

        response_data = json.loads(response.content)
        photo_id = response_data["id"]

        photo = photologue.models.Photo.objects.get(id=photo_id)
        self.assertEqual(photo.caption, "masozravka")

    def test_get(self):
        with open("apps/dpnk/test_files/DSC00002.JPG", "rb") as photofile:
            photofile_content = photofile.read()
        uploaded_file = SimpleUploadedFile(
            name="masozravka.jpeg", content=photofile_content, content_type="image/jpeg"
        )
        data = {"file_field": uploaded_file}

        photo = photologue.models.Photo.objects.create(
            title="Test Photo",
            slug="test-photo",
            image=uploaded_file,
            caption="masozravka",
        )

        user_attendance = UserAttendance.objects.get(pk=1)
        user_attendance.team.subsidiary.company.get_gallery().photos.add(photo)
        address = reverse("photo-list")
        print(address)
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content.decode())
        print(results)
        self.assertEqual(results["count"], 1)
        self.assertEqual(results["results"][0]["id"], photo.id)
        self.assertEqual(results["results"][0]["caption"], photo.caption)


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class SubsidiaryTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("subsidiary-detail", kwargs={"pk": 1})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "id": 1,
                "address_street": "Jindřišská",
                "company": "http://testing-campaign.testserver/rest/company/1/",
                "teams": [
                    {
                        "name": "Tým1",
                        "id": 1,
                        "frequency": 0.000650618087182824,
                        "distance": 80.15,
                        "icon_url": "/media/upload/photologue/photos/frj337AJ0AD47aLGBgIFt8rsDSC00002.JPG",
                        "rest_url": "http://testing-campaign.testserver/rest/team/1/",
                        "eco_trip_count": 1,
                        "emissions": {
                            "co2": 10339.4,
                            "co": 58060.7,
                            "nox": 13601.5,
                            "n2o": 2003.8,
                            "voc": 6644.4,
                            "ch4": 617.2,
                            "so2": 392.7,
                            "solid": 2805.2,
                            "pb": 0.9,
                        },
                        "working_rides_base_count": 1537,
                    }
                ],
                "city": "http://testing-campaign.testserver/rest/city/1/",
                "eco_trip_count": 1,
                "frequency": 0.000650618087182824,
                "emissions": {
                    "co2": 10339.4,
                    "co": 58060.7,
                    "nox": 13601.5,
                    "n2o": 2003.8,
                    "voc": 6644.4,
                    "ch4": 617.2,
                    "so2": 392.7,
                    "solid": 2805.2,
                    "pb": 0.9,
                },
                "distance": 80.15,
                "icon": None,
                "icon_url": None,
                "gallery": "http://testing-campaign.testserver/rest/gallery/3/",
                "gallery_slug": "subsidiary-1-photos",
                "working_rides_base_count": 1537,
            },
            {
                "id": 2,
                "address_street": "Mečová",
                "company": "http://testing-campaign.testserver/rest/company/2/",
                "teams": [
                    {
                        "name": "Tým2",
                        "id": 2,
                        "frequency": 0.0,
                        "distance": 0.0,
                        "icon_url": None,
                        "rest_url": "http://test.lvh.me:8021/rest/team/2/",
                        "eco_trip_count": 0,
                        "emissions": {
                            "co2": 0.0,
                            "co": 0.0,
                            "nox": 0.0,
                            "n2o": 0.0,
                            "voc": 0.0,
                            "ch4": 0.0,
                            "so2": 0.0,
                            "solid": 0.0,
                            "pb": 0.0,
                        },
                        "working_rides_base_count": 1522,
                    }
                ],
                "city": "http://testing-campaign.testserver/rest/city/2/",
                "eco_trip_count": 0,
                "frequency": 0.0,
                "emissions": {
                    "co2": 0.0,
                    "co": 0.0,
                    "nox": 0.0,
                    "n2o": 0.0,
                    "voc": 0.0,
                    "ch4": 0.0,
                    "so2": 0.0,
                    "solid": 0.0,
                    "pb": 0.0,
                },
                "distance": 0.0,
                "icon": None,
                "icon_url": None,
                "gallery": None,
                "gallery_slug": "subsidiary-2-photos",
                "working_rides_base_count": 1522,
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class NotificationTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("notification-detail", kwargs={"pk": 1})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "id": 1,
                "level": "info",
                "unread": True,
                "deleted": False,
                "verb": "Pozvěte další členy do svého týmu",
                "description": None,
                "timestamp": "2024-08-04T00:29:50.729000",
                "data": "{'url': '/pozvanky/', 'icon': '/static/img/dpnk_logo.svg'}",
                "mark_as_read": "http://testing-campaign.testserver/inbox/notifications/mark-as-read/110910/",
                "mark_as_unread": "http://testing-campaign.testserver/inbox/notifications/mark-as-unread/110910/",
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class LoggedInUsersTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("logged_in_user_list-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content.decode())
        print(results)
        self.assertEqual(results["count"], 1)
        self.assertEqual(results["results"][0]["username"], "test")


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class CompetitionTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("competition-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content.decode())
        print(results)
        self.assertEqual(results["count"], 1)
        self.assertEqual(results["results"][0]["slug"], "vyzva1")
        self.assertEqual(results["results"][0]["competitor_type"], "single_user")
        self.assertEqual(results["results"][0]["competition_type"], "length")


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class MyTeamTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("my_team-detail", kwargs={"pk": 1})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "name": "Tým1",
                "icon": None,
                "id": 1,
                "subsidiary": "http://testing-campaign.testserver/rest/subsidiary/1/",
                "members": [
                    {
                        "id": 1,
                        "rest_url": "http://testing-campaign.testserver/rest/all_userattendance/1/",
                        "name": "test",
                        "frequency": 0.000650618087182824,
                        "distance": 80.15,
                        "avatar_url": "",
                        "eco_trip_count": 1,
                        "working_rides_base_count": 1537,
                        "emissions": {
                            "co2": 10339.4,
                            "co": 58060.7,
                            "nox": 13601.5,
                            "n2o": 2003.8,
                            "voc": 6644.4,
                            "ch4": 617.2,
                            "so2": 392.7,
                            "solid": 2805.2,
                            "pb": 0.9,
                        },
                        "is_me": True,
                    }
                ],
                "frequency": 0.000650618087182824,
                "distance": 80.15,
                "eco_trip_count": 1,
                "working_rides_base_count": 1537,
                "emissions": {
                    "co2": 10339.4,
                    "co": 58060.7,
                    "nox": 13601.5,
                    "n2o": 2003.8,
                    "voc": 6644.4,
                    "ch4": 617.2,
                    "so2": 392.7,
                    "solid": 2805.2,
                    "pb": 0.9,
                },
                "campaign": "http://testing-campaign.testserver/rest/campaign/20/",
                "icon_url": "/media/upload/photologue/photos/frj337AJ0AD47aLGBgIFt8rsDSC00002.JPG",
                "gallery": "http://testing-campaign.testserver/rest/gallery/2/",
                "gallery_slug": "team-1-photos",
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class MyCompanyTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("my-company-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 1,
                        "name": "Organizace1",
                        "subsidiaries": [
                            {
                                "id": 1,
                                "address_street": "Jindřišská",
                                "city": "http://testing-campaign.testserver/rest/city/1/",
                                "frequency": 0.000656598818122127,
                                "distance": 80.15,
                                "icon_url": None,
                                "rest_url": "http://testing-campaign.testserver/rest/subsidiary/1/",
                                "emissions": {
                                    "co2": 10339.4,
                                    "co": 58060.7,
                                    "nox": 13601.5,
                                    "n2o": 2003.8,
                                    "voc": 6644.4,
                                    "ch4": 617.2,
                                    "so2": 392.7,
                                    "solid": 2805.2,
                                    "pb": 0.9,
                                },
                                "eco_trip_count": 1,
                                "working_rides_base_count": 1523,
                            }
                        ],
                        "eco_trip_count": 1,
                        "frequency": 0.0003282994090610635,
                        "emissions": {
                            "co2": 10339.4,
                            "co": 58060.7,
                            "nox": 13601.5,
                            "n2o": 2003.8,
                            "voc": 6644.4,
                            "ch4": 617.2,
                            "so2": 392.7,
                            "solid": 2805.2,
                            "pb": 0.9,
                        },
                        "distance": 80.15,
                        "icon": None,
                        "icon_url": None,
                        "gallery": "http://testing-campaign.testserver/rest/gallery/1/",
                        "gallery_slug": "company-1-photos",
                        "working_rides_base_count": 1523,
                    }
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class ColleagueTripsTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("colleague_trip-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 1,
                        "trip_date": "2024-08-04",
                        "direction": "trip_to",
                        "commuteMode": "bicycle",
                        "durationSeconds": None,
                        "distanceMeters": 80150,
                        "sourceApplication": None,
                        "user": "test",
                        "user_attendance": 1,
                        "team": "Tým1",
                        "subsidiary": "Jindřišská 4, 110 00 Praha - Praha",
                        "has_track": True,
                    },
                    {
                        "id": 2,
                        "trip_date": "2024-08-06",
                        "direction": "trip_to",
                        "commuteMode": "by_foot",
                        "durationSeconds": None,
                        "distanceMeters": 57750,
                        "sourceApplication": None,
                        "user": "test3",
                        "user_attendance": 3,
                        "team": "Tým1",
                        "subsidiary": "Jindřišská 4, 110 00 Praha - Praha",
                        "has_track": True,
                    },
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class TripsTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("trip-list")
        response = self.client.get(
            address, {"start": "2024-08-01", "end": "2024-08-11"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "distanceMeters": 80150,
                        "durationSeconds": None,
                        "commuteMode": "bicycle",
                        "sourceApplication": None,
                        "trip_date": "2024-08-04",
                        "sourceId": None,
                        "file": None,
                        "description": "",
                        "id": 1,
                        "direction": "trip_to",
                        "track": {
                            "type": "MultiLineString",
                            "coordinates": [
                                [[15.567627, 50.680797], [14.710693, 50.212064]]
                            ],
                        },
                    }
                ],
            },
        )

    def test_get_no_trip(self):
        address = reverse("trip-list")
        response = self.client.get(
            address, {"start": "2024-09-01", "end": "2024-09-11"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"count": 0, "next": None, "previous": None, "results": []},
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class CityInCampaignTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("city_in_campaign-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 2,
                        "city__name": "Brno",
                        "city__location": {
                            "latitude": 49.197261,
                            "longitude": 16.627808,
                        },
                        "city__wp_url": "https://dopracenakole.cz/mesta/brno",
                        "competitor_count": 1,
                    },
                    {
                        "id": 1,
                        "city__name": "Praha",
                        "city__location": {
                            "latitude": 50.104139,
                            "longitude": 14.644775,
                        },
                        "city__wp_url": "https://dopracenakole.cz/mesta/praha",
                        "competitor_count": 2,
                    },
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class CityTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("city-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 2,
                        "name": "Brno",
                        "location": {
                            "type": "Point",
                            "coordinates": [16.627808, 49.197261],
                        },
                        "wp_url": "https://dopracenakole.cz/mesta/brno",
                        "competitor_count": 1,
                        "trip_stats": {
                            "distance__sum": 0.0,
                            "user_count": 0,
                            "count__sum": 0,
                            "count_bicycle": None,
                            "distance_bicycle": None,
                            "count_foot": None,
                            "distance_foot": None,
                        },
                        "emissions": {
                            "co2": 0.0,
                            "co": 0.0,
                            "nox": 0.0,
                            "n2o": 0.0,
                            "voc": 0.0,
                            "ch4": 0.0,
                            "so2": 0.0,
                            "solid": 0.0,
                            "pb": 0.0,
                        },
                        "subsidiaries": [
                            "http://testing-campaign.testserver/rest/subsidiary/2/"
                        ],
                        "eco_trip_count": 0,
                        "distance": 0.0,
                        "organizer": "",
                        "organizer_url": "",
                        "description": "Do práce na kole v tomto městě pořádá ",
                        "competitions": [],
                    },
                    {
                        "id": 1,
                        "name": "Praha",
                        "location": {
                            "type": "Point",
                            "coordinates": [14.644775, 50.104139],
                        },
                        "wp_url": "https://dopracenakole.cz/mesta/praha",
                        "competitor_count": 2,
                        "trip_stats": {
                            "distance__sum": 137.9,
                            "user_count": 2,
                            "count__sum": 2,
                            "count_bicycle": 1,
                            "distance_bicycle": 80.15,
                            "count_foot": 1,
                            "distance_foot": 57.75,
                        },
                        "emissions": {
                            "co2": 17789.1,
                            "co": 99894.8,
                            "nox": 23401.6,
                            "n2o": 3447.5,
                            "voc": 11431.9,
                            "ch4": 1061.8,
                            "so2": 675.7,
                            "solid": 4826.5,
                            "pb": 1.5,
                        },
                        "subsidiaries": [
                            "http://testing-campaign.testserver/rest/subsidiary/1/"
                        ],
                        "eco_trip_count": 2,
                        "distance": 137.9,
                        "organizer": "",
                        "organizer_url": "",
                        "description": "Do práce na kole v tomto městě pořádá ",
                        "competitions": [],
                    },
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class MyCityTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("my-city-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 1,
                        "name": "Praha",
                        "location": {
                            "type": "Point",
                            "coordinates": [14.644775, 50.104139],
                        },
                        "wp_url": "https://dopracenakole.cz/mesta/praha",
                        "competitor_count": 2,
                        "trip_stats": {
                            "distance__sum": 137.9,
                            "user_count": 2,
                            "count__sum": 2,
                            "count_bicycle": 1,
                            "distance_bicycle": 80.15,
                            "count_foot": 1,
                            "distance_foot": 57.75,
                        },
                        "emissions": {
                            "co2": 17789.1,
                            "co": 99894.8,
                            "nox": 23401.6,
                            "n2o": 3447.5,
                            "voc": 11431.9,
                            "ch4": 1061.8,
                            "so2": 675.7,
                            "solid": 4826.5,
                            "pb": 1.5,
                        },
                        "subsidiaries": [
                            "http://testing-campaign.testserver/rest/subsidiary/1/"
                        ],
                        "eco_trip_count": 2,
                        "distance": 137.9,
                        "organizer": "",
                        "organizer_url": "",
                        "description": "Do práce na kole v tomto městě pořádá ",
                        "competitions": [],
                    }
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2024, month=7, day=20),
)
class UserAttendanceTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = "/rest/userattendance/"  # reverse("userattendance-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        userattendance = models.UserProfile.objects.get(pk=1)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 1,
                        "name": "test",
                        "frequency": 0.000650618087182824,
                        "distance": 80.15,
                        "points": 0,
                        "points_display": "0 bodů",
                        "eco_trip_count": 1,
                        "team": "http://testing-campaign.testserver/rest/team/1/",
                        "emissions": {
                            "co2": 10339.4,
                            "co": 58060.7,
                            "nox": 13601.5,
                            "n2o": 2003.8,
                            "voc": 6644.4,
                            "ch4": 617.2,
                            "so2": 392.7,
                            "solid": 2805.2,
                            "pb": 0.9,
                        },
                        "avatar_url": "",
                        "working_rides_base_count": 1537,
                        "remaining_rides_count": 1058,
                        # "sesame_token": "AAAAAQim6U-BceUDjwwaHr9J",
                        "sesame_token": userattendance.get_sesame_token(),
                        "registration_complete": True,
                        "gallery": "http://testing-campaign.testserver/rest/gallery/4/",
                        "unread_notification_count": 2,
                        "is_coordinator": True,
                    }
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class ThisCampaignTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("this-campaign-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 20,
                        "slug": "testing-campaign",
                        "days_active": 8,
                        "year": "2021",
                        "campaign_type": "http://testing-campaign.testserver/rest/campaign_type/1/",
                        "phase_set": [
                            {
                                "phase_type": "registration",
                                "date_from": None,
                                "date_to": "2025-11-21",
                            },
                            {
                                "phase_type": "competition",
                                "date_from": "2021-09-01",
                                "date_to": "2025-12-31",
                            },
                            {
                                "phase_type": "results",
                                "date_from": "2021-06-01",
                                "date_to": None,
                            },
                            {
                                "phase_type": "admissions",
                                "date_from": None,
                                "date_to": None,
                            },
                            {
                                "phase_type": "payment",
                                "date_from": "2020-01-01",
                                "date_to": "2025-08-01",
                            },
                            {
                                "phase_type": "invoices",
                                "date_from": None,
                                "date_to": None,
                            },
                            {
                                "phase_type": "entry_enabled",
                                "date_from": "2021-07-01",
                                "date_to": "2025-06-03",
                            },
                        ],
                    }
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class CampaignTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("campaign-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "phase_set": [
                            {
                                "phase_type": "competition",
                                "date_from": None,
                                "date_to": None,
                            }
                        ],
                        "id": 21,
                        "slug": "test2",
                        "days_active": 7,
                        "year": "2024",
                        "campaign_type": "http://testing-campaign.testserver/rest/campaign_type/1/",
                    },
                    {
                        "phase_set": [
                            {
                                "phase_type": "registration",
                                "date_from": None,
                                "date_to": "2025-11-21",
                            },
                            {
                                "phase_type": "competition",
                                "date_from": "2021-09-01",
                                "date_to": "2025-12-31",
                            },
                            {
                                "phase_type": "results",
                                "date_from": "2021-06-01",
                                "date_to": None,
                            },
                            {
                                "phase_type": "admissions",
                                "date_from": None,
                                "date_to": None,
                            },
                            {
                                "phase_type": "payment",
                                "date_from": "2020-01-01",
                                "date_to": "2025-08-01",
                            },
                            {
                                "phase_type": "invoices",
                                "date_from": None,
                                "date_to": None,
                            },
                            {
                                "phase_type": "entry_enabled",
                                "date_from": "2021-07-01",
                                "date_to": "2025-06-03",
                            },
                        ],
                        "id": 20,
                        "slug": "testing-campaign",
                        "days_active": 8,
                        "year": "2021",
                        "campaign_type": "http://testing-campaign.testserver/rest/campaign_type/1/",
                    },
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class CampaignTypeTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("campaigntype-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 1,
                        "slug": "dpnk",
                        "name": "Do práce na kole",
                        "name_en": None,
                        "name_cs": "Do práce na kole",
                        "web": "https://www.dopracenakole.cz",
                        "campaigns": [
                            "http://testing-campaign.testserver/rest/campaign/21/",
                            "http://testing-campaign.testserver/rest/campaign/20/",
                        ],
                        "frontend_url": "https://dpnk-frontend.s3-eu-west-1.amazonaws.com/2021.10/",
                    }
                ],
            },
        )

    def test_post(self):
        post_data = {
            "slug": "dpnk_test",
            "name": "Do práce na kole 2",
            "name_en": "",
            "name_cs": "Do práce na kole 2",
            "web": "https://www.dopracenakole.cz",
        }
        response = self.client.post(
            "/rest/campaign_type/", post_data, format="multipart", follow=True
        )
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content.decode())
        campaign_type = models.CampaignType.objects.get(pk=response_data["id"])
        self.assertEqual(campaign_type.name, "Do práce na kole 2")
        self.assertEqual(campaign_type.slug, "dpnk_test")


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class CharitativeOrganizationTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("charitative_organization-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "name": "CharitativníOrganizace1",
                        "description": "<p>Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Cras <br>elementum. Nulla est. Integer tempor. Vestibulum fermentum tortor id mi.<br> Praesent vitae arcu tempor neque lacinia pretium. Etiam bibendum elit <br>eget erat. Morbi scelerisque luctus velit. Maecenas sollicitudin. <br>Maecenas aliquet accumsan leo. Vestibulum fermentum tortor id mi. <br>Praesent in mauris eu tortor porttitor accumsan. Nunc dapibus tortor vel<br> mi dapibus sollicitudin. In laoreet, magna id viverra tincidunt, sem <br>odio bibendum justo, vel imperdiet sapien wisi sed libero. Duis ante <br>orci, molestie vitae vehicula venenatis, tincidunt ac pede. In dapibus <br>augue non sapien. Etiam neque.</p>",
                        "ridden_distance": {
                            "distance__sum": 0.0,
                            "user_count": 0,
                            "count__sum": 0,
                            "count_bicycle": None,
                            "distance_bicycle": None,
                            "count_foot": None,
                            "distance_foot": None,
                        },
                        "image": None,
                        "icon": None,
                    }
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class CompetitionTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("competition-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 1,
                        "name": "Výzva1",
                        "slug": "vyzva1",
                        "competitor_type": "single_user",
                        "competition_type": "length",
                        "url": None,
                        "results": "http://testing-campaign.testserver/rest/result/vyzva1/",
                        "priority": 0,
                    }
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2024, month=8, day=10),
)
class CompetitionResultsTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("result-list", kwargs={"competition_slug": "vyzva1"})
        print(address)

        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 23,
                        "user_attendance": "test",
                        "team": None,
                        "company": None,
                        "competition": "http://testing-campaign.testserver/rest/competition/1/",
                        "result": "0.000000",
                        "place": 1,
                        "name": "test",
                        "icon_url": "",
                        "frequency": 0.0,
                        "divident": 0,
                        "divisor": 22,
                        "distance": 0.0,
                        "emissions": {
                            "co2": 0.0,
                            "co": 0.0,
                            "nox": 0.0,
                            "n2o": 0.0,
                            "voc": 0.0,
                            "ch4": 0.0,
                            "so2": 0.0,
                            "solid": 0.0,
                            "pb": 0.0,
                        },
                    }
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class MySubsidiaryTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("my-subsidiary-detail", kwargs={"pk": 1})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "id": 1,
                "address_street": "Jindřišská",
                "company": "http://testing-campaign.testserver/rest/company/1/",
                "teams": [
                    {
                        "name": "Tým1",
                        "id": 1,
                        "frequency": 0.000650618087182824,
                        "distance": 80.15,
                        "icon_url": "/media/upload/photologue/photos/frj337AJ0AD47aLGBgIFt8rsDSC00002.JPG",
                        "rest_url": "http://testing-campaign.testserver/rest/team/1/",
                        "eco_trip_count": 1,
                        "emissions": {
                            "co2": 10339.4,
                            "co": 58060.7,
                            "nox": 13601.5,
                            "n2o": 2003.8,
                            "voc": 6644.4,
                            "ch4": 617.2,
                            "so2": 392.7,
                            "solid": 2805.2,
                            "pb": 0.9,
                        },
                        "working_rides_base_count": 1537,
                    }
                ],
                "city": "http://testing-campaign.testserver/rest/city/1/",
                "eco_trip_count": 1,
                "frequency": 0.000650618087182824,
                "emissions": {
                    "co2": 10339.4,
                    "co": 58060.7,
                    "nox": 13601.5,
                    "n2o": 2003.8,
                    "voc": 6644.4,
                    "ch4": 617.2,
                    "so2": 392.7,
                    "solid": 2805.2,
                    "pb": 0.9,
                },
                "distance": 80.15,
                "icon": None,
                "icon_url": None,
                "gallery": "http://testing-campaign.testserver/rest/gallery/3/",
                "gallery_slug": "subsidiary-1-photos",
                "working_rides_base_count": 1537,
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class MyCompanyTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("my-company-detail", kwargs={"pk": 1})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "id": 1,
                "name": "Organizace1",
                "subsidiaries": [
                    {
                        "id": 1,
                        "address_street": "Jindřišská",
                        "city": "http://testing-campaign.testserver/rest/city/1/",
                        "frequency": 0.000650618087182824,
                        "distance": 80.15,
                        "icon_url": None,
                        "rest_url": "http://testing-campaign.testserver/rest/subsidiary/1/",
                        "emissions": {
                            "co2": 10339.4,
                            "co": 58060.7,
                            "nox": 13601.5,
                            "n2o": 2003.8,
                            "voc": 6644.4,
                            "ch4": 617.2,
                            "so2": 392.7,
                            "solid": 2805.2,
                            "pb": 0.9,
                        },
                        "eco_trip_count": 1,
                        "working_rides_base_count": 1537,
                    }
                ],
                "eco_trip_count": 1,
                "frequency": 0.000325309043591412,
                "emissions": {
                    "co2": 10339.4,
                    "co": 58060.7,
                    "nox": 13601.5,
                    "n2o": 2003.8,
                    "voc": 6644.4,
                    "ch4": 617.2,
                    "so2": 392.7,
                    "solid": 2805.2,
                    "pb": 0.9,
                },
                "distance": 80.15,
                "icon": None,
                "icon_url": None,
                "gallery": "http://testing-campaign.testserver/rest/gallery/1/",
                "gallery_slug": "company-1-photos",
                "working_rides_base_count": 1537,
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class NotificationTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("notification-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 2,
                        "level": "info",
                        "unread": True,
                        "deleted": False,
                        "verb": "Jsi sám v týmu. Pozvěte další členové.",
                        "description": None,
                        "timestamp": "2024-08-04T21:00:58.344000",
                        "data": "{'url': '/pozvanky/', 'icon': ''}",
                        "mark_as_read": "http://testing-campaign.testserver/inbox/notifications/mark-as-read/110911/",
                        "mark_as_unread": "http://testing-campaign.testserver/inbox/notifications/mark-as-unread/110911/",
                    },
                    {
                        "id": 1,
                        "level": "info",
                        "unread": True,
                        "deleted": False,
                        "verb": "Pozvěte další členy do svého týmu",
                        "description": None,
                        "timestamp": "2024-08-04T00:29:50.729000",
                        "data": "{'url': '/pozvanky/', 'icon': '/static/img/dpnk_logo.svg'}",
                        "mark_as_read": "http://testing-campaign.testserver/inbox/notifications/mark-as-read/110910/",
                        "mark_as_unread": "http://testing-campaign.testserver/inbox/notifications/mark-as-unread/110910/",
                    },
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class StravaAccountTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("strava_account-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "strava_username": "test",
                        "first_name": "Test",
                        "last_name": "Test",
                        "user_sync_count": 0,
                        "errors": "",
                    }
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class CoordinatedCityTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("coordinated-city-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 1,
                        "name": "Praha",
                        "location": {
                            "type": "Point",
                            "coordinates": [14.644775, 50.104139],
                        },
                        "wp_url": "https://dopracenakole.cz/mesta/praha",
                        "competitor_count": 2,
                        "trip_stats": {
                            "distance__sum": 137.9,
                            "user_count": 2,
                            "count__sum": 2,
                            "count_bicycle": 1,
                            "distance_bicycle": 80.15,
                            "count_foot": 1,
                            "distance_foot": 57.75,
                        },
                        "emissions": {
                            "co2": 17789.1,
                            "co": 99894.8,
                            "nox": 23401.6,
                            "n2o": 3447.5,
                            "voc": 11431.9,
                            "ch4": 1061.8,
                            "so2": 675.7,
                            "solid": 4826.5,
                            "pb": 1.5,
                        },
                        "subsidiaries": [
                            "http://testing-campaign.testserver/rest/subsidiary/1/"
                        ],
                        "eco_trip_count": 2,
                        "distance": 137.9,
                        "organizer": "",
                        "organizer_url": "",
                        "description": "Do práce na kole v tomto městě pořádá ",
                        "competitions": [],
                        "data_export_password": "",
                        "data_export_url": None,
                    }
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class LandingPageIconTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("landing_page_icon-list")
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "file": "http://testing-campaign.testserver/media/upload/kojot.jpg",
                        "role": "main",
                        "min_frequency": None,
                        "max_frequency": None,
                    }
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class GalleryTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None

    def test_get(self):
        address = reverse("gallery-detail", kwargs={"pk": 2})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "title": "team-1-photos",
                "slug": "team-1-photos",
                "description": "",
                "photos": ["http://testing-campaign.testserver/rest/photo/1/"],
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
