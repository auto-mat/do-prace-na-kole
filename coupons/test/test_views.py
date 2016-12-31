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

from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from django.test.utils import override_settings

from dpnk.test.util import print_response  # noqa

from model_mommy import mommy

import settings


@override_settings(
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class DiscountCouponViewTests(TestCase):
    def setUp(self):
        super().setUp()
        payment_phase = mommy.make(
            "dpnk.Phase",
            phase_type="payment",
            campaign__slug="testing-campaign",
            campaign__late_admission_fee=120,
        )
        self.campaign = payment_phase.campaign
        mommy.make(
            "dpnk.Phase",
            phase_type="competition",
            campaign=self.campaign,
            date_from=datetime.date(year=2010, month=1, day=1),
            date_to=datetime.date(year=2019, month=12, day=12),
        )
        userattendance = mommy.make(
            'dpnk.UserAttendance',
            campaign=self.campaign,
            team__campaign=self.campaign,
            team__name="test team",
            t_shirt_size__name="XXXL",
            userprofile__user__username='test',
        )
        self.client = Client(HTTP_HOST="testing-campaign.example.com")
        self.client.force_login(
            userattendance.userprofile.user,
            settings.AUTHENTICATION_BACKENDS[0],
        )

    def test_discount_coupon_view_nonexistent(self):
        post_data = {
            'code': 'as-asdfsd',
            'next': 'Next',
        }
        response = self.client.post(reverse('discount_coupon'), post_data)
        self.assertContains(response, "<li>Tento slevový kupón neexistuje, nebo již byl použit</li>", html=True)

    def test_discount_coupon_view_found(self):
        mommy.make(
            "coupons.DiscountCoupon",
            coupon_type__prefix="AA",
            coupon_type__valid_until=datetime.date(year=2017, month=12, day=12),
            coupon_type__campaign=self.campaign,
            discount=100,
            token="AAAAAA",
            pk=1,
        )
        post_data = {
            'code': 'Aa-aaaAaa',
            'next': 'Next',
        }
        response = self.client.post(reverse('discount_coupon'), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('profil'))
        response = self.client.post(reverse('discount_coupon'), post_data)
        self.assertContains(response, "<li>Tento slevový kupón již byl použit</li>", html=True)

    def test_discount_coupon_view_found_discount(self):
        mommy.make(
            "coupons.DiscountCoupon",
            coupon_type__prefix="AA",
            coupon_type__valid_until=datetime.date(year=2017, month=12, day=12),
            coupon_type__campaign=self.campaign,
            discount=50,
            token="AAAAAB",
            pk=2,
        )
        post_data = {
            'code': 'Aa-aaaAab',
            'next': 'Next',
        }
        response = self.client.post(reverse('discount_coupon'), post_data, follow=True)
        self.assertContains(response, '<span id="payment_amount">60,0 Kč</span>', html=True)
        self.assertRedirects(response, reverse('typ_platby'))
