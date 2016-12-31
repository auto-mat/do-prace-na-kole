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
import sys

from django.test import TestCase
from django.test.utils import override_settings

from dpnk import apps, models


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class AppsTests(TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users']

    def test_apps_ready(self):
        module = sys.modules['dpnk']
        dpnk_config = apps.DPNKConfig('dpnk', module)
        dpnk_config.ready()
        self.assertEqual(
            str(getattr(models.Team, "team_in_campaign_testing-campaign").__class__),
            "<class 'dpnk.apps.DPNKConfig.ready.<locals>.get_team_in_campaign_manager.<locals>.TeamInCampaignManager'>",
        )
