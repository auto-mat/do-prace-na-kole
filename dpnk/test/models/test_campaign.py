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

from django.test import TestCase
from django.test.utils import override_settings

from dpnk import models
from dpnk.test.util import ClearCacheMixin

from model_mommy import mommy


class TestCampaignMethods(ClearCacheMixin, TestCase):
    def test_phase(self):
        """
        Test that phase caching works properly
        """
        campaign = models.Campaign.objects.create(name="Campaign", slug="campaign")
        phase = models.Phase.objects.create(campaign=campaign, phase_type="competition")
        self.assertEqual(campaign.phase("competition"), phase)

        campaign1 = models.Campaign.objects.create(name="Campaign 1", slug="campaign1")
        phase1 = models.Phase.objects.create(campaign=campaign1, phase_type="competition")
        self.assertEqual(campaign1.phase("competition"), phase1)

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=11, day=20),
    )
    def test_day_active(self):
        campaign = mommy.make("Campaign")
        self.assertTrue(campaign.day_active(datetime.date(2010, 11, 14)))
        self.assertTrue(campaign.day_active(datetime.date(2010, 11, 20)))
        self.assertFalse(campaign.day_active(datetime.date(2010, 11, 13)))
        self.assertFalse(campaign.day_active(datetime.date(2010, 11, 21)))

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=11, day=20),
    )
    def test_vacation_day_active(self):
        phase = mommy.make("Phase", phase_type="competition", date_to="2010-12-14")
        campaign = phase.campaign
        self.assertFalse(campaign.vacation_day_active(datetime.date(2010, 11, 14)))
        self.assertFalse(campaign.vacation_day_active(datetime.date(2010, 11, 20)))
        self.assertTrue(campaign.vacation_day_active(datetime.date(2010, 11, 25)))
        self.assertFalse(campaign.vacation_day_active(datetime.date(2010, 12, 17)))


class TestMethods(TestCase):
    def test_campaign_phase_does_not_exist(self):
        campaign = models.Campaign()
        with self.assertRaises(models.Phase.DoesNotExist):
            campaign.phase("unknown_phase")


class TestUserAttendancesForDelivery(TestCase):
    def test_no_admission(self):
        user_attendance = mommy.make_recipe(
            'dpnk.test.UserAttendanceRecipe',
            t_shirt_size__ship=True,
            team__name="Foo team",
            userprofile__user__first_name="Foo",
        )
        self.assertEqual(
            user_attendance.payment_status,
            'no_admission',
        )
        self.assertQuerysetEqual(
            user_attendance.campaign.user_attendances_for_delivery(),
            ['<UserAttendance: Foo>'],
        )

    def test_token_user(self):
        token = mommy.make(
            'DiscountCoupon',
            discount=100,
            coupon_type__name="Foo coupon type",
        )
        user_attendance = mommy.make_recipe(
            'dpnk.test.UserAttendanceRecipe',
            discount_coupon=token,
            t_shirt_size__ship=True,
            team__name="Foo team",
            userprofile__user__first_name="Foo",
        )
        mommy.make(
            "price_level.PriceLevel",
            takes_effect_on=datetime.date(year=2010, month=2, day=1),
            price=100,
            category='basic',
            pricable=user_attendance.campaign,
        )
        user_attendance.save()
        self.assertEqual(
            user_attendance.payment_status,
            'done',
        )
        self.assertQuerysetEqual(
            user_attendance.campaign.user_attendances_for_delivery(),
            ['<UserAttendance: Foo>'],
        )

    def test_none(self):
        user_attendance = mommy.make_recipe(
            'dpnk.test.UserAttendanceRecipe',
            t_shirt_size__ship=True,
            team__name="Foo team",
            userprofile__user__first_name="Foo",
        )
        mommy.make(
            "price_level.PriceLevel",
            takes_effect_on=datetime.date(year=2010, month=2, day=1),
            price=100,
            category='basic',
            pricable=user_attendance.campaign,
        )
        user_attendance.save()
        self.assertEqual(
            user_attendance.payment_status,
            'none',
        )
        self.assertQuerysetEqual(
            user_attendance.campaign.user_attendances_for_delivery(),
            [],
        )
