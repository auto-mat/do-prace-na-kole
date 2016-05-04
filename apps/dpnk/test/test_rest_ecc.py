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

from django.test import TestCase
from django.test.utils import override_settings
from dpnk import rest_ecc
from dpnk.models import UserAttendance, GpxFile
from freezegun import freeze_time
from unittest.mock import MagicMock, patch
import datetime


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
    ECC_PROVIDER_CODE="????",
    ECC_URL_BASE="http://localhost/services",
)
@freeze_time("2010-11-20 12:00")
class ECCTests(TestCase):
    fixtures = ['campaign', 'auth_user', 'users', 'transactions', 'batches', 'trips']

    @patch('requests.post')
    def test_ecc_user_attendance_post(self, post):
        response = MagicMock()
        response.status_code = 403
        response.json.return_value = {'error': "User is not authorized or not found with matching username or password"}

        response1 = MagicMock()
        response1.status_code = 200
        response1.json.return_value = {'status': 'ok', 'token': 'token'}
        post.side_effect = [response, response1, response1, response1, response1]
        rest_ecc.user_attendance_post(UserAttendance.objects.get(pk=1115))
        gpx_file = GpxFile.objects.get(pk=2)
        self.assertEquals(gpx_file.ecc_last_upload, datetime.datetime(year=2010, month=11, day=20, hour=12, minute=0))

    def test_track_post_not_changed(self):
        gpx_file = GpxFile.objects.get(pk=2)
        gpx_file.ecc_last_upload = datetime.datetime.now()
        gpx_file.save()
        return_val = rest_ecc.track_post(gpx_file)
        self.assertEqual(return_val, False)

    def test_ecc_user_data(self):
        user_attendance = UserAttendance.objects.get(pk=1115)
        data = rest_ecc.user_data(user_attendance)
        self.assertDictEqual(data, {
            'nickName': '',
            'gender': 'M',
            'firstName': 'Testing',
            'source': 'API-????',
            'lastName': 'User 1',
            'team': '56fa9f7788c53763287aaac0',
            'email': user_attendance.userprofile.ecc_email,
            'password': user_attendance.userprofile.ecc_password,
        })

    @override_settings(
        MEDIA_ROOT="apps/dpnk/test_files",
    )
    def test_ecc_track_json(self):
        modranska_rokle = GpxFile.objects.get(pk=2)
        modranska_rokle.clean()
        modranska_rokle.track = modranska_rokle.track_clean
        modranska_rokle.save()

        json = rest_ecc.track_json(GpxFile.objects.get(pk=1), "token")
        self.assertJSONEqual(json, {
            "trackEnd_hr": "2010-11-01 10:00:00",
            "trackEnd": 1288602000.0,
            "trackDuration": "0",
            "trackDuration_hr": "0:0:0",
            "extrainfo": {
                "start_year": 2010,
                "start_month": 11,
                "averagespeed": "0",
                "start_day": 1,
                "maxspeed": "0",
                "mapcenter": "0",
                "totaldistance": None
            },
            "trackStart": 1288602000.0,
            "trackData_points": None,
            "trackData_info": [],
            "source": "API-????",
            "token": "token",
            "trackStart_hr": "2010-11-01 10:00:00"
        })
