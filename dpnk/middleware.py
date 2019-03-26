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
from django.contrib.sites.models import Site
from django.http import Http404
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import get_language
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

            # Change language, if not available in campaign
            available_language_codes = list(zip(*request.campaign.get_available_languages()))[0]
            if get_language() not in available_language_codes:
                new_language = available_language_codes[0]
                translation.activate(new_language)
                request.session[translation.LANGUAGE_SESSION_KEY] = new_language
        except Campaign.DoesNotExist:
            if '/admin/' not in request.path:  # We want to make admin accessible to be able to set campaigns.
                if campaign_slug is None:
                    from django.conf import settings
                    current_site = Site.objects.get(pk=int(settings.SITE_ID))
                    raise Http404(
                        """Could not read subdomain.
Ensure that you have DPNK_SITE_ID set correctly.

Current SITE_ID is %s. Which points to site %s.

For more info see https://django-subdomains.readthedocs.io/en/latest/ .
You need to create a site object in the admin in order to do this: ex http://localhost:8000/admin/sites/site/
Current sites are

%s

Note: after updating the sites list in the admin interface, server
restart is requried.
""" % (settings.SITE_ID, str(current_site), "\n\n".join(["domain: %s id: %s" % (site.domain, str(site.id)) for site in Site.objects.all()])),
                    )

                raise Http404(_("Kampaň s identifikátorem %s neexistuje. Zadejte prosím správnou adresu.") % campaign_slug)
            else:
                request.campaign = None

        request.user_attendance = get_or_create_userattendance(request, campaign_slug)
