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
import json

from django.conf import settings

import requests

from .models import GpxFile


class EccBadTrackStatusException(Exception):
    pass


class EccBadRegisterStatusException(Exception):
    pass


class EccBadLoginStatusException(Exception):
    pass


def user_data(user_attendance):
    value = {
        "email": user_attendance.userprofile.ecc_email,
        "password": user_attendance.userprofile.ecc_password,
        "firstName": user_attendance.userprofile.user.first_name,
        "lastName": user_attendance.userprofile.user.last_name,
        "nickName": user_attendance.userprofile.nickname,
        "gender": {
            "male": "M",
            "female": "F",
            "unknown": "O",
            None: "O",
        }[user_attendance.userprofile.sex],
        "team": "56fa9f7788c53763287aaac0",
        "source": "API-%s" % settings.ECC_PROVIDER_CODE,
    }
    return value


def user_register(user_attendance):
    url = "%s/user/register" % settings.ECC_URL_BASE
    data = user_data(user_attendance)
    response = requests.post(url, data=data)
    if not (response.status_code == 200 and response.json()['status'] == 'ok'):
        raise EccBadRegisterStatusException()


def login_post(user_attendance):
    url = "%s/user/login" % settings.ECC_URL_BASE
    data = {
        "email": user_attendance.userprofile.ecc_email,
        "password": user_attendance.userprofile.ecc_password,
    }
    return requests.post(url, data=data)


def login_or_register(user_attendance):
    response = login_post(user_attendance)
    if response.status_code == 403 and response.json()['error'] == "User is not authorized or not found with matching username or password":
        user_register(user_attendance)
        response = login_post(user_attendance)
    if not response.status_code == 200:
        raise EccBadLoginStatusException()
    return response.json()['token']


def track_json(gpx_file, token):

    points = []
    info_points = []

    if gpx_file.direction == 'trip_to':
        start_time = datetime.datetime.combine(gpx_file.trip_date, datetime.time(hour=10, minute=0))
        end_time = datetime.datetime.combine(gpx_file.trip_date, datetime.time(hour=10, minute=0))
    else:
        start_time = datetime.datetime.combine(gpx_file.trip_date, datetime.time(hour=18, minute=0))
        end_time = datetime.datetime.combine(gpx_file.trip_date, datetime.time(hour=18, minute=0))

    if gpx_file.track:
        for segment in gpx_file.track:
            points += list(segment)
            for i in range(0, len(segment)):
                info_points.append({
                    "time": start_time.timestamp(),
                    "altitude": "0",
                    "speed": "0",
                    "resumed": "1" if i == 0 else "0",
                })

    value = {
        "source": "API-%s" % settings.ECC_PROVIDER_CODE,
        "trackData_points": points,
        "trackData_info": info_points,
        "trackStart": start_time.timestamp(),
        "trackEnd": end_time.timestamp(),
        "trackDuration": "0",
        "trackDuration_hr": "0:0:0",
        "trackStart_hr": str(start_time),
        "trackEnd_hr": str(end_time),
        "token": token,
        "extrainfo": {
            "totaldistance": gpx_file.length(),
            "averagespeed": "0",
            "maxspeed": "0",
            "mapcenter": points[0] if points else "0",
            "start_year": gpx_file.trip_date.year,
            "start_month": gpx_file.trip_date.month,
            "start_day": gpx_file.trip_date.day,
        },
    }
    data = json.dumps(value)
    return data


def track_post(gpx_file, token=None, force=False):
    if not force and gpx_file.ecc_last_upload:  # TODO: reload the track if it changed since then
        return False

    if gpx_file.trip and gpx_file.trip.commute_mode != 'bicycle':
        return False

    if not token:
        token = login_or_register(gpx_file.user_attendance)
    data = track_json(gpx_file, token)
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    url = "%s/track/send" % settings.ECC_URL_BASE
    response = requests.post(url, data=data, headers=headers)
    if not (response.status_code == 200 and response.json()['status'] == 'ok'):
        raise EccBadTrackStatusException()
    gpx_file.ecc_last_upload = datetime.datetime.now()
    gpx_file.save()
    return True


def gpx_files_post(gpx_files, token=None):
    uploaded_tracks = 0
    skipped_tracks = 0
    for gpx_file in gpx_files:
        uploaded = track_post(gpx_file, token)
        if uploaded:
            uploaded_tracks += 1
        else:
            skipped_tracks += 1
    return uploaded_tracks, skipped_tracks


def user_attendance_post(user_attendance):
    gpx_files = GpxFile.objects.filter(user_attendance=user_attendance)
    if gpx_files:
        token = login_or_register(user_attendance)
        return gpx_files_post(gpx_files, token)
    return 0, 0
