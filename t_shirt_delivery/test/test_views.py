# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2017 o.s. Auto*Mat
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

from unittest.mock import MagicMock, patch

from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from dpnk.test.mommy_recipes import UserAttendanceRecipe, testing_campaign
from dpnk.test.util import print_response  # noqa

from model_mommy import mommy

from price_level.models import PriceLevel

import settings

from t_shirt_delivery.models import TShirtSize


class ViewsTestsLogon(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.example.com", HTTP_REFERER="test-referer")
        self.t_shirt_size = mommy.make(
            "TShirtSize",
            id=1,
            campaign=testing_campaign,
        )
        mommy.make(
            "price_level.PriceLevel",
            takes_effect_on=datetime.date(year=2010, month=2, day=1),
            pricable=testing_campaign,
        )
        mommy.make(
            "Phase",
            phase_type="payment",
            campaign=testing_campaign,
        )
        self.user_attendance = UserAttendanceRecipe.make(
            approved_for_team="approved",
            team__subsidiary__city__cityincampaign__campaign=testing_campaign,
            userprofile__user__first_name="Testing",
            userprofile__user__last_name="User",
            userprofile__user__email="testing.user@email.com",
            userprofile__personal_data_opt_in=True,
            distance=5,
        )
        self.user_attendance.campaign.save()
        self.user_attendance.save()
        self.client.force_login(self.user_attendance.userprofile.user, settings.AUTHENTICATION_BACKENDS[0])

    def test_dpnk_t_shirt_size(self):
        post_data = {
            't_shirt_size': '1',
            'next': 'Next',
        }
        response = self.client.post(reverse('zmenit_triko'), post_data, follow=True)
        self.assertRedirects(response, reverse("typ_platby"))
        self.user_attendance.refresh_from_db()
        self.assertTrue(self.user_attendance.t_shirt_size.pk, 1)

    def test_dpnk_t_shirt_size_no_sizes(self):
        TShirtSize.objects.all().delete()
        self.user_attendance.campaign.save()
        response = self.client.get(reverse('zmenit_triko'))
        self.assertRedirects(response, reverse("typ_platby"), target_status_code=403)

    def test_dpnk_t_shirt_size_shipped(self):
        mommy.make("PackageTransaction", status=20002, t_shirt_size=self.t_shirt_size, user_attendance=self.user_attendance)
        response = self.client.get(reverse('zmenit_triko'))
        self.assertContains(response, "Vaše tričko již je na cestě k vám, už se na něj můžete těšit.", status_code=403)

    @patch('slumber.API')
    def test_dpnk_t_shirt_size_no_sizes_no_admission(self, slumber_mock):
        m = MagicMock()
        m.feed.get.return_value = []
        slumber_mock.return_value = m
        TShirtSize.objects.all().delete()
        PriceLevel.objects.all().delete()
        self.user_attendance.campaign.save()
        response = self.client.get(reverse('zmenit_triko'), follow=True)
        self.assertRedirects(response, reverse("profil"))

    def test_dpnk_t_shirt_size_no_team(self):
        self.user_attendance.team = None
        self.user_attendance.save()
        response = self.client.get(reverse('zmenit_triko'))
        self.assertContains(response, "Velikost trička nemůžete měnit, dokud nemáte zvolený tým.", status_code=403)

    def test_dpnk_t_shirt_size_get(self):
        response = self.client.get(reverse('zmenit_triko'))
        self.assertContains(
            response,
            '<label for="id_t_shirt_size" class="control-label  requiredField">'
            'Velikost trika'
            '<span class="asteriskField">*</span>'
            '</label>',
            html=True,
        )
