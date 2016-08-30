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

import denorm

from django.core.management import call_command
from django.test import TestCase

from dpnk import models, util


class Tests(TestCase):
    def setUp(self):
        call_command('denorm_init')
        util.rebuild_denorm_models(models.Team.objects.filter(pk=1))

    def tearDown(self):
        call_command('denorm_drop')

    fixtures = ['campaign', 'auth_user', 'users', 'transactions', 'invoices', 'company_competition', 'batches']

    def test_change_invoice_payments_status(self):
        payment = models.Payment.objects.get(pk=3)
        invoice = models.Invoice.objects.get(pk=1)
        payment.invoice = invoice
        payment.save()
        self.assertEquals(invoice.payment_set.get().status, 0)
        invoice.paid_date = datetime.date(year=2010, month=11, day=20)
        invoice.save()
        self.assertEquals(invoice.payment_set.get().status, 1007)
        invoice.delete()
        payment = models.Payment.objects.get(pk=3)
        self.assertEquals(payment.status, 1005)

    def test_competition_type_string(self):
        competition = models.Competition.objects.get(pk=3)
        self.assertEquals(str(competition.type_string()), " soutěž na pravidelnost týmů   ")

        competition = models.Competition.objects.get(pk=4)
        self.assertEquals(str(competition.type_string()), " dotazník jednotlivců   ")

        competition = models.Competition.objects.get(pk=5)
        self.assertEquals(str(competition.type_string()), " soutěž na vzdálenost jednotlivců  ve městě Testing city pro muže")

        competition = models.Competition.objects.get(pk=6)
        self.assertEquals(str(competition.type_string()), " soutěž na vzdálenost jednotlivců  ve městě Testing city ")

        competition = models.Competition.objects.get(pk=7)
        self.assertEquals(str(competition.type_string()), "vnitrofiremní soutěž na pravidelnost týmů organizace Testing company  ")

        competition = models.Competition.objects.get(pk=8)
        self.assertEquals(str(competition.type_string()), " soutěž na vzdálenost společností  ve městě Testing city ")

        competition = models.Competition.objects.get(pk=9)
        self.assertEquals(str(competition.type_string()), " soutěž na vzdálenost týmů  ve městě Testing city pro muže")


class TestMethods(TestCase):
    fixtures = ['campaign', 'auth_user', 'users', 'transactions', 'invoices', 'company_competition', 'batches']

    def test_too_much_members(self):
        campaign = models.Campaign(max_team_members=None)
        self.assertFalse(campaign.too_much_members(1000))

        campaign = models.Campaign(max_team_members=0)
        self.assertTrue(campaign.too_much_members(1))

        campaign = models.Campaign(max_team_members=5)
        self.assertFalse(campaign.too_much_members(5))

        campaign = models.Campaign(max_team_members=5)
        self.assertTrue(campaign.too_much_members(6))

    def test_campaign_phase_does_not_exist(self):
        campaign = models.Campaign()
        self.assertEquals(campaign.phase("unknown_phase"), None)

    def test_user_attendance_get_distance(self):
        user_attendance = models.UserAttendance.objects.length().get(pk=1115)
        self.assertEquals(user_attendance.get_distance(), 156.9)

    def test_user_attendance_get_distance_no_length(self):
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        self.assertEquals(user_attendance.get_distance(), 156.9)

    def test_user_attendance_get_distance_fail(self):
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        user_attendance.track = "MULTILINESTRING((0 0, 0 0))"
        user_attendance.save()
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        self.assertEqual(user_attendance.get_distance(), 0)

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

    def test_invoice_raises_sequence_number_overrun(self):
        campaign = models.Campaign.objects.create(
            invoice_sequence_number_first=0,
            invoice_sequence_number_last=0,
        )
        models.Phase.objects.create(
            type="competition",
            campaign=campaign,
            date_from="2016-1-1",
            date_to="2016-1-1",
        )
        company = models.Company.objects.create()
        with self.assertRaisesRegexp(Exception, "Došla číselná řada faktury"):
            models.Invoice.objects.create(
                campaign=campaign,
                company=company,
            )

    def test_package_transaction_raises_sequence_number_overrun(self):
        campaign = models.Campaign.objects.create(
            tracking_number_first=0,
            tracking_number_last=0,
        )
        user = models.User.objects.create(first_name="Test", last_name="Name")
        userprofile = models.UserProfile.objects.create(user=user)
        user_attendance = models.UserAttendance.objects.create(
            userprofile=userprofile,
            campaign=campaign,
        )
        models.Company.objects.create()
        models.PackageTransaction.objects.create(
            delivery_batch_id=1234,
            user_attendance=user_attendance,
        )
        with self.assertRaisesRegexp(Exception, "Došla číselná řada pro balíčkové transakce"):
            models.PackageTransaction.objects.create(
                delivery_batch_id=1234,
                user_attendance=user_attendance,
            )

    def test_answer_post_save_single_user(self):
        competition = models.Competition.objects.create(
            competitor_type="single_user",
            type="questionnaire",
            without_admission=True,
            campaign_id=1,
        )
        question = models.Question.objects.create(competition=competition)
        models.CompetitionResult.objects.filter().delete()
        models.UserAttendance.objects.get(pk=1115).save()
        denorm.flush()
        self.assertFalse(models.CompetitionResult.objects.exists())
        models.Answer.objects.create(question=question, user_attendance_id=1115)
        self.assertEquals(models.CompetitionResult.objects.get().result, 0.0)
        self.assertEquals(models.CompetitionResult.objects.get().user_attendance_id, 1115)

    def test_answer_post_save_company(self):
        campaign = models.Campaign.objects.get(pk=339)
        competition = models.Competition.objects.create(
            competitor_type="company",
            type="questionnaire",
            without_admission=True,
            campaign=campaign,
        )
        question = models.Question.objects.create(competition=competition)
        models.CompetitionResult.objects.filter().delete()
        models.UserAttendance.objects.get(pk=1115).save()
        denorm.flush()
        self.assertFalse(models.CompetitionResult.objects.exists())
        models.Answer.objects.create(question=question, user_attendance_id=1115)
        self.assertEquals(models.CompetitionResult.objects.get().result, 0.0)
        self.assertEquals(models.CompetitionResult.objects.get().company_id, 1)

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
        self.assertEquals(models.CompetitionResult.objects.get().result, None)
        self.assertEquals(models.CompetitionResult.objects.get().team_id, 1)
