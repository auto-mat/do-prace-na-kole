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

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from dpnk import util
import datetime


@override_settings(
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class UtilTests(TestCase):
    def test_day_active_last7(self):
        self.assertTrue(util.day_active_last7(datetime.date(2010, 11, 14)))
        self.assertTrue(util.day_active_last7(datetime.date(2010, 11, 20)))
        self.assertFalse(util.day_active_last7(datetime.date(2010, 11, 13)))
        self.assertFalse(util.day_active_last7(datetime.date(2010, 11, 21)))

    def test_day_active_last7_cut_after_may(self):
        self.assertTrue(util.day_active_last7_cut_after_may(datetime.date(2010, 11, 14)))
        self.assertTrue(util.day_active_last7_cut_after_may(datetime.date(2010, 11, 20)))
        self.assertFalse(util.day_active_last7_cut_after_may(datetime.date(2010, 11, 13)))
        self.assertFalse(util.day_active_last7_cut_after_may(datetime.date(2010, 11, 21)))

    @override_settings(
        FAKE_DATE=datetime.date(year=2016, month=6, day=3),
    )
    def test_day_active_last7_cut_after_may_may(self):
        self.assertTrue(util.day_active_last7_cut_after_may(datetime.date(2016, 6, 1)))
        self.assertTrue(util.day_active_last7_cut_after_may(datetime.date(2016, 6, 3)))
        self.assertFalse(util.day_active_last7_cut_after_may(datetime.date(2016, 5, 31)))
        self.assertFalse(util.day_active_last7_cut_after_may(datetime.date(2016, 6, 4)))

    @override_settings(
        FAKE_DATE=datetime.date(year=2016, month=6, day=7),
    )
    def test_day_active_last7_cut_after_may_may9(self):
        self.assertTrue(util.day_active_last7_cut_after_may(datetime.date(2016, 6, 1)))
        self.assertTrue(util.day_active_last7_cut_after_may(datetime.date(2016, 6, 7)))
        self.assertFalse(util.day_active_last7_cut_after_may(datetime.date(2016, 5, 31)))
        self.assertFalse(util.day_active_last7_cut_after_may(datetime.date(2016, 6, 8)))


class TodayTests(TestCase):
    def test_today(self):
        del settings.FAKE_DATE
        self.assertEquals(util._today(), datetime.date.today())
