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
from django.contrib import admin
from django.contrib.messages.api import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase

from dpnk.models import UserAttendance
from dpnk.test.mommy_recipes import UserAttendanceRecipe

from t_shirt_delivery import actions, models


class TestActions(TestCase):
    def setUp(self):
        self.modeladmin = admin.ModelAdmin(UserAttendance, "")
        self.factory = RequestFactory()
        self.request = self.factory.get("")
        self.request.subdomain = "testing-campaign"
        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

    def test_create_batch(self):
        """ Test, that create_batch action makes DeliveryBatch with it's boxes """
        UserAttendanceRecipe.make(
            _quantity=2,
        )
        queryset = UserAttendance.objects.all()
        actions.create_batch(self.modeladmin, self.request, queryset)
        message = get_messages(self.request)._queued_messages[0].message
        self.assertEquals(message, "Vytvořena nová dávka obsahující 2 položek")
        self.assertEqual(
            models.DeliveryBatch.objects.count(),
            1,
        )
