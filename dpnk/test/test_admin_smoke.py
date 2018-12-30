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

from dpnk import models, util
from dpnk.test.util import DenormMixin
from dpnk.test.util import print_response  # noqa


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class AdminSmokeTests(DenormMixin, smoke_tests.AdminSiteSmokeTest):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'test_results_data', 'transactions', 'batches', 'invoices', 'trips']
    exclude_apps = ['djcelery', 'coupons', 'avatar']

    def setUp(self):
        super().setUp()
        util.rebuild_denorm_models(models.Team.objects.filter(pk__in=[4, 3, 1]))

    def get_request(self, params={}):
        request = super().get_request(params)
        request.subdomain = "testing-campaign"
        return request

    def post_request(self, params={}):
        request = super().get_request(params)
        request.subdomain = "testing-campaign"
        return request
