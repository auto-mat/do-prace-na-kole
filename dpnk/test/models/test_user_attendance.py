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
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings

from dpnk import models
from dpnk import util

from model_mommy import mommy

from ..mommy_recipes import PriceLevelRecipe, UserAttendancePaidRecipe


class TestFrequencyPercentage(TestCase):
    def setUp(self):
        self.user_attendance = mommy.make('dpnk.UserAttendance')

    def test_without_day(self):
        """
        Test that get_frequency_percentage function works properly
        """
        frequency = self.user_attendance.get_frequency_percentage()
        self.assertEqual(frequency, 0)

    def test_with_day(self):
        """
        Test that get_frequency_percentage function works properly with day set
        """
        frequency = self.user_attendance.get_frequency_percentage(day=datetime.date(year=2017, month=12, day=12))
        self.assertEqual(frequency, 0)


@override_settings(
    FAKE_DATE=datetime.date(year=2017, month=1, day=2),
)
class TestEnteredCompetitionReason(TestCase):
    def setUp(self):
        tshirt_size = mommy.make(
            't_shirt_delivery.TShirtSize',
            name='XXXL',
            campaign__track_required=False,
        )
        self.campaign = tshirt_size.campaign
        self.campaign.has_any_tshirt = True
        self.user_attendance = mommy.make(
            'dpnk.UserAttendance',
            campaign=self.campaign,
            team__campaign=self.campaign,
            userprofile__sex='male',
            personal_data_opt_in=True,
            userprofile__user__first_name='foo',
            userprofile__user__last_name='user',
            userprofile__user__email='foo@user',
            t_shirt_size=tshirt_size,
            approved_for_team='approved',
        )

    def test_profile_uncomplete(self):
        """
        Test that entered_competition_reason function works properly for uncomplete profile
        """
        self.user_attendance.personal_data_opt_in = False
        reason = self.user_attendance.entered_competition_reason()
        self.assertEqual(reason, 'profile_uncomplete')

    def test_team_uncomplete(self):
        """
        Test that entered_competition_reason function works properly for team_uncomplete
        """
        self.user_attendance.team = None
        reason = self.user_attendance.entered_competition_reason()
        self.assertEqual(reason, 'team_uncomplete')

    def test_team_waiting(self):
        """
        Test that entered_competition_reason function works properly for team_waiting
        """
        self.user_attendance.t_shirt_size = None
        self.user_attendance.approved_for_team = 'unknown'
        reason = self.user_attendance.entered_competition_reason()
        self.assertEqual(reason, 'team_waiting')

    def test_tshirt_uncomplete(self):
        """
        Test that entered_competition_reason function works properly for tshirt_uncomplete
        """
        self.user_attendance.t_shirt_size = None
        reason = self.user_attendance.entered_competition_reason()
        self.assertEqual(reason, 'tshirt_uncomplete')

    def test_payment_waiting(self):
        """
        Test that entered_competition_reason function works properly for payment_waiting
        """
        mommy.make(
            'price_level.PriceLevel',
            takes_effect_on=datetime.date(year=2017, month=1, day=1),
            pricable=self.campaign,
        )
        self.user_attendance.payment_status = 'waiting'
        reason = self.user_attendance.entered_competition_reason()
        self.assertEqual(reason, 'payment_waiting')

    def test_payment_uncomplete(self):
        """
        Test that entered_competition_reason function works properly for payment_uncomplete
        """
        mommy.make(
            'price_level.PriceLevel',
            takes_effect_on=datetime.date(year=2017, month=1, day=1),
            pricable=self.campaign,
        )
        self.user_attendance.payment_status = 'none'
        reason = self.user_attendance.entered_competition_reason()
        self.assertEqual(reason, 'payment_uncomplete')

    def test_track_uncomplete(self):
        """
        Test that entered_competition_reason function works properly for track_required
        """
        self.campaign.track_required = True
        reason = self.user_attendance.entered_competition_reason()
        self.assertEqual(reason, 'track_uncomplete')

    def test_true(self):
        """
        Test that entered_competition_reason function works properly for True result
        """
        reason = self.user_attendance.entered_competition_reason()
        self.assertEqual(reason, True)


@override_settings(
    FAKE_DATE=datetime.date(year=2017, month=1, day=2),
)
class TestAdmissionFee(TestCase):
    def setUp(self):
        phase = mommy.make(
            'dpnk.Phase',
            phase_type="competition",
            date_from=datetime.date(year=2017, month=11, day=1),
            date_to=datetime.date(year=2017, month=12, day=12),
        )
        self.campaign = phase.campaign
        phase = mommy.make(
            'price_level.PriceLevel',
            price=100,
            category='basic',
            takes_effect_on=datetime.date(year=2017, month=1, day=1),
            pricable=self.campaign,
        )
        phase = mommy.make(
            'price_level.PriceLevel',
            price=200,
            category='company',
            takes_effect_on=datetime.date(year=2017, month=1, day=1),
            pricable=self.campaign,
        )
        phase = mommy.make(
            'price_level.PriceLevel',
            price=150,
            category='basic',
            takes_effect_on=datetime.date(year=2017, month=2, day=1),
            pricable=self.campaign,
        )
        phase = mommy.make(
            'price_level.PriceLevel',
            price=250,
            category='company',
            takes_effect_on=datetime.date(year=2017, month=2, day=1),
            pricable=self.campaign,
        )
        self.user_attendance = mommy.make(
            'dpnk.UserAttendance',
            track="MULTILINESTRING((0 0,-1 1))",
            campaign=self.campaign,
            distance=123,
            pk=1115,
        )

    def test_company_admission_fee(self):
        self.assertEquals(self.user_attendance.company_admission_fee(), 200)

    @override_settings(
        FAKE_DATE=datetime.date(year=2017, month=2, day=1),
    )
    def test_company_admission_fee_second(self):
        self.assertEquals(self.user_attendance.company_admission_fee(), 250)

    def test_admission_fee(self):
        self.assertEquals(self.user_attendance.admission_fee(), 100)

    @override_settings(
        FAKE_DATE=datetime.date(year=2017, month=2, day=1),
    )
    def test_admission_fee_second(self):
        self.assertEquals(self.user_attendance.admission_fee(), 150)


