# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2013 o.s. Auto*Mat
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

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase

from dpnk import email
from dpnk.models import Campaign, City, Company, CompanyAdmin, Phase, Subsidiary, Team, UserAttendance, UserProfile


# Uncoment this to check to generate email files in /tmp/dpnk-test-messages
# from django.test.utils import override_settings
# @override_settings(
#     EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend',
#     EMAIL_FILE_PATH = '/tmp/dpnk-test-messages',
# )
class TestEmails(TestCase):
    def setUp(self):
        self.campaign = Campaign.objects.create(name="Testing campaign 1", slug="testing_campaign_1")
        self.phase = Phase.objects.create(
            date_from=datetime.date(year=2010, month=10, day=20),
            date_to=datetime.date(year=2010, month=11, day=20),
            campaign=self.campaign, phase_type='competition',
        )
        self.city = City.objects.create(name="Testing City", slug="testing_city")

        self.company = Company.objects.create(name="Testing Company")
        self.subsidiary = Subsidiary.objects.create(company=self.company, city=self.city)
        self.team = Team.objects.create(name="Testing team", campaign=self.campaign, subsidiary=self.subsidiary)

        self.user = User.objects.create(first_name="Testing", last_name="User", username="user1", email="user1@email.com")
        self.userprofile = UserProfile.objects.create(user=self.user)
        self.user_attendance = UserAttendance.objects.create(userprofile=self.userprofile, campaign=self.campaign, team=self.team, approved_for_team='approved')

        self.user_tm1 = User.objects.create(first_name="Team", last_name="Member 1", username="user2", email="user2@email.com")
        self.userprofile_tm1 = UserProfile.objects.create(user=self.user_tm1)
        self.user_attendance_tm1 = UserAttendance.objects.create(userprofile=self.userprofile_tm1, campaign=self.campaign, team=self.team, approved_for_team='approved')

        self.user_tm2 = User.objects.create(first_name="Team", last_name="Member 2", username="user3", email="user3@email.com")
        self.userprofile_tm2 = UserProfile.objects.create(user=self.user_tm2)
        self.user_attendance_tm2 = UserAttendance.objects.create(userprofile=self.userprofile_tm2, campaign=self.campaign, team=self.team, approved_for_team='approved')

        self.company_admin = CompanyAdmin.objects.create(userprofile=self.user.userprofile, administrated_company=self.company, campaign=self.campaign)

    def test_send_approval_request_mail(self):
        email.approval_request_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - žádost o ověření členství")
        self.assertEqual(mail.outbox[1].subject, "Testing campaign 1 - žádost o ověření členství")
        self.assertEqual(mail.outbox[0].to[0], "user2@email.com")
        self.assertEqual(mail.outbox[1].to[0], "user3@email.com")

    def test_send_invitation_register_mail(self):
        email.invitation_register_mail(self.user_attendance, self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, "Testing campaign 1 - potvrzení registrace")
        self.assertEqual(msg.to[0], "user1@email.com")
        link = 'http://testing_campaign_1.localhost:8000/%s/tym/%s/user1@email.com/' % (self.userprofile.language, self.user_attendance.team.invitation_token)
        self.assertTrue(link in msg.body)

    def test_send_register_mail(self):
        email.register_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, "Testing campaign 1 - potvrzení registrace")
        self.assertEqual(msg.to[0], "user1@email.com")
        link = 'http://testing_campaign_1.localhost:8000/%s/' % self.userprofile.language
        self.assertTrue(link in msg.body)

    def test_send_team_membership_approval_mail(self):
        email.team_membership_approval_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - potvrzení ověření členství v týmu")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")

    def test_send_team_membership_denial_mail(self):
        email.team_membership_denial_mail(self.user_attendance, self.user_attendance, "reason of denial")
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, "Testing campaign 1 - ZAMÍTNUTÍ členství v týmu")
        self.assertEqual(msg.to[0], "user1@email.com")
        link = 'http://testing_campaign_1.localhost:8000/%s/tym/' % self.userprofile.language
        self.assertTrue(link in msg.body)

    def test_send_team_created_mail(self):
        email.team_created_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, "Testing campaign 1 - potvrzení vytvoření týmu")
        self.assertEqual(msg.to[0], "user1@email.com")
        link = 'http://testing_campaign_1.localhost:8000/%s/pozvanky/' % self.userprofile.language
        self.assertTrue(link in msg.body)

    def test_send_invitation_mail(self):
        email.invitation_mail(self.user_attendance, "email@email.com")
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, "Testing campaign 1 - pozvánka do týmu")
        self.assertEqual(msg.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(msg.to[0], "email@email.com")
        self.assertEqual(msg.to[0], "email@email.com")
        link_cs = 'http://testing_campaign_1.localhost:8000/cs/registrace/%s/email@email.com/' % self.user_attendance.team.invitation_token
        self.assertTrue(link_cs in msg.body)
        link_en = 'http://testing_campaign_1.localhost:8000/en/registrace/%s/email@email.com/' % self.user_attendance.team.invitation_token
        self.assertTrue(link_en in msg.body)

    def test_send_payment_confirmation_mail(self):
        email.payment_confirmation_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - přijetí platby")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")

    def test_send_payment_confirmation_company_mail(self):
        email.payment_confirmation_company_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - přijetí platby")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")

    def test_send_company_admin_register_competitor_mail(self):
        email.company_admin_register_competitor_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, "Testing campaign 1 - koordinátor organizace - potvrzení registrace")
        self.assertEqual(msg.to[0], "user1@email.com")

    def test_send_company_admin_register_no_competitor_mail(self):
        email.company_admin_register_no_competitor_mail(self.company_admin, self.company)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - koordinátor organizace - potvrzení registrace")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            message = "Zpráva pro kandidáta/ku Testing User na koordinátora/ku organizace Testing Company v soutěži Testing campaign 1."
        else:
            message = "A message for Testing User, a candidate for the company coordinator role in Testing Company in the Testing campaign 1 competition."
        self.assertTrue(message in msg.body)

    def test_send_company_admin_approval_mail(self):
        email.company_admin_approval_mail(self.company_admin)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - koordinátor organizace - schválení správcovství organizace")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")
        msg = mail.outbox[0]
        link = 'http://testing_campaign_1.localhost:8000/%s/spolecnost/zadost_admina/' % self.userprofile.language
        self.assertTrue(link in msg.body)
        if self.userprofile.language == 'cs':
            message = "Zpráva pro Testing User, koordinátora organizace Testing Company v soutěži Testing campaign 1"
        else:
            message = "A message for Testing User, a company coordinator in Testing Company in the Testing campaign 1 competition."
        self.assertTrue(message in msg.body)

    def test_send_company_admin_rejected_mail(self):
        email.company_admin_rejected_mail(self.company_admin)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - koordinátor organizace - zamítnutí správcovství organizace")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            message = "Zpráva pro Testing User ze soutěže Testing campaign 1."
        else:
            message = "A message for Testing User from the Testing campaign 1 competition."
        self.assertTrue(message in msg.body)


class TestEmailsEn(TestEmails):
    def setUp(self):
        super(TestEmailsEn, self).setUp()
        self.userprofile.language = "en"
        self.company_admin.userprofile.language = "en"
