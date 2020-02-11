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
import denorm

from django.test import TestCase

from dpnk import models


class TestMethods(TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'company_competition', 'batches']

    def test_too_much_members(self):
        campaign = models.Campaign(max_team_members=None)
        self.assertFalse(campaign.too_much_members(1000))

        campaign = models.Campaign(max_team_members=0)
        self.assertTrue(campaign.too_much_members(1))

        campaign = models.Campaign(max_team_members=5)
        self.assertFalse(campaign.too_much_members(5))

        campaign = models.Campaign(max_team_members=5)
        self.assertTrue(campaign.too_much_members(6))

    def test_company_admin_name_for_trusted(self):
        user = models.User.objects.create(first_name="Test", last_name="Name")
        userprofile = models.UserProfile.objects.create(user=user)
        self.assertEqual(userprofile.name_for_trusted(), "Test Name")

    def test_company_admin_name_for_trusted_username(self):
        user = models.User.objects.create(username="test_name")
        userprofile = models.UserProfile.objects.create(user=user)
        self.assertEqual(userprofile.name_for_trusted(), "test_name")

    def test_company_admin_name_for_trusted_nickname_username(self):
        user = models.User.objects.create(username="test_name")
        userprofile = models.UserProfile.objects.create(user=user, nickname="Nick")
        self.assertEqual(userprofile.name_for_trusted(), "test_name (Nick)")

    def test_company_admin_name_for_trusted_nickname(self):
        user = models.User.objects.create(first_name="Test", last_name="Name")
        userprofile = models.UserProfile.objects.create(user=user, nickname="Nick")
        self.assertEqual(userprofile.name_for_trusted(), "Test Name (Nick)")

    def test_answer_post_save_single_user(self):
        competition = models.Competition.objects.create(
            competitor_type="single_user",
            competition_type="questionnaire",
            campaign_id=339,
        )
        question = models.Question.objects.create(competition=competition)
        models.CompetitionResult.objects.filter().delete()
        models.UserAttendance.objects.get(pk=1115).save()
        denorm.flush()
        self.assertFalse(models.CompetitionResult.objects.exists())
        models.Answer.objects.create(question=question, user_attendance_id=1115)
        self.assertEqual(models.CompetitionResult.objects.get().result, 0.0)
        self.assertEqual(models.CompetitionResult.objects.get().user_attendance_id, 1115)

    def test_answer_post_save_company(self):
        campaign = models.Campaign.objects.get(pk=339)
        competition = models.Competition.objects.create(
            competitor_type="company",
            competition_type="questionnaire",
            campaign=campaign,
        )
        question = models.Question.objects.create(competition=competition)
        models.CompetitionResult.objects.filter().delete()
        models.UserAttendance.objects.get(pk=1115).save()
        denorm.flush()
        self.assertFalse(models.CompetitionResult.objects.exists())
        models.Answer.objects.create(question=question, user_attendance_id=1115)
        self.assertEqual(models.CompetitionResult.objects.get().result, 0.0)
        self.assertEqual(models.CompetitionResult.objects.get().company_id, 1)

    def test_answer_post_save_team(self):
        campaign = models.Campaign.objects.create()
        competition = models.Competition.objects.create(
            competitor_type="team",
            campaign=campaign,
        )
        question = models.Question.objects.create(competition=competition)
        models.CompetitionResult.objects.filter().delete()
        self.assertFalse(models.CompetitionResult.objects.exists())
        models.Answer.objects.create(question=question, user_attendance_id=1115)
        self.assertEqual(models.CompetitionResult.objects.get().result, None)
        self.assertEqual(models.CompetitionResult.objects.get().team_id, 1)
