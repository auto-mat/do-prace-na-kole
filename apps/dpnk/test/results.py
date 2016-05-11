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

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from dpnk import models, util, actions
from dpnk.test.util import DenormMixin, ClearCacheMixin
from dpnk.test.util import print_response  # noqa
import datetime


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class ResultTests(ClearCacheMixin, DenormMixin, TestCase):
    fixtures = ['campaign', 'auth_user', 'users', 'transactions', 'batches', 'company_competition', 'test_results_data', 'trips']

    def test_dpnk_competition_results_unknown(self):
        address = reverse('competition_results', kwargs={'competition_slug': 'unexistent_competition'})
        response = self.client.get(address)
        self.assertContains(response, "Tuto soutěž v systému nemáme.")

    def test_dpnk_competition_results_company_competition(self):
        address = reverse('competition_results', kwargs={'competition_slug': 'vykonnost-spolecnosti'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Výkonnost společností:")

    def test_dpnk_competition_results_FQ_LB(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        models.Competition.objects.get(slug="FQ-LB").recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'FQ-LB', 'limit': 1})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Pravidelnost týmů:")
        self.assertContains(response, "3,0")
        self.assertContains(response, "Testing team 1")

    def test_dpnk_competition_results_quest(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        competition = models.Competition.objects.filter(slug="quest")
        actions.normalize_questionnqire_admissions(None, None, competition)
        competition.get().recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'quest'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Dotazník:")
        self.assertContains(response, "13,0")
        self.assertContains(response, '<a href="/cs/questionnaire_answers/quest/#comp_res_')
        self.assertContains(response, 'Testing User 1')

    def test_dpnk_competition_results_vykonnost(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        models.Competition.objects.get(slug="vykonnost").recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'vykonnost'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Výkonnost:")
        self.assertContains(response, "161,9")
        self.assertContains(response, "Testing User 1")

    def test_dpnk_competition_results_TF(self):
        address = reverse('competition_results', kwargs={'competition_slug': 'TF'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Team frequency:")
