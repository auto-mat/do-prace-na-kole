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

import json

client_id = "????"


def user_json(user_attendance):
    values = {
        "email": user_attendance.userprofile.user.email,
        "firstName": user_attendance.userprofile.user.first_name,
        "lastName": user_attendance.userprofile.user.last_name,
        "nickName": user_attendance.userprofile.nickname,
        "gender": {"male": "M", "female": "F", None: "O"}[user_attendance.userprofile.sex],
        "team": "56fa9f7788c53763287aaac0",
        "source": "API-%s" % client_id,
    }
    data = json.dumps(values)
    return data


def track_json(gpx_file):
    values = {
        "source": "API-%s" % client_id,
        "trackData_points": list(gpx_file.track[0]),
    }
    data = json.dumps(values)
    return data
