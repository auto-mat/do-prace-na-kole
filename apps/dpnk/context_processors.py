# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2015 o.s. Auto*Mat
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
from django.conf import settings  # import the settings file
from .models import UserAttendance


def site(request):
    return {'SITE_URL': settings.SITE_URL}


def user_attendance(request):
    if request.user and request.user.is_authenticated() and hasattr(request.user, 'userprofile'):
        userprofile = request.user.userprofile
        campaign_slug = request.subdomain
        try:
            user_attendance = userprofile.userattendance_set.select_related('campaign', 'team', 't_shirt_size').get(campaign__slug=campaign_slug)
        except UserAttendance.DoesNotExist:
            user_attendance = None
        return {'user_attendance': user_attendance}
    else:
        return {'user_attendance': None}
