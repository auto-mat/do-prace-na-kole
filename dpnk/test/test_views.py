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

from unittest.mock import patch

import denorm

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from django.test.utils import override_settings

from dpnk import actions, models, util, views
from dpnk.test.tests import ViewsLogon
from dpnk.test.util import ClearCacheMixin, DenormMixin
from dpnk.test.util import print_response  # noqa

import settings


@override_settings(
    PAYU_POS_ID="123321"
)
class CompetitionsViewTests(ViewsLogon):
    def test_competition_rules(self):
        address = reverse('competition-rules-city', kwargs={'city_slug': "testing-city"})
        response = self.client.get(address)
        self.assertContains(response, "DPNK - Pravidla soutěží - Testing city")
        self.assertContains(response, "Competition vykonnostr rules")
        self.assertContains(response, "soutěž na vzdálenost jednotlivců  ve městě Testing city")
        self.assertContains(response, "soutěž na vzdálenost týmů  ve městě Testing city pro muže")

    def test_competition_results(self):
        address = reverse('competition-results-city', kwargs={'city_slug': "testing-city"})
        response = self.client.get(address)
        self.assertContains(response, "10 000,0")
        self.assertContains(response, "Ulice / Testing company")
        self.assertContains(response, "DPNK - Výsledky soutěží - Testing city")
        self.assertContains(response, "soutěž na vzdálenost jednotlivců  ve městě Testing city")

    def test_payment(self):
        address = reverse('payment')
        response = self.client.get(address)
        self.assertContains(response, '<input type="hidden" name="amount" value="12000">', html=True)
        self.assertContains(response, '<input type="hidden" name="pos_id" value="123321">', html=True)
        self.assertContains(response, '<input type="hidden" name="order_id" value="1128-1">', html=True)

    def test_team_members(self):
        util.rebuild_denorm_models(models.Team.objects.filter(pk=1))
        util.rebuild_denorm_models(models.UserAttendance.objects.get(pk=1115).team.all_members())
        address = reverse('team_members')
        response = self.client.get(address)
        self.assertContains(response, 'Odsouhlasený')
        self.assertContains(response, 'test-registered@test.cz')

    def test_other_team_members(self):
        address = reverse('other_team_members_results')
        response = self.client.get(address)
        self.assertContains(response, 'Ještě nezačal/a soutěžit')
        self.assertContains(response, '30')
        self.assertContains(response, '156,9&nbsp;km')

    def test_edit_team(self):
        address = reverse('edit_team')
        response = self.client.get(address)
        self.assertContains(response, 'Upravit název týmu')
        self.assertContains(response, 'Testing team 1')

    def test_daily_chart(self):
        address = reverse(views.daily_chart)
        response = self.client.get(address)
        self.assertContains(response, '<img src=\'http://chart.apis.google.com/chart?chxl=0:|1:|2010-11-20|')

    def test_update_team(self):
        address = reverse('zmenit_tym')
        response = self.client.get(address)
        self.assertContains(response, 'Po koordinátorovi vaší organizace na emailové adrese')
        self.assertContains(response, 'test_wa@email.cz')
        self.assertContains(response, 'test@email.cz')
        self.assertContains(response, 'test@test.cz')
        self.assertContains(response, 'Testing team 1 (Nick, Testing User 1, Registered User 1)')

    def test_team_approval_request(self):
        address = reverse('zaslat_zadost_clenstvi')
        response = self.client.get(address)
        self.assertContains(response, 'Žádost o ověření členství byla odeslána.')
        self.assertEqual(len(mail.outbox), 2)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test2@test.cz'])
        msg = mail.outbox[1]
        self.assertEqual(msg.recipients(), ['test-registered@test.cz'])

    def test_payment_beneficiary(self):
        address = reverse('payment_beneficiary')
        response = self.client.get(address)
        self.assertContains(response, '<input type="hidden" name="amount" value="35000">', html=True)
        self.assertContains(response, '<input type="hidden" name="pos_id" value="123321">', html=True)
        self.assertContains(response, '<input type="hidden" name="order_id" value="1128-1">', html=True)

    def test_bike_repair(self):
        address = reverse('bike_repair')
        response = self.client.get(address)
        self.assertContains(response, 'Cykloservis')
        self.assertContains(response, 'Uživatelské jméno zákazníka')
        self.assertContains(response, 'Uživatelské jméno, které vám sdělí zákazník')
        self.assertContains(response, 'Poznámka')

    def test_bike_repair_post(self):
        address = reverse('bike_repair')
        post_data = {
            "user_attendance": "test@email.cz",
            "description": "Bike repair note",
            "submit": "Odeslat",
        }
        response = self.client.post(address, post_data)
        self.assertRedirects(response, reverse('bike_repair'))

        response = self.client.post(address, post_data)
        self.assertContains(response, 'Tento uživatel byl již')
        self.assertContains(response, 'v cykloservisu Testing User 1 (poznámka: Bike repair note).')
        self.assertEquals(response.status_code, 200)

    def test_bike_repair_post_nonexistent_user(self):
        address = reverse('bike_repair')
        post_data = {
            "user_attendance": "test test",
            "description": "Bike repair note",
            "submit": "Odeslat",
        }
        response = self.client.post(address, post_data)
        self.assertContains(response, 'Takový uživatel neexistuje')
        self.assertEquals(response.status_code, 200)

    def test_bike_repair_post_last_campaign(self):
        address = reverse('bike_repair')
        post_data = {
            "user_attendance": "test@test.cz",
            "description": "Bike repair note",
            "submit": "Odeslat",
        }
        response = self.client.post(address, post_data)
        self.assertContains(response, 'Tento uživatel není nováček, soutěžil již v předcházejících kampaních: Testing campaign - last year')
        self.assertEquals(response.status_code, 200)

    feed_value = (
        {
            "content": "Emission calculator description text",
            "published": "2016-12-12",
            "start_date": "2016-12-12",
            "title": "Title",
            "url": "http://example.com",
            "excerpt": "Excerpt",
        },
    )

    @patch('slumber.API')
    def test_login(self, slumber_api):
        slumber_instance = slumber_api.return_value
        slumber_instance.feed.get.return_value = self.feed_value
        address = reverse('login')
        response = self.client.get(address)
        self.assertRedirects(response, reverse('profil'), status_code=302)

    @patch('slumber.API')
    def test_dont_allow_adding_rides(self, slumber_api):
        slumber_instance = slumber_api.return_value
        slumber_instance.feed.get.return_value = self.feed_value
        cityincampaign = models.CityInCampaign.objects.get(city=self.user_attendance.team.subsidiary.city, campaign=self.user_attendance.campaign)
        cityincampaign.allow_adding_rides = False
        cityincampaign.save()

        address = reverse('profil')
        response = self.client.get(address)
        self.assertContains(response, '<div class="alert alert-info">Zde budete zadávat vaše jízdy</div>', html=True)

    @patch('slumber.API')
    def test_registration_access(self, slumber_api):
        slumber_instance = slumber_api.return_value
        slumber_instance.feed.get.return_value = self.feed_value
        address = reverse('registration_access')
        response = self.client.get(address)
        self.assertRedirects(response, reverse('profil'), status_code=302)


