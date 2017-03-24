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
from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from dpnk.test.util import print_response  # noqa

from model_mommy import mommy

import settings


class DispatchViewTests(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.example.com", HTTP_REFERER="test-referer")
        user = mommy.make("auth.User", is_staff=True)
        self.client.force_login(user, settings.AUTHENTICATION_BACKENDS[0])

    def test_bad_format(self):
        """ Test, that bad input format shows error """
        post_data = {
            'dispatch_id': 'a34',
            'next': 'Next',
        }
        response = self.client.post(reverse('dispatch'), post_data)
        self.assertContains(
            response,
            "<strong>Číslo balíku/krabice je v nesprávném formátu</strong>",
            html=True,
        )

    def test_already_dispatched(self):
        """ Test, that warning shows if package is already dispatched """
        mommy.make(
            "TeamPackage",
            dispatched=True,
            id=123,
        )
        post_data = {
            'dispatch_id': 'T123',
            'next': 'Next',
        }
        response = self.client.post(reverse('dispatch'), post_data, follow=True)
        self.assertContains(
            response,
            '<strong style="color:orange">Balíček/krabice byl v minulosti již zařazen k sestavení: Balíček bez týmu</strong>',
            html=True,
        )

    def test_subsidiary_dispatch_teampackage_not(self):
        """
        Test, that warning shows if subsidiary package has undispatched team packages.
        """
        mommy.make(
            "TeamPackage",
            dispatched=False,
            box__id=123,
            id=123,
        )
        post_data = {
            'dispatch_id': 'S123',
            'next': 'Next',
        }
        response = self.client.post(reverse('dispatch'), post_data, follow=True)
        self.assertContains(
            response,
            "<strong style='color:red'>"
            "Tato krabice obsahuje balíčky, které ještě nebyli zařazeny k sestavení: "
            "<a href='/admin/t_shirt_delivery/teampackage/?box__id__exact=123&amp;dispatched__exact=0'>"
            "zobrazit seznam nesestavených balíčků"
            "</a></strong>",
            html=True,
        )

    def test_not_found(self):
        """ Test, that warning shows if package is not found """
        post_data = {
            'dispatch_id': 'T123',
            'next': 'Next',
        }
        response = self.client.post(reverse('dispatch'), post_data, follow=True)
        self.assertContains(
            response,
            '<strong style="color:red">Balíček/krabice nebyl nalezen.</strong>',
            html=True,
        )

    def test_dispatch(self):
        """ Test, that warning shows if package is already dispatched """
        team_package = mommy.make(
            "TeamPackage",
            id=123,
        )
        post_data = {
            'dispatch_id': 'T123',
            'next': 'Next',
        }
        response = self.client.post(reverse('dispatch'), post_data, follow=True)
        self.assertContains(
            response,
            '<strong style="color:green">Balíček/krabice zařazen jako sestavený: Balíček bez týmu</strong>',
            html=True,
        )
        team_package.refresh_from_db()
        self.assertTrue(team_package.dispatched)
