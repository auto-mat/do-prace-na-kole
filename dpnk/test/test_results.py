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

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from dpnk import actions, models, results, util
from dpnk.test.util import ClearCacheMixin, DenormMixin
from dpnk.test.util import print_response  # noqa


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class ResultTests(ClearCacheMixin, DenormMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches', 'company_competition', 'test_results_data', 'trips']

    def test_dpnk_competition_results_unknown(self):
        address = reverse('competition_results', kwargs={'competition_slug': 'unexistent_competition'})
        response = self.client.get(address)
        self.assertContains(response, "Tuto soutěž v systému nemáme.")

    def test_dpnk_competition_results_company_length_competition(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        models.Competition.objects.get(slug="vykonnost-spolecnosti").recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'vykonnost-spolecnosti'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Výkonnost společností:")
        self.assertContains(response, "Competition rules")
        self.assertContains(response, "<td>161,9</td>", html=True)
        self.assertContains(response, "Testing company")

    def test_dpnk_competition_results_company_competition_frequency(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        models.Competition.objects.get(slug="pravidelnost-spolecnosti").recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'pravidelnost-spolecnosti'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Pravidelnost společností:")
        self.assertContains(response, "Competition rules")
        self.assertContains(response, "<td>1.</td>", html=True)
        self.assertContains(response, "<td>3,3</td>", html=True)
        self.assertContains(response, "<td>2</td>", html=True)
        self.assertContains(response, "<td>61</td>", html=True)
        self.assertContains(response, "Testing company")

    @override_settings(
        FAKE_DATE=datetime.date(year=2011, month=12, day=20),
    )
    def test_dpnk_competition_results_company_competition_questionnaire(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        competition = models.Competition.objects.filter(slug="dotaznik-spolecnosti")
        competition.get().recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'dotaznik-spolecnosti'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Dotazník společností:")
        self.assertContains(response, "Competition rules")
        self.assertContains(response, "<td>1.</td>", html=True)
        self.assertContains(response, "<td>0,0</td>", html=True)
        self.assertContains(response, "Testing company")

    def test_dpnk_competition_results_FQ_LB(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        models.Competition.objects.get(slug="FQ-LB").recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'FQ-LB', 'limit': 1})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Pravidelnost týmů:")
        self.assertContains(response, "<td>2,9</td>", html=True)
        self.assertContains(response, "<td>2</td>", html=True)
        self.assertContains(response, "<td>69</td>", html=True)
        self.assertContains(response, "<td>3</td>", html=True)
        self.assertContains(response, "Testing team 1")

    def test_dpnk_competition_results_quest_not_finished(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        competition = models.Competition.objects.filter(slug="quest")
        actions.normalize_questionnqire_admissions(None, None, competition)
        competition.get().recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'quest'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Dotazník:")
        self.assertContains(response, "Výsledky této soutěže se nezobrazují")

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=12, day=20),
    )
    def test_dpnk_competition_results_quest(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        competition = models.Competition.objects.filter(slug="quest")
        actions.normalize_questionnqire_admissions(None, None, competition)
        competition.get().recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'quest'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Dotazník:")
        self.assertContains(response, "16,2")
        self.assertContains(response, '<a href="/cs/questionnaire_answers/quest/#comp_res_')
        self.assertContains(response, 'Testing User 1')

    def test_dpnk_competition_results_vykonnost(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        models.Competition.objects.get(slug="vykonnost").recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'vykonnost'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Výkonnost:")
        self.assertContains(response, "<td>161,9</td>", html=True)
        self.assertContains(response, "Testing User 1")

    def test_dpnk_competition_results_vykonnost_tymu(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        models.Competition.objects.get(slug="vykonnost-tymu").recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'vykonnost-tymu'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Výkonnost týmů:")
        self.assertContains(response, "Po&shy;čet za&shy;po&shy;čí&shy;ta&shy;ných ki&shy;lo&shy;me&shy;trů")
        self.assertContains(response, "<td>54,0</td>", html=True)
        self.assertContains(response, "<td>161,9</td>", html=True)
        self.assertContains(response, "<td>3</td>", html=True)
        self.assertContains(response, "Testing team 1")

    def test_dpnk_competition_results_pravidelnost_jednotlivcu(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        models.Competition.objects.get(slug="pravidelnost-jednotlivcu").recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'pravidelnost-jednotlivcu'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Pravidelnost jednotlivců:")
        self.assertContains(response, "Po&shy;čet za&shy;po&shy;čí&shy;ta&shy;ných jí&shy;zd")
        self.assertContains(response, "<td>1.</td>", html=True)
        self.assertContains(response, "<td>8,7</td>", html=True)
        self.assertContains(response, "<td>2</td>", html=True)
        self.assertContains(response, "<td>23</td>", html=True)
        self.assertContains(response, "Testing User 1")
        self.assertContains(response, "Testing team 1")
        self.assertContains(response, "Testing city")

    def test_dpnk_competition_results_company_competition(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        models.Competition.objects.get(slug="FA-testing-campaign-pravidelnost-spolecnosti").recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'FA-testing-campaign-pravidelnost-spolecnosti'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Pravidelnost společnosti:")
        self.assertContains(response, "Po&shy;čet za&shy;po&shy;čí&shy;ta&shy;ných jí&shy;zd")
        self.assertContains(response, "<td>1.</td>", html=True)
        self.assertContains(response, "<td>0</td>", html=True)
        self.assertContains(response, "<td>3</td>", html=True)
        self.assertContains(response, "Ulice / Testing company")
        self.assertContains(response, "Testing team 1")
        self.assertContains(response, "Testing city")

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=12, day=20),
    )
    def test_dpnk_competition_results_dotaznik_tymu(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        models.Competition.objects.get(slug="team-questionnaire").recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'team-questionnaire'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Dotazník týmů:")
        self.assertContains(response, "Po&shy;čet sou&shy;tě&shy;ží&shy;cí&shy;ch v")
        self.assertContains(response, "<td>1.</td>", html=True)
        self.assertContains(response, "<td>0,0</td>", html=True)
        self.assertContains(response, "<td>3</td>", html=True)
        self.assertContains(response, "Testing team 1")
        self.assertContains(response, "Ulice / Testing company")
        self.assertContains(response, "Testing city")

    def test_dpnk_competition_results_TF(self):
        address = reverse('competition_results', kwargs={'competition_slug': 'TF'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Team frequency:")


class RidesBaseTests(TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users']

    def test_get_minimum_rides_base_proportional(self):
        competition = models.Competition.objects.get(slug="FQ-LB")
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 1)), 1)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 7)), 10)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 15)), 23)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 30)), 23)

    def test_get_minimum_rides_base_proportional_phase(self):
        competition = models.Phase.objects.get(pk=2)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 1)), 0)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 7)), 5)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 15)), 12)
        self.assertEquals(results.get_minimum_rides_base_proportional(competition, datetime.date(2010, 11, 30)), 25)
