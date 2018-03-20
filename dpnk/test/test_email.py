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


def language_url_infix(language):
    if language == 'cs':
        return ""
    else:
        return "/en"


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
        self.user_attendance = UserAttendance.objects.create(
            userprofile=self.userprofile,
            campaign=self.campaign,
            team=self.team,
            approved_for_team='approved',
        )

        self.user_tm1 = User.objects.create(first_name="Team", last_name="Member 1", username="user2", email="user2@email.com")
        self.userprofile_tm1 = UserProfile.objects.create(user=self.user_tm1)
        self.user_attendance_tm1 = UserAttendance.objects.create(
            userprofile=self.userprofile_tm1,
            campaign=self.campaign,
            team=self.team,
            approved_for_team='approved',
        )

        self.user_tm2 = User.objects.create(first_name="Team", last_name="Member 2", username="user3", email="user3@email.com")
        self.userprofile_tm2 = UserProfile.objects.create(user=self.user_tm2)
        self.user_attendance_tm2 = UserAttendance.objects.create(
            userprofile=self.userprofile_tm2,
            campaign=self.campaign,
            team=self.team,
            approved_for_team='approved',
        )

        self.company_admin = CompanyAdmin.objects.create(
            userprofile=self.user.userprofile,
            administrated_company=self.company,
            campaign=self.campaign,
            company_admin_approved='undecided',
        )
        mail.outbox = []

    def test_send_approval_request_mail(self):
        email.approval_request_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 2)
        if self.userprofile.language == 'cs':
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - žádost o ověření členství")
            self.assertEqual(mail.outbox[1].subject, "Testing campaign 1 - žádost o ověření členství")
        else:
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - membership verification request")
            self.assertEqual(mail.outbox[1].subject, "Testing campaign 1 - membership verification request")
        self.assertEqual(mail.outbox[0].to[0], "user2@email.com")
        self.assertEqual(mail.outbox[1].to[0], "user3@email.com")

    def test_send_invitation_register_mail(self):
        email.invitation_register_mail(self.user_attendance, self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(msg.subject, "Testing campaign 1 - potvrzení registrace")
        else:
            self.assertEqual(msg.subject, "Testing campaign 1 - registration confirmation")
        self.assertEqual(msg.to[0], "user1@email.com")
        link = 'https://testing_campaign_1.localhost:8000%s/tym/%s/user1@email.com/' % (
            language_url_infix(self.userprofile.language),
            self.user_attendance.team.invitation_token,
        )
        self.assertTrue(link in msg.body)

    def test_send_register_mail(self):
        email.register_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(msg.subject, "Testing campaign 1 - potvrzení registrace")
        else:
            self.assertEqual(msg.subject, "Testing campaign 1 - registration confirmation")
        self.assertEqual(msg.to[0], "user1@email.com")
        link = 'https://testing_campaign_1.localhost:8000%s/' % language_url_infix(self.userprofile.language)
        self.assertTrue(link in msg.body)

    def test_unfilled_rides_notification(self):
        email.unfilled_rides_mail(self.user_attendance, 5)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(str(msg.subject), "Testing campaign 1 - připomenutí nevyplněných jízd")
        else:
            self.assertEqual(str(msg.subject), "Testing campaign 1 - reminder of unfilled rides")
        self.assertEqual(msg.to[0], "user1@email.com")
        link = 'https://testing_campaign_1.localhost:8000%s/' % language_url_infix(self.userprofile.language)
        self.assertTrue(link in msg.body)
        if self.userprofile.language == 'cs':
            message = "za posledních 5 dní jste si nevyplnil/a jízdy"
        else:
            message = "in last 5 days"
        self.assertTrue(message in msg.body)
        if self.userprofile.language == 'cs':
            message = "že jízdy lze vyplňovat pouze 7 dní zpětně"
        else:
            message = "filled in for 7 days back"
        self.assertTrue(message in msg.body)

    def test_send_team_membership_approval_mail(self):
        email.team_membership_approval_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        if self.userprofile.language == 'cs':
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - potvrzení ověření členství v týmu")
        else:
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - team membership verification confirmation")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")

    def test_send_team_membership_denial_mail(self):
        email.team_membership_denial_mail(self.user_attendance, self.user_attendance, "reason of denial")
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(msg.subject, "Testing campaign 1 - ZAMÍTNUTÍ členství v týmu")
        else:
            self.assertEqual(msg.subject, "Testing campaign 1 - Team membership DENIED")
        self.assertEqual(msg.to[0], "user1@email.com")
        link = 'https://testing_campaign_1.localhost:8000%s/tym/' % language_url_infix(self.userprofile.language)
        self.assertTrue(link in msg.body)

    def test_send_team_created_mail(self):
        email.team_created_mail(self.user_attendance, 'Foo team')
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(msg.subject, "Testing campaign 1 - potvrzení vytvoření týmu")
        else:
            self.assertEqual(msg.subject, "Testing campaign 1 - team creation confirmation")
        self.assertEqual(msg.to[0], "user1@email.com")
        link = 'https://testing_campaign_1.localhost:8000%s/pozvanky/' % language_url_infix(self.userprofile.language)
        self.assertTrue(link in msg.body)

    def test_send_invitation_mail(self):
        email.invitation_mail(self.user_attendance, "email@email.com")
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(msg.subject, "Testing campaign 1 - pozvánka do týmu (invitation to a team)")
        else:
            self.assertEqual(msg.subject, "Testing campaign 1 - invitation to a team (pozvánka do týmu)")
        self.assertEqual(msg.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(msg.to[0], "email@email.com")
        link_cs = 'https://testing_campaign_1.localhost:8000/registrace/%s/email@email.com/' % self.user_attendance.team.invitation_token
        self.assertTrue(link_cs in msg.body)
        link_en = 'https://testing_campaign_1.localhost:8000/en/registrace/%s/email@email.com/' % self.user_attendance.team.invitation_token
        self.assertTrue(link_en in msg.body)

    def test_send_payment_confirmation_mail(self):
        email.payment_confirmation_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        if self.userprofile.language == 'cs':
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - přijetí platby")
        else:
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - payment acceptation")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")

    def test_send_payment_confirmation_company_mail(self):
        email.payment_confirmation_company_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        if self.userprofile.language == 'cs':
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - přijetí platby")
        else:
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - payment acceptation")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")

    def test_send_company_admin_register_competitor_mail(self):
        email.company_admin_register_competitor_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(msg.subject, "Testing campaign 1 - firemní koordinátor - potvrzení registrace")
        else:
            self.assertEqual(msg.subject, "Testing campaign 1 - Company Coordinator - registration confirmation")
        self.assertEqual(msg.to[0], "user1@email.com")

    def test_send_company_admin_register_no_competitor_mail(self):
        email.company_admin_register_no_competitor_mail(self.company_admin, self.company)
        self.assertEqual(len(mail.outbox), 1)
        if self.userprofile.language == 'cs':
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - firemní koordinátor - potvrzení registrace")
        else:
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - Company Coordinator - registration confirmation")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            message = "Zpráva pro kandidáta Testing User na funkci firemního koordinátora v organizaci Testing Company v soutěži Testing campaign 1."
        else:
            message = (
                "A message for Testing User, "
                "a candidate for the company coordinator role in Testing Company in the Testing campaign 1 competition."
            )
        self.assertTrue(message in msg.body)

    def test_send_company_admin_approval_mail(self):
        email.company_admin_approval_mail(self.company_admin)
        self.assertEqual(len(mail.outbox), 1)
        if self.userprofile.language == 'cs':
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - firemní koordinátor - schválení správcovství organizace")
        else:
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - Company Coordinator - company administration approval")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")
        msg = mail.outbox[0]
        link = 'https://testing_campaign_1.localhost:8000%s/spolecnost/editovat_spolecnost/' % language_url_infix(self.userprofile.language)
        self.assertTrue(link in msg.body)
        if self.userprofile.language == 'cs':
            message = "Zpráva pro Testing User, firemního koordinátora v organizaci Testing Company v soutěži Testing campaign 1"
        else:
            message = "A message for Testing User, a company coordinator in Testing Company in the Testing campaign 1 competition."
        self.assertTrue(message in msg.body)

    def test_send_company_admin_rejected_mail(self):
        email.company_admin_rejected_mail(self.company_admin)
        self.assertEqual(len(mail.outbox), 1)
        if self.userprofile.language == 'cs':
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - firemní koordinátor - zamítnutí správcovství organizace")
        else:
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - Company Coordinator - company administration denial")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            message = "Zpráva pro Testing User ze soutěže Testing campaign 1."
        else:
            message = "A message for Testing User from the Testing campaign 1 competition."
        self.assertTrue(message in msg.body)


class TestEmailsEn(TestEmails):
    def setUp(self):
        super().setUp()
        self.userprofile.language = "en"
        self.company_admin.userprofile.language = "en"
