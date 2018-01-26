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
from django.contrib.gis.db.models.functions import Length
from django.http import Http404
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import ugettext_lazy as _

from .models import Campaign, UserAttendance


def get_or_create_userattendance(request, campaign_slug):
    if request.user and request.user.is_authenticated:
        try:
            return UserAttendance.objects.select_related(
                'campaign',
                'team__subsidiary__city',
                't_shirt_size',
                'userprofile__user',
                'representative_payment',
                'related_company_admin',
            ).annotate(
                length=Length('track'),
            ).get(
                userprofile__user=request.user,
                campaign__slug=campaign_slug,
            )
        except UserAttendance.DoesNotExist:
            if hasattr(request.user, 'userprofile') and request.campaign:
                return UserAttendance.objects.create(
                    userprofile=request.user.userprofile,
                    campaign=request.campaign,
                    approved_for_team='undecided',
                )


class UserAttendanceMiddleware(MiddlewareMixin):
    def process_request(self, request):
        campaign_slug = request.subdomain

        try:
            request.campaign = Campaign.objects.get(slug=campaign_slug)
        except Campaign.DoesNotExist:
            if '/admin/' not in request.path:  # We want to make admin accessible to be able to set campaigns.
                raise Http404(_("Kampaň s identifikátorem %s neexistuje. Zadejte prosím správnou adresu.") % campaign_slug)
            else:
                request.campaign = None

        request.user_attendance = get_or_create_userattendance(request, campaign_slug)
