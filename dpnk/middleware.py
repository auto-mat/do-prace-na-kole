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
from .models import Campaign, UserAttendance


class UserAttendanceMiddleware:
    def process_request(self, request):
        campaign_slug = request.subdomain
        if request.user and request.user.is_authenticated():
            try:
                user_attendance_set = UserAttendance.objects.length()
                user_attendance_set = user_attendance_set.select_related(
                    'campaign',
                    'team__subsidiary__city',
                    't_shirt_size',
                    'userprofile__user',
                    'representative_payment',
                    'related_company_admin',
                )
                request.user_attendance = user_attendance_set.get(userprofile__user=request.user, campaign__slug=campaign_slug)
                request.campaign = request.user_attendance.campaign
            except UserAttendance.DoesNotExist:
                request.user_attendance = None
        else:
            request.user_attendance = None

        if not hasattr(request, 'campaign') and campaign_slug:
            try:
                request.campaign = Campaign.objects.get(slug=campaign_slug)
            except Campaign.DoesNotExist:
                request.campaign = None
        else:
            request.campaign = None
