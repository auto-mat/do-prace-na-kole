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

from django.test.utils import override_settings

from django_admin_smoke_tests import tests as smoke_tests

from dpnk.test.util import DenormMixin


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class AdminSmokeTests(DenormMixin, smoke_tests.AdminSiteSmokeTest):
    fixtures = ['campaign', 'auth_user', 'users', 'coupons']
    exclude_apps = ['djcelery', 'dpnk']

    def setUp(self):
        super().setUp()

    def get_request(self, params={}):
        request = super().get_request(params)
        request.subdomain = "testing-campaign"
        return request

    def post_request(self, params={}):
        request = super().get_request(params)
        request.subdomain = "testing-campaign"
        return request
