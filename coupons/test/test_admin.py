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

from django.test import Client
from django.test.utils import override_settings

from django_admin_smoke_tests import tests as smoke_tests

from model_mommy import mommy

import settings


@override_settings(
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class AdminSmokeTests(smoke_tests.AdminSiteSmokeTest):
    fixtures = []
    exclude_apps = ['djcelery', 'dpnk', 't_shirt_delivery']

    def setUp(self):
        super().setUp()
        user = mommy.make(
            'auth.User',
            user__username='test',
            user__is_superuser=True,
        )
        mommy.make(
            "coupons.DiscountCoupon",
            coupon_type__prefix="AA",
            discount=100,
            token="AAAAAA",
            pk=1,
        )
        self.client = Client(HTTP_HOST="testing-campaign.example.com")
        self.client.force_login(user, settings.AUTHENTICATION_BACKENDS[0])

    def get_request(self, params={}):
        request = super().get_request(params)
        request.subdomain = "testing-campaign"
        return request

    def post_request(self, params={}):
        request = super().get_request(params)
        request.subdomain = "testing-campaign"
        return request
