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

from django.test import TestCase, RequestFactory
from dpnk import actions, models
from django.contrib import admin
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.management import call_command
from unittest.mock import MagicMock
import createsend


class TestActions(TestCase):
    fixtures = ['campaign', 'users', 'transactions', 'batches', 'vouchers']

    def setUp(self):
        self.modeladmin = admin.ModelAdmin(models.UserAttendance, "")
        self.factory = RequestFactory()
        self.request = self.factory.get("")
        self.request.user = models.User.objects.get(username="test")
        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)
        call_command('denorm_init')
        call_command('denorm_rebuild')

    def tearDown(self):
        call_command('denorm_drop')

    def test_approve_am_payment(self):
        queryset = models.UserAttendance.objects.all()
        payment = models.Payment.objects.get(pk=5)
        self.assertEquals(payment.status, 1)
        actions.approve_am_payment(self.modeladmin, self.request, queryset)
        payment = models.Payment.objects.get(pk=5)
        self.assertEquals(payment.status, 99)

    def test_update_mailing(self):
        ret_mailing_id = "344ass"
        createsend.Subscriber.add = MagicMock(return_value=ret_mailing_id)
        queryset = models.UserAttendance.objects.all()
        actions.update_mailing(self.modeladmin, self.request, queryset)

    def test_add_trips(self):
        queryset = models.UserAttendance.objects.all()
        actions.add_trips(self.modeladmin, self.request, queryset)

    def test_assign_vouchers(self):
        queryset = models.UserAttendance.objects.all()[1:2]
        voucher = models.Voucher.objects.get(pk=1)
        self.assertEquals(voucher.user_attendance, None)
        actions.assign_vouchers(self.modeladmin, self.request, queryset)
        voucher = models.Voucher.objects.get(pk=1)
        self.assertNotEquals(voucher.user_attendance.pk, None)

    def test_assign_vouchers_not_enough(self):
        queryset = models.UserAttendance.objects.all()
        actions.assign_vouchers(self.modeladmin, self.request, queryset)
        voucher = models.Voucher.objects.get(pk=1)
        self.assertEquals(voucher.user_attendance, None)

    def test_show_distance(self):
        queryset = models.UserAttendance.objects.all()
        actions.show_distance(self.modeladmin, self.request, queryset)

    def test_recalculate_results(self):
        queryset = models.UserAttendance.objects.all()
        actions.recalculate_results(self.modeladmin, self.request, queryset)

    def test_touch_user_attendance(self):
        queryset = models.UserAttendance.objects.all()
        actions.touch_user_attendance(self.modeladmin, self.request, queryset)

    def test_recalculate_competitions_results(self):
        queryset = models.Competition.objects.all()
        actions.recalculate_competitions_results(self.modeladmin, self.request, queryset)

    def test_normalize_questionnqire_admissions(self):
        queryset = models.Competition.objects.all()
        actions.normalize_questionnqire_admissions(self.modeladmin, self.request, queryset)
