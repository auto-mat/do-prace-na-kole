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

from django.test import TestCase

from dpnk.social_pipeline import create_userprofile

from model_mommy import mommy


class TestSocialPipeline(TestCase):
    def test_create_userprofile(self):
        user = mommy.make("User")
        response = {'gender': 'male'}
        create_userprofile(None, None, response, user, is_new=True)
        self.assertEqual(user.userprofile.sex, 'male')

    def test_create_userprofile_null_sex(self):
        user = mommy.make("User")
        response = {}
        create_userprofile(None, None, response, user, is_new=True)
        self.assertEqual(user.userprofile.sex, 'unknown')

    def test_create_userprofile_null_user(self):
        """ Test, that call with null user doesn't cause exception """
        create_userprofile(None, None, {}, None, is_new=True)

    def test_create_userprofile_is_not_new(self):
        """ Test, that call with is_new=False doesn't create profile """
        user = mommy.make("User")
        create_userprofile(None, None, {}, user, is_new=False)
        self.assertFalse(hasattr(user, 'userprofile'))