class TestGetDistance(TestCase):
    def setUp(self):
        self.campaign = mommy.make('dpnk.Campaign')
        mommy.make(
            'dpnk.UserAttendance',
            track="MULTILINESTRING((0 0,-1 1))",
            campaign=self.campaign,
            distance=123,
            pk=1115,
        )

    def test_no_track(self):
        user_attendance = mommy.make(
            'dpnk.UserAttendance',
            campaign=self.campaign,
            distance=123,
        )
        self.assertEquals(user_attendance.get_distance(), 123)

    def test_user_attendance_get_distance(self):
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        self.assertEquals(user_attendance.get_distance(), 156.9)

    def test_user_attendance_get_distance_no_length(self):
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        self.assertEquals(user_attendance.get_distance(), 156.9)

    @patch('dpnk.models.user_attendance.logger')
    def test_user_attendance_get_distance_fail(self, mock_logger):
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        user_attendance.track = "MULTILINESTRING((0 0, 0 0))"
        user_attendance.save()
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        self.assertEqual(user_attendance.get_distance(), 0)


class TestIsLibero(TransactionTestCase):
    # This is here, because creating Payment messes up with indexes and other subsequent tests will fail.
    reset_sequences = True

    def setUp(self):
        PriceLevelRecipe.make()
        self.user_attendance = UserAttendancePaidRecipe.make(approved_for_team='approved')
        util.rebuild_denorm_models([self.user_attendance])
        util.rebuild_denorm_models([self.user_attendance.team])
        self.user_attendance.refresh_from_db()
        self.user_attendance.team.refresh_from_db()

    def test_true(self):
        self.user_attendance.campaign.max_team_members = 2
        self.assertTrue(self.user_attendance.is_libero())

    def test_false(self):
        self.user_attendance.campaign.max_team_members = 1
        self.assertFalse(self.user_attendance.is_libero())


class TestClean(TestCase):
    def setUp(self):
        self.campaign = mommy.make(
            'dpnk.campaign',
            name="Foo campaign",
            max_team_members=1,
        )

    def test_clean_team_none(self):
        user_attendance = mommy.make(
            'dpnk.UserAttendance',
            campaign=self.campaign,
            team=None,
        )
        user_attendance.clean()

    def test_clean_team(self):
        user_attendance = mommy.make(
            'dpnk.UserAttendance',
            campaign=self.campaign,
            team__name='Foo team',
            team__campaign=self.campaign,
        )
        user_attendance.clean()

    def test_too_much_team_members(self):
        team = mommy.make('Team', campaign=self.campaign)
        mommy.make(
            'dpnk.UserAttendance',
            campaign=self.campaign,
            team=team,
            approved_for_team='approved',
        )
        user_attendance = mommy.make(
            'dpnk.UserAttendance',
            campaign=self.campaign,
            team=team,
            approved_for_team='undecided',
        )
        with self.assertRaisesRegex(ValidationError, r"{'team': \['Tento tým již má plný počet členů'\]}"):
            user_attendance.clean()

    def test_campaign_mismatch(self):
        user_attendance = mommy.make(
            'dpnk.UserAttendance',
            campaign=mommy.make("Campaign", name="Bar campaign"),
            team=mommy.make('Team', campaign=self.campaign),
        )
        with self.assertRaisesRegex(
            ValidationError,
            r"'campaign': \['Zvolená kampaň \(Bar campaign\) musí být shodná s kampaní týmu \(Foo campaign\)'\]",
        ):
            user_attendance.clean()

    @patch('dpnk.models.user_attendance.logger')
    def test_campaign_mismatch_logger(self, mock_logger):
        team = mommy.make('Team', campaign=self.campaign)
        user_attendance = mommy.make(
            'dpnk.UserAttendance',
            campaign=self.campaign,
            team=team,
        )
        user_attendance.team = mommy.make('Team', campaign__name="Bar campaign")
        user_attendance.save()
        mock_logger.error.assert_called_with(
            "UserAttendance campaign doesn't match team campaign",
            extra={
                'user_attendance': user_attendance,
                'campaign': user_attendance.campaign,
                'new_team': user_attendance.team,
                'team_campaign': user_attendance.team.campaign,
            },
        )