@override_settings(
    SITE_ID=2,
)
class InvoiceTests(ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'invoices']

    def setUp(self):
        self.client = Client(HTTP_HOST="testing-campaign.testserver")
        self.client.force_login(models.User.objects.get(username='test'), settings.AUTHENTICATION_BACKENDS[0])

    def test_invoices(self):
        address = reverse('invoices')
        response = self.client.get(address)
        self.assertContains(response, '<td>10. října 2010</td>', html=True)


@override_settings(
    SITE_ID=2,
)
class BaseViewsTests(ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users']

    def setUp(self):
        self.client = Client(HTTP_HOST="testing-campaign.testserver")
        self.client.force_login(models.User.objects.get(username='test'), settings.AUTHENTICATION_BACKENDS[0])

    @patch('slumber.API')
    def test_registration_access(self, slumber_api):
        slumber_instance = slumber_api.return_value
        slumber_instance.feed.get = {}
        address = reverse('profil')
        response = self.client.get(address)
        self.assertRedirects(response, reverse('typ_platby'))

    def test_chaining(self):
        util.rebuild_denorm_models(models.Team.objects.filter(pk__in=(1, 4)))
        denorm.flush()
        kwargs = {
            'app': 'dpnk',
            'model': 'Team',
            'manager': 'team_in_campaign_testing-campaign',
            'field': 'subsidiary',
            'foreign_key_app_name': 'dpnk',
            'foreign_key_model_name': 'Subsidiary',
            'foreign_key_field_name': 'company',
            'value': '1',
        }
        address = reverse('chained_filter', kwargs=kwargs)
        response = self.client.get(address)
        self.assertJSONEqual(
            response.content.decode(),
            [{'value': 4, 'display': 'Empty team ()'}, {'value': 1, 'display': 'Testing team 1 (Nick, Testing User 1, Registered User 1)'}],
        )


class PaymentTypeViewTests(ViewsLogon):
    def test_dpnk_payment_type(self):
        post_data = {
            'payment_type': 'company',
            'next': 'Next',
        }
        models.Payment.objects.all().delete()
        denorm.flush()
        response = self.client.post(reverse('typ_platby'), post_data, follow=True)
        self.assertRedirects(response, reverse("registration_uncomplete"))
        self.assertEquals(models.Payment.objects.get().pay_type, 'fc')

    def test_dpnk_payment_type_no_t_shirt(self):
        post_data = {
            'payment_type': 'company',
            'next': 'Next',
        }
        models.Payment.objects.all().delete()
        ua = models.UserAttendance.objects.get(pk=1115)
        ua.t_shirt_size = None
        ua.save()
        denorm.flush()
        response = self.client.post(reverse('typ_platby'), post_data, follow=True)
        self.assertContains(response, "Před tím, než zaplatíte startovné, musíte mít vybrané triko", status_code=403)

    def test_dpnk_payment_type_without_company_admin(self):
        post_data = {
            'payment_type': 'company',
            'next': 'Next',
        }
        models.Payment.objects.all().delete()
        models.CompanyAdmin.objects.all().delete()
        denorm.flush()
        response = self.client.post(reverse('typ_platby'), post_data)
        self.assertContains(response, "Váš zaměstnavatel Testing company nemá zvoleného koordinátora organizace.")

        post_data['payment_type'] = 'coupon'
        response = self.client.post(reverse('typ_platby'), post_data, follow=True)
        self.assertRedirects(response, reverse("discount_coupon"))
        self.assertContains(response, "<h2>Uplatnit slevový voucher</h2>", html=True)

    def test_dpnk_payment_type_pay_admin(self):
        post_data = {
            'payment_type': 'pay',
            'next': 'Next',
        }
        models.Payment.objects.all().delete()
        models.CompanyAdmin.objects.all().delete()
        denorm.flush()
        response = self.client.post(reverse('typ_platby'), post_data)
        print_response(response)
        self.assertContains(
            response,
            "Pokud jste se dostali sem, tak to může být způsobené tím, že používáte zastaralý prohlížeč nebo máte vypnutý JavaScript.",
            status_code=500,
        )


class DistanceTests(TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'trips']

    def test_distance(self):
        trips = models.Trip.objects.all()
        distance = views.distance_all_modes(trips)
        self.assertEquals(
            distance,
            {
                'distance__sum': 10.3,
                'distance_bicycle': 5.3,
                'distance_foot': 5.0,
                'count__sum': 2,
                'count_bicycle': 1,
                'count_foot': 1,
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class CompetitionResultsViewTests(ClearCacheMixin, DenormMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches', 'company_competition', 'test_results_data', 'trips']

    def test_dpnk_competition_results_unknown(self):
        address = reverse('competition_results', kwargs={'competition_slug': 'unexistent_competition'})
        response = self.client.get(address)
        self.assertContains(response, "Tuto soutěž v systému nemáme.")

    def test_dpnk_competition_results_vykonnost_tymu(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        models.Competition.objects.get(slug="vykonnost-tymu").recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'vykonnost-tymu'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Výkonnost týmů:")
        self.assertContains(
            response,
            '<th scope="column" id=result_divident>Po&shy;čet za&shy;po&shy;čí&shy;ta&shy;ných ki&shy;lo&shy;me&shy;trů</th>',
            html=True,
        )

    def test_dpnk_competition_results_quest_not_finished(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        competition = models.Competition.objects.filter(slug="quest")
        actions.normalize_questionnqire_admissions(None, None, competition)
        competition.get().recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'quest'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Dotazník:")
        self.assertContains(response, "Výsledky této soutěže se nezobrazují")

    def test_dpnk_competition_results_TF(self):
        address = reverse('competition_results', kwargs={'competition_slug': 'TF'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Team frequency:")
