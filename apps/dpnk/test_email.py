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

from django.test import TestCase
from django.test.utils import override_settings
from dpnk.models import UserAttendance, Company, CompanyAdmin, UserProfile, Campaign, Team, Subsidiary, City
from django.contrib.auth.models import User
from . import email


@override_settings(EMAIL_FILE_PATH='/tmp/dpnk-test-emails')
@override_settings(EMAIL_BACKEND='django.core.mail.backends.filebased.EmailBackend')
class TestEmails(TestCase):
    def setUp(self):
        self.campaign = Campaign.objects.create(name="Testing campaign 1", slug="testing_campaign_1")
        self.city = City.objects.create(name="Testing City", slug="testing_city")

        self.company = Company.objects.create(name="Testing Company")
        self.subsidiary = Subsidiary.objects.create(company=self.company, city=self.city)
        self.team = Team.objects.create(name="Testing team", campaign=self.campaign, subsidiary=self.subsidiary)

        self.user = User.objects.create(first_name="Testing", last_name="User", username="user1", email="user1@email.com")
        self.userprofile = UserProfile.objects.create(user=self.user)
        self.user_attendance = UserAttendance.objects.create(userprofile=self.userprofile, campaign=self.campaign, team=self.team)

        self.user_tm1 = User.objects.create(first_name="Team", last_name="Member 1", username="user2", email="user2@email.com")
        self.userprofile_tm1 = UserProfile.objects.create(user=self.user_tm1)
        self.user_attendance_tm1 = UserAttendance.objects.create(userprofile=self.userprofile_tm1, campaign=self.campaign, team=self.team)

        self.user_tm2 = User.objects.create(first_name="Team", last_name="Member 2", username="user3", email="user3@email.com")
        self.userprofile_tm2 = UserProfile.objects.create(user=self.user_tm2)
        self.user_attendance_tm2 = UserAttendance.objects.create(userprofile=self.userprofile_tm2, campaign=self.campaign, team=self.team)

        self.company_admin = CompanyAdmin.objects.create(user=self.user, administrated_company=self.company, campaign=self.campaign)

    def test_send_approval_request_mail(self):
        email.approval_request_mail(self.user_attendance)

    def test_send_invitation_register_mail(self):
        email.invitation_register_mail(self.user_attendance, self.user_attendance)

    def test_send_register_mail(self):
        email.register_mail(self.user_attendance)

    def test_send_team_membership_approval_mail(self):
        email.team_membership_approval_mail(self.user_attendance)

    def test_send_team_membership_denial_mail(self):
        email.team_membership_denial_mail(self.user_attendance, self.user_attendance, "reason of denial")

    def test_send_team_created_mail(self):
        email.team_created_mail(self.user_attendance)

    def test_send_invitation_mail(self):
        email.invitation_mail(self.user_attendance, "email@email.cz")

    def test_send_payment_confirmation_mail(self):
        email.payment_confirmation_mail(self.user_attendance)

    def test_send_payment_confirmation_company_mail(self):
        email.payment_confirmation_company_mail(self.user_attendance)

    def test_send_company_admin_register_competitor_mail(self):
        email.company_admin_register_competitor_mail(self.user_attendance)

    def test_send_company_admin_register_no_competitor_mail(self):
        email.company_admin_register_no_competitor_mail(self.company_admin, self.company)

    def test_send_company_admin_approval_mail(self):
        email.company_admin_approval_mail(self.company_admin)

    def test_send_company_admin_rejected_mail(self):
        email.company_admin_rejected_mail(self.company_admin)
