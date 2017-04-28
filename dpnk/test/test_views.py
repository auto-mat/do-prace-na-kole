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
from collections import OrderedDict

from unittest.mock import ANY, MagicMock, call, patch

from PyPDF2 import PdfFileReader

import createsend

import denorm

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import Client, RequestFactory, TestCase
from django.test.utils import override_settings

from dpnk import actions, mailing, models, util, views
from dpnk.test.util import ClearCacheMixin, DenormMixin
from dpnk.test.util import print_response  # noqa

from model_mommy import mommy

from rest_framework.authtoken.models import Token

import settings

from t_shirt_delivery.models import PackageTransaction

from .mommy_recipes import CampaignRecipe, UserAttendanceRecipe, testing_campaign


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class ViewsLogon(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches']

    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.testserver")
        self.client.force_login(models.User.objects.get(username='test'), settings.AUTHENTICATION_BACKENDS[0])
        util.rebuild_denorm_models(models.Team.objects.filter(pk=1))
        util.rebuild_denorm_models(models.UserAttendance.objects.filter(pk__in=[1115, 2115]))
        self.user_attendance = models.UserAttendance.objects.get(pk=1115)


@override_settings(
    PAYU_POS_ID="123321"
)
class CompetitionsViewTests(ViewsLogon):
    def test_competition_rules(self):
        address = reverse('competition-rules-city', kwargs={'city_slug': "testing-city"})
        response = self.client.get(address)
        self.assertContains(response, "Do práce na kole - Pravidla soutěží - Testing city")
        self.assertContains(response, "Competition vykonnostr rules")
        self.assertContains(response, "soutěž na vzdálenost jednotlivců  ve městě Testing city")
        self.assertContains(response, "soutěž na vzdálenost týmů  ve městě Testing city pro muže")

    def test_competition_results(self):
        address = reverse('competition-results-city', kwargs={'city_slug': "testing-city"})
        response = self.client.get(address)
        self.assertContains(response, "Do práce na kole - Výsledky soutěží - Testing city")
        self.assertContains(response, "soutěž na vzdálenost jednotlivců  ve městě Testing city")

    def test_payment(self):
        address = reverse('payment')
        response = self.client.get(address)
        self.assertContains(response, '<input type="hidden" name="amount" value="12000">', html=True)
        self.assertContains(response, '<input type="hidden" name="pos_id" value="123321">', html=True)
        self.assertContains(response, '<input type="hidden" name="order_id" value="1128-1">', html=True)
        self.assertContains(response, '<input type="hidden" name="client_ip" value="0.0.0.0">', html=True)

    def test_payment_http_x_forwarded_for(self):
        """ Test in case, when IP is being delivered through HTTP_X_FORWARDED_FOR """
        address = reverse('payment')
        response = self.client.get(address, HTTP_X_FORWARDED_FOR="123.123.123.123")
        self.assertContains(response, '<input type="hidden" name="client_ip" value="123.123.123.123">', html=True)

    def test_payment_http_x_forwarded_for_proxy(self):
        """ Test in case, when IP is being delivered through HTTP_X_FORWARDED_FOR and the client is behid proxy """
        address = reverse('payment')
        response = self.client.get(address, HTTP_X_FORWARDED_FOR="unknown, 123.123.123.123")
        self.assertContains(response, '<input type="hidden" name="client_ip" value="123.123.123.123">', html=True)

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
        self.assertContains(response, 'Po koordinátorovi vaší organizace na e-mailové adrese')
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


@override_settings(
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class PaymentTypeViewTests(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.example.com", HTTP_REFERER="test-referer")
        self.campaign = testing_campaign
        t_shirt_size = mommy.make(
            "TShirtSize",
            campaign=self.campaign,
            name="Foo t-shirt-size",
        )
        mommy.make(
            "price_level.PriceLevel",
            takes_effect_on=datetime.date(year=2010, month=2, day=1),
            price=100,
            pricable=self.campaign,
        )
        mommy.make(
            "dpnk.Phase",
            phase_type="payment",
            date_from="2010-1-1",
            date_to="2020-1-1",
            campaign=self.campaign,
        )
        self.user_attendance = UserAttendanceRecipe.make(
            campaign=self.campaign,
            t_shirt_size=t_shirt_size,
            team__name="Foo team",
            team__subsidiary__company__name="Testing company",
            team__campaign=self.campaign,
        )
        self.client.force_login(self.user_attendance.userprofile.user, settings.AUTHENTICATION_BACKENDS[0])

    def test_dpnk_payment_type_with_discount_coupon(self):
        self.user_attendance.discount_coupon = mommy.make(
            "DiscountCoupon",
            discount=100,
            coupon_type__name="Foo coupon type",
        )
        self.user_attendance.save()
        response = self.client.get(reverse('typ_platby'))
        self.assertContains(
            response,
            '<div class="alert alert-danger">Již máte účastnický poplatek zaplacen. Pokračujte na <a href="/cs/">zadávání jízd</a>.</div>',
            html=True,
            status_code=403,
        )

    def test_dpnk_payment_type_company(self):
        mommy.make(
            "CompanyAdmin",
            administrated_company=self.user_attendance.team.subsidiary.company,
            userprofile__user__email="foo@email.com",
            company_admin_approved='approved',
            campaign=self.campaign,
        )
        post_data = {
            'payment_type': 'company',
            'next': 'Next',
        }
        response = self.client.post(reverse('typ_platby'), post_data, follow=True)
        self.assertRedirects(response, reverse("upravit_profil"))
        self.assertContains(
            response,
            '<div class="alert alert-warning">Platbu ještě musí schválit koordinátor vaší organizace <a href="mailto:foo@email.com">foo@email.com</a></div>',
            html=True,
        )
        self.assertEquals(models.Payment.objects.get().pay_type, 'fc')

    def test_dpnk_payment_type_no_t_shirt(self):
        post_data = {
            'payment_type': 'company',
            'next': 'Next',
        }
        self.user_attendance.t_shirt_size = None
        self.user_attendance.save()
        response = self.client.post(reverse('typ_platby'), post_data, follow=True)
        self.assertContains(response, "Před tím, než zaplatíte účastnický poplatek, musíte mít vybrané triko", status_code=403)

    def test_dpnk_payment_type_without_company_admin(self):
        post_data = {
            'payment_type': 'company',
            'next': 'Next',
        }
        response = self.client.post(reverse('typ_platby'), post_data)
        self.assertContains(response, "Váš zaměstnavatel Testing company nemá zvoleného firemního koordinátora.")

    def test_dpnk_payment_type_discount_coupon(self):
        post_data = {
            'payment_type': 'coupon',
            'next': 'Next',
        }
        response = self.client.post(reverse('typ_platby'), post_data, follow=True)
        self.assertRedirects(response, reverse("discount_coupon"))
        self.assertContains(response, "<h2>Uplatnit slevový voucher</h2>", html=True)

    @patch('dpnk.views.logger')
    def test_dpnk_payment_type_pay_admin(self, mock_logger):
        post_data = {
            'payment_type': 'pay',
            'next': 'Next',
        }
        response = self.client.post(reverse('typ_platby'), post_data)
        self.assertContains(
            response,
            "Pokud jste se dostali sem, tak to může být způsobené tím, že používáte zastaralý prohlížeč nebo máte vypnutý JavaScript.",
            status_code=500,
        )
        mock_logger.error.assert_called_with("Wrong payment type", extra={'request': ANY, 'payment_type': 'pay'})


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

    @patch('dpnk.views.logger')
    def test_dpnk_competition_results_unknown(self, mock_logger):
        address = reverse('competition_results', kwargs={'competition_slug': 'unexistent_competition'})
        response = self.client.get(address)
        mock_logger.exception.assert_called_with("Unknown competition", extra={'slug': 'unexistent_competition', 'request': ANY})
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


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
    SSLIFY_ADMIN_DISABLE=True,
)
class ViewsTests(DenormMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches', 'company_competition']

    def setUp(self):
        super().setUp()
        util.rebuild_denorm_models(models.Team.objects.filter(pk=1))
        self.client = Client(HTTP_HOST="testing-campaign.testserver")

    def test_login_view(self):
        address = reverse('login')
        response = self.client.get(address)
        self.assertContains(response, "E-mail (uživatelské jméno)")

        address = reverse('login', kwargs={'initial_email': "test@test.cz"})
        response = self.client.get(address)
        self.assertContains(response, "E-mail (uživatelské jméno)")
        self.assertContains(response, "test@test.cz")

    def test_admin_views_competition(self):
        self.client.force_login(models.User.objects.get(username='admin'), settings.AUTHENTICATION_BACKENDS[0])
        response = self.client.get(reverse("admin:dpnk_competition_add"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="id_competitor_type"')

        response = self.client.get(reverse("admin:dpnk_competition_change", args=[3]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="id_competitor_type"')

    def test_dpnk_views_no_login(self):
        address = reverse('registrace')
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)

    def test_competitor_counts(self):
        address = reverse('competitor_counts')
        for payment in models.Payment.objects.all():
            payment.status = models.Status.DONE
            payment.save()
        util.rebuild_denorm_models(models.Team.objects.filter(pk=1))
        util.rebuild_denorm_models(models.UserAttendance.objects.filter(pk=1115))
        response = self.client.get(address)
        self.assertContains(response, "<tr><td>Testing city</td><td>2</td></tr>", html=True)
        self.assertContains(response, "<tr><td>bez vybraného města</td><td>0</td></tr>", html=True)
        self.assertContains(response, "<tr><th>celkem</th><th>2</th></tr>", html=True)

    def test_dpnk_company_admin_registration(self):
        address = reverse('register_admin')
        post_data = {
            'email': 'testadmin@test.cz',
            'password1': 'test11',
            'password2': 'test11',
            'motivation_company_admin': 'some motivation',
            'telephone': 123456789,
            'first_name': 'Company',
            'last_name': 'Admin',
            'administrated_company': 2,
            'campaign': 339,
            'will_pay_opt_in': True,
            'personal_data_opt_in': True,
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertRedirects(response, reverse('company_structure'))
        user = models.User.objects.get(email='testadmin@test.cz')
        self.assertEquals(user.get_full_name(), "Company Admin")
        self.assertEquals(models.UserProfile.objects.get(user=user).telephone, '123456789')
        self.assertEquals(models.CompanyAdmin.objects.get(userprofile=user.userprofile).administrated_company.pk, 2)
        self.assertEqual(len(mail.outbox), 2)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['testadmin@test.cz'])
        self.assertEqual(str(msg.subject), 'Testing campaign - firemní koordinátor - schválení správcovství organizace')
        msg = mail.outbox[1]
        self.assertEqual(msg.recipients(), ['testadmin@test.cz'])
        self.assertEqual(str(msg.subject), 'Testing campaign - firemní koordinátor - potvrzení registrace')

    def test_dpnk_company_admin_registration_existing(self):
        user = models.User.objects.get(username='test1')
        models.CompanyAdmin.objects.create(
            administrated_company_id=2,
            userprofile=user.userprofile,
            campaign_id=339,
            company_admin_approved='approved',
        )
        address = reverse('register_admin')
        post_data = {
            'administrated_company': 2,
            'campaign': 339,
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(response, "Tato organizace již má svého firemního koordinátora.")

    def test_dpnk_registration(self):
        address = reverse('registrace')
        post_data = {
            'email': 'test1@test.cz',
            'password1': 'test11',
            'password2': 'test11',
        }
        response = self.client.post(address, post_data)
        self.assertRedirects(response, reverse('upravit_profil'))
        user = models.User.objects.get(email='test1@test.cz')
        self.assertNotEquals(user, None)
        self.assertNotEquals(models.UserProfile.objects.get(user=user), None)
        self.assertNotEquals(models.UserAttendance.objects.get(userprofile__user=user), None)

    def test_dpnk_registration_access(self):
        address = reverse('registration_access')
        response = self.client.get(address)
        self.assertContains(response, "E-mail (uživatelské jméno)")
        post_data = {
            'email': 'test@test.cz',
        }
        response = self.client.post(address, post_data)
        self.assertRedirects(response, reverse('login', kwargs={"initial_email": "test@test.cz"}))

    def test_dpnk_registration_access_email_unknown(self):
        address = reverse('registration_access')
        post_data = {
            'email': 'test1@test.cz',
        }
        response = self.client.post(address, post_data)
        self.assertRedirects(response, reverse('registrace', kwargs={"initial_email": "test1@test.cz"}))

    def test_dpnk_registration_email_used(self):
        address = reverse('registrace')
        post_data = {
            'email': 'test@test.cz',
            'password1': 'test11',
            'password2': 'test11',
        }
        response = self.client.post(address, post_data)
        self.assertContains(response, "Tato e-mailová adresa se již používá.")

    @patch('slumber.API')
    def test_dpnk_userattendance_creation(self, slumber_api):
        slumber_api.feed.get = {}
        self.client.force_login(models.User.objects.get(username='user_without_attendance'), settings.AUTHENTICATION_BACKENDS[0])
        address = reverse('profil')
        response = self.client.get(address)
        self.assertRedirects(response, reverse('upravit_profil'))
        user_attendance = models.UserAttendance.objects.length().get(userprofile__user__username='user_without_attendance', campaign__pk=339)
        self.assertEqual(user_attendance.userprofile.user.pk, 1041)
        self.assertEqual(user_attendance.get_distance(), 156.9)

    def test_password_recovery(self):
        address = reverse('password_reset')
        post_data = {
            'email': 'test@test.cz',
        }
        response = self.client.post(address, post_data)
        self.assertRedirects(response, reverse('password_reset_done'))
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test@test.cz'])
        self.assertEqual(msg.subject, 'Zapomenuté heslo Do práce na kole')
        self.assertTrue('http://testing-campaign.testserver/cs/zapomenute_heslo/zmena/' in msg.body)

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=10, day=1),
    )
    def test_dpnk_registration_out_of_phase(self):
        address = reverse('registrace')
        response = self.client.get(address)
        self.assertEqual(response.status_message, "out_of_phase")
        self.assertEqual(response.status_code, 403)

    def test_dpnk_mailing_list(self):
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        Token.objects.filter(user=user_attendance.userprofile.user).update(key='d201a3c9e88ecd433fdbbc3a2e451cbd3f80c4ba')
        ret_mailing_id = "344ass"
        createsend.Subscriber.add = MagicMock(return_value=ret_mailing_id)
        mailing.add_or_update_user_synchronous(user_attendance)
        custom_fields = [
            OrderedDict((('Key', 'Mesto'), ('Value', 'testing-city'))),
            OrderedDict((('Key', 'Firemni_spravce'), ('Value', True))),
            OrderedDict((('Key', 'Stav_platby'), ('Value', None))),
            OrderedDict((('Key', 'Aktivni'), ('Value', True))),
            OrderedDict((('Key', 'Auth_token'), ('Value', 'd201a3c9e88ecd433fdbbc3a2e451cbd3f80c4ba'))),
            OrderedDict((('Key', 'Id'), ('Value', 1128))),
            OrderedDict((('Key', 'Novacek'), ('Value', False))),
            OrderedDict((('Key', 'Kampan'), ('Value', 'testing-campaign'))),
            OrderedDict((('Key', 'Vstoupil_do_souteze'), ('Value', False))),
            OrderedDict((('Key', 'Pocet_lidi_v_tymu'), ('Value', 3))),
            OrderedDict((('Key', 'Povoleni_odesilat_emaily'), ('Value', True))),
        ]
        createsend.Subscriber.add.assert_called_once_with('12345abcde', 'test@test.cz', 'Testing User 1', custom_fields, True)
        self.assertEqual(user_attendance.userprofile.mailing_id, ret_mailing_id)
        self.assertEqual(user_attendance.userprofile.mailing_hash, '2ddd65f5dc0ca3755885e23fefc956f1')

        createsend.Subscriber.update = MagicMock()
        mailing.add_or_update_user_synchronous(user_attendance)
        self.assertFalse(createsend.Subscriber.update.called)
        self.assertEqual(user_attendance.userprofile.mailing_hash, '2ddd65f5dc0ca3755885e23fefc956f1')

        custom_fields[0] = OrderedDict((('Key', 'Mesto'), ('Value', 'other-city')))
        user_attendance.team.subsidiary.city = models.City.objects.get(slug="other-city")
        user_attendance.team.subsidiary.save()
        createsend.Subscriber.get = MagicMock()
        createsend.Subscriber.update = MagicMock()
        mailing.add_or_update_user_synchronous(user_attendance)
        createsend.Subscriber.get.assert_called_once_with('12345abcde', ret_mailing_id)
        createsend.Subscriber.update.assert_called_once_with('test@test.cz', 'Testing User 1', custom_fields, True)
        self.assertEqual(user_attendance.userprofile.mailing_hash, '264683d74013ab0fa8619ba7bbdefec6')

        user_attendance.userprofile.user.is_active = False
        user_attendance.userprofile.user.save()
        createsend.Subscriber.get = MagicMock()
        createsend.Subscriber.delete = MagicMock(return_value=ret_mailing_id)
        mailing.add_or_update_user_synchronous(user_attendance)
        createsend.Subscriber.get.assert_called_once_with('12345abcde', ret_mailing_id)
        createsend.Subscriber.delete.assert_called_once_with()
        self.assertEqual(user_attendance.userprofile.mailing_id, ret_mailing_id)
        self.assertEqual(user_attendance.userprofile.mailing_hash, None)


@override_settings(
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class RegistrationViewTests(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.example.com")

    def test_dpnk_registration_token(self):
        mommy.make(
            "Team",
            invitation_token="token123213",
            campaign=testing_campaign,
            id=1,
        )
        kwargs = {
            "token": "token123213",
            'initial_email': 'test1@test.cz',
        }
        address = reverse('registrace', kwargs=kwargs)
        post_data = {
            'email': 'test1@test.cz',
            'password1': 'test11',
            'password2': 'test11',
        }
        response = self.client.post(address, post_data)
        self.assertRedirects(response, reverse('upravit_profil'))
        user = models.User.objects.get(email='test1@test.cz')
        self.assertNotEquals(user, None)
        self.assertNotEquals(models.UserProfile.objects.get(user=user), None)
        ua = models.UserAttendance.objects.get(userprofile__user=user)
        self.assertNotEquals(ua, None)
        self.assertEquals(ua.team.pk, 1)

    def test_dpnk_registration_token_team_full(self):
        mommy.make(
            "Team",
            invitation_token="token123213",
            campaign=CampaignRecipe.make(max_team_members=0, slug="testing-campaign"),
            id=1,
        )
        kwargs = {
            "token": "token123213",
            'initial_email': 'test1@test.cz',
        }
        address = reverse('registrace', kwargs=kwargs)
        post_data = {
            'email': 'test1@test.cz',
            'password1': 'test11',
            'password2': 'test11',
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertRedirects(response, reverse('upravit_profil'))
        self.assertContains(
            response,
            '<div class="alert alert-danger">Tým do kterého jste byli pozváni je již plný, budete si muset vybrat nebo vytvořit jiný tým.</div>',
            html=True,
        )
        user = models.User.objects.get(email='test1@test.cz')
        ua = models.UserAttendance.objects.get(userprofile__user=user)
        self.assertEquals(ua.team, None)


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class RequestFactoryViewTests(ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users']

    def setUp(self):
        self.factory = RequestFactory()
        util.rebuild_denorm_models(models.Team.objects.filter(pk=1))
        self.user_attendance = models.UserAttendance.objects.get(pk=1115)
        self.session_id = "2075-1J1455206457"
        self.trans_id = "2055"

    def test_questionnaire_view(self):
        kwargs = {'questionnaire_slug': 'quest'}
        address = reverse('questionnaire', kwargs=kwargs)
        request = self.factory.get(address)
        request.user = self.user_attendance.userprofile.user
        request.user_attendance = self.user_attendance
        request.subdomain = "testing-campaign"
        request.resolver_match = {"url_name": "questionnaire"}
        response = views.QuestionnaireView.as_view()(request, **kwargs)
        self.assertContains(response, 'yes')
        self.assertContains(response, 'Question text')
        self.assertContains(response, '<p>Given comment</p>')

        post_data = {
            "question-2-choices": 1,
            "question-3-comment": 12,
            "question-4-comment": "http://www.asdf.cz",
            'submit': 'Odeslat',

        }
        request = self.factory.post(address, post_data)
        request.user = self.user_attendance.userprofile.user
        request.user_attendance = self.user_attendance
        request.subdomain = "testing-campaign"
        response = views.QuestionnaireView.as_view()(request, **kwargs)
        self.assertEquals(response.url, reverse("competitions"))

    @patch('dpnk.views.logger')
    def test_questionnaire_view_unknown(self, mock_logger):
        kwargs = {'questionnaire_slug': 'quest1'}
        address = reverse('questionnaire', kwargs=kwargs)
        request = self.factory.get(address)
        request.user = self.user_attendance.userprofile.user
        request.user_attendance = self.user_attendance
        request.subdomain = "testing-campaign"
        request.resolver_match = {"url_name": "questionnaire"}
        response = views.QuestionnaireView.as_view()(request, **kwargs)
        mock_logger.exception.assert_called_with('Unknown questionaire', extra={'request': ANY, 'slug': 'quest1'})
        self.assertContains(response, 'Tento dotazník v systému nemáme.', status_code=401)

    def test_questionnaire_view_uncomplete(self):
        kwargs = {'questionnaire_slug': 'quest'}
        address = reverse('questionnaire', kwargs=kwargs)

        post_data = {
            "question-2-choices": 1,
            "question-3-comment": 12,
            "question-4-comment": "",
            'submit': 'Odeslat',

        }
        request = self.factory.post(address, post_data)
        request.user = self.user_attendance.userprofile.user
        request.user_attendance = self.user_attendance
        request.subdomain = "testing-campaign"
        response = views.QuestionnaireView.as_view()(request, **kwargs)
        self.assertContains(response, "Odpověď na jednu otázku obsahuje chybu. Prosím opravte tuto chybu a znovu stiskněte tlačítko Odeslat.")
        self.assertContains(response, '<a href="%sDSC00002.JPG">DSC00002.JPG</a>' % settings.MEDIA_URL, html=True)

    @override_settings(
        FAKE_DATE=datetime.date(year=2016, month=11, day=20),
    )
    def test_questionnaire_view_late(self):
        kwargs = {'questionnaire_slug': 'quest'}
        address = reverse('questionnaire', kwargs=kwargs)

        post_data = {}
        request = self.factory.post(address, post_data)
        request.user = self.user_attendance.userprofile.user
        request.user_attendance = self.user_attendance
        request.subdomain = "testing-campaign"
        response = views.QuestionnaireView.as_view()(request, **kwargs)
        self.assertContains(response, "Soutěž již nelze vyplňovat")


class ViewsTestsLogon(ViewsLogon):
    def test_dpnk_team_view(self):
        response = self.client.get(reverse('zmenit_tym'))
        self.assertNotContains(response, "Testing company")
        self.assertContains(response, "Testing team 1")

    def test_dpnk_team_view_no_payment(self):
        models.Payment.objects.all().delete()
        denorm.flush()
        response = self.client.get(reverse('zmenit_tym'))
        self.assertContains(response, "Testing company")
        self.assertContains(response, "Testing team 1")
        models.Payment.objects.all().delete()

    def test_ajax_select(self):
        address = "/selectable/dpnk-companylookup/??term=tést"
        response = self.client.get(address)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "data": [
                    {"value": "Testing company", "label": "Testing company", "id": 1},
                    {"value": "Testing company without admin", "label": "Testing company without admin", "id": 2},
                ],
                "meta": {
                    "more": "Show more results",
                    "page": 1,
                    "term": "",
                    "limit": 25,
                },
            },
        )

    def test_dpnk_team_invitation_no_last_team(self):
        token = self.user_attendance.team.invitation_token
        self.user_attendance.team = None
        self.user_attendance.save()
        email = self.user_attendance.userprofile.user.email
        address = reverse('zmenit_tym', kwargs={'token': token, 'initial_email': email})
        response = self.client.get(address)
        self.assertContains(response, "<div>Přejete si být zařazeni do týmu Testing team 1 (Nick, Testing User 1, Registered User 1)?</div>", html=True)

    def test_dpnk_team_invitation_admission_payed(self):
        email = self.user_attendance.userprofile.user.email
        address = reverse('zmenit_tym', kwargs={'token': "token123215", 'initial_email': email})
        response = self.client.get(address)
        self.assertContains(response, '<div class="alert alert-danger">Již máte zaplaceno, nemůžete měnit tým mimo svoji pobočku.</div>', html=True)

    def test_dpnk_team_invitation_full(self):
        self.user_attendance.campaign.max_team_members = 1
        self.user_attendance.campaign.save()
        token = "token123215"
        team = models.Team.objects.get(invitation_token=token)
        team.save()
        denorm.flush()
        email = self.user_attendance.userprofile.user.email
        address = reverse('zmenit_tym', kwargs={'token': token, 'initial_email': email})
        response = self.client.get(address)
        self.assertContains(
            response,
            '<div class="alert alert-danger">Tým do kterého jste byli pozváni je již plný, budete si muset vybrat nebo vytvořit jiný tým.</div>',
            html=True,
        )

    def test_dpnk_team_invitation_team_last_campaign(self):
        models.Payment.objects.all().delete()
        denorm.flush()
        email = self.user_attendance.userprofile.user.email
        address = reverse('zmenit_tym', kwargs={'token': "token123214", 'initial_email': email})
        response = self.client.get(address)
        self.assertContains(
            response,
            '<div class="alert alert-danger">'
            'Přihlašujete se do týmu ze špatné kampaně (pravděpodobně z minulého roku).'
            '</div>',
            html=True,
        )

    def test_dpnk_team_invitation(self):
        token = self.user_attendance.team.invitation_token
        email = self.user_attendance.userprofile.user.email
        address = reverse('zmenit_tym', kwargs={'token': token, 'initial_email': email})
        response = self.client.get(address)
        self.assertContains(response, "<h2>Pozvánka do týmu</h2>", html=True)

        post_data = {
            "question": "on",
            "submit": "Odeslat",
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(response, "Vybrat/změnit tým")

    def test_dpnk_team_invitation_bad_email(self):
        token = self.user_attendance.team.invitation_token
        response = self.client.get(reverse('zmenit_tym', kwargs={'token': token, 'initial_email': 'invitation_test@email.com'}), follow=True)
        self.assertRedirects(response, "/cs/login/invitation_test@email.com/?next=/cs/tym/token123213/invitation_test@email.com/")
        self.assertContains(response, "invitation_test@email.com")

    def test_dpnk_team_invitation_unknown_team(self):
        response = self.client.get(reverse('zmenit_tym', kwargs={'token': 'asdf', 'initial_email': 'invitation_test@email.com'}))
        self.assertContains(response, "Tým nenalezen", status_code=403)

    @patch('slumber.API')
    def test_dpnk_team_view_choose(self, slumber_api):
        m = MagicMock()
        m.feed.get.return_value = []
        slumber_api.return_value = m
        PackageTransaction.objects.all().delete()
        models.Payment.objects.all().delete()
        util.rebuild_denorm_models(models.Team.objects.filter(pk=3))
        self.user_attendance.save()
        response = self.client.get(reverse('zmenit_tym'))
        self.assertContains(
            response,
            '<label for="id_company-name" class="control-label  requiredField">'
            'Název organizace'
            '<span class="asteriskField">*</span>'
            '</label>',
            html=True,
        )
        self.assertContains(response, "id_subsidiary")

        post_data = {
            'company_1': '1',
            'subsidiary': '1',
            'team': '3',
            'next': 'Next',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)
        self.assertRedirects(response, reverse("zmenit_triko"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(models.UserAttendance.objects.get(pk=1115).approved_for_team, "undecided")

    def test_dpnk_team_view_choose_empty_team(self):
        util.rebuild_denorm_models(models.Team.objects.all())
        PackageTransaction.objects.all().delete()
        models.Payment.objects.all().delete()
        self.user_attendance.approved_for_team = "undecided"
        self.user_attendance.save()
        post_data = {
            'company_1': '1',
            'subsidiary': '1',
            'team': '4',
            'prev': 'Prev',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)
        self.assertRedirects(response, reverse("upravit_profil"))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(models.UserAttendance.objects.get(pk=1115).approved_for_team, "approved")

    def test_dpnk_update_profile_view(self):
        util.rebuild_denorm_models(models.Team.objects.filter(pk=2))
        post_data = {
            'sex': 'male',
            'first_name': 'Testing',
            'last_name': 'Name',
            'nickname': 'My super nick',
            'mailing_opt_in': 'True',
            'email': 'testing@email.cz',
            'language': 'cs',
            'telephone': '111222333',
            'dont_show_name': True,
            'personal_data_opt_in': 'True',
            'next': 'Další',
        }
        address = reverse('upravit_profil')
        response = self.client.post(address, post_data, follow=True)
        self.assertRedirects(response, reverse("zmenit_tym"))
        self.assertContains(response, "My super nick")

    def test_dpnk_update_profile_view_no_nick(self):
        post_data = {
            'dont_show_name': True,
            'next': 'Další',
        }
        address = reverse('upravit_profil')
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(response, "Pokud si nepřejete zobrazovat své jméno, zadejte, co se má zobrazovat místo něj")

    def test_dpnk_update_profile_view_no_sex(self):
        post_data = {
            'sex': 'unknown',
            'next': 'Další',
        }
        address = reverse('upravit_profil')
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(response, "Zadejte pohlaví")

    def test_dpnk_update_profile_view_email_exists(self):
        post_data = {
            'email': 'test2@test.cz',
            'next': 'Další',
        }
        address = reverse('upravit_profil')
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(response, "Tento e-mail již je v našem systému zanesen.")

    @patch('dpnk.models.team.logger')
    def test_dpnk_team_view_choose_team_full(self, mock_logger):
        campaign = models.Campaign.objects.get(pk=339)
        campaign.max_team_members = 0
        campaign.save()
        post_data = {
            'company': '1',
            'subsidiary': '1',
            'team': '3',
            'next': 'Next',
        }
        PackageTransaction.objects.all().delete()
        models.Payment.objects.all().delete()
        self.user_attendance.save()
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)
        mock_logger.error.assert_called_with("Too many members in team", extra={'team': ANY})
        self.assertContains(response, "Tento tým již má plný počet členů")

    @patch('dpnk.forms.logger')
    def test_dpnk_team_view_choose_team_out_of_campaign(self, mock_logger):
        post_data = {
            'company_1': '1',
            'subsidiary': '2',
            'team': '2',
            'next': 'Next',
        }
        PackageTransaction.objects.all().delete()
        models.Payment.objects.all().delete()
        self.user_attendance.save()
        response = self.client.post(reverse('zmenit_tym'), post_data)
        assert mock_logger.error.mock_calls == [
            call("Team not in campaign", extra={'request': ANY, 'team': ANY, 'subdomain': ANY}),
            call("Subsidiary in city that doesn't belong to this campaign", extra={'request': ANY, 'subsidiary': ANY}),
        ]
        self.assertContains(response, "Zvolený tým není dostupný v aktuální kampani")

    def test_dpnk_team_view_choose_team_after_payment(self):
        post_data = {
            'company_1': '1',
            'subsidiary': '2',
            'team': '3',
            'next': 'Next',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data)
        self.assertContains(response, "Po zaplacení není možné měnit tým mimo pobočku")

    @patch('dpnk.forms.logger')
    def test_dpnk_team_view_choose_nonexistent_city(self, mock_logger):
        post_data = {
            'company_1': '1',
            'subsidiary': '2',
            'id_team_selected': 'on',
            'team-name': 'Testing team last campaign',
            'team-campaign': 339,
            'next': 'Next',
        }
        PackageTransaction.objects.all().delete()
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)
        mock_logger.error.assert_called_with("Subsidiary in city that doesn't belong to this campaign", extra={'request': ANY, 'subsidiary': ANY})
        self.assertContains(response, "Zvolená pobočka je registrována ve městě, které v aktuální kampani nesoutěží.")

    def test_dpnk_team_view_create(self):
        self.user_attendance.team = None
        self.user_attendance.save()
        response = self.client.get(reverse('zmenit_tym'))
        self.assertContains(response, "Testing team last campaign")
        post_data = {
            'company-name': 'Created company',
            'id_company_selected': 'on',
            'subsidiary-city': '1',
            'subsidiary-address_recipient': 'Created name',
            'subsidiary-address_street': 'Created street',
            'subsidiary-address_street_number': '99',
            'subsidiary-address_psc': '99 999',
            'subsidiary-address_city': 'Testing city',
            'id_subsidiary_selected': 'on',
            'team-name': 'Created team',
            'company_1': '1',
            'subsidiary': '1',
            'team-campaign': '339',
            'id_team_selected': 'on',
            'next': 'Další',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)

        self.assertRedirects(response, reverse("pozvanky"))
        self.assertContains(response, "Tým Created team úspěšně vytvořen")
        user = models.UserAttendance.objects.get(pk=1115)
        self.assertEquals(user.team.name, "Created team")
        self.assertEquals(user.team.subsidiary.address.street, "Created street")
        self.assertEquals(user.team.subsidiary.company.name, "Created company")
        self.assertEquals(models.UserAttendance.objects.get(pk=1115).approved_for_team, "approved")

    @patch('slumber.API')
    def company_payment(self, slumber_api, amount, amount_tax, beneficiary=False):
        slumber_instance = slumber_api.return_value
        slumber_instance.feed.get.return_value = [{"content": "Emission calculator description text"}]
        response = self.client.get(reverse('company_admin_pay_for_users'))
        self.assertContains(
            response,
            '<tr>'
            '<td>'
            '<input class="tableselectmultiple selectable-checkbox form-check-input" id="id_paing_for_0" name="paing_for" type="checkbox" value="2115" />'
            '</td>'
            '<td>%s</td>'
            '<td>Registered</td>'
            '<td>User 1</td>'
            '<td></td>'
            '<td>test-registered@test.cz</td>'
            '<td>Testing city</td>'
            '</tr>' % amount,
            html=True,
        )
        post_data = {
            'paing_for': '2115',
            'submit': 'Odeslat',
        }
        response = self.client.post(reverse('company_admin_pay_for_users'), post_data, follow=True)
        self.assertRedirects(response, reverse('company_admin_pay_for_users'))
        p = models.UserAttendance.objects.get(id=2115).representative_payment
        self.assertEquals(p.status, models.Status.COMPANY_ACCEPTS)

        response = self.client.get(reverse('invoices'))
        self.assertContains(response, "<td>Registered User 1</td>", html=True)
        self.assertContains(response, "<td>%i Kč</td>" % amount, html=True)

        post_data = {
            'create_invoice': 'on',
            'submit': 'Odeslat',
            'order_number': 1323575433,
        }
        if beneficiary:
            post_data['company_pais_benefitial_fee'] = "on"
        response = self.client.post(reverse('invoices'), post_data, follow=True)
        self.assertContains(response, "<td>Zaplacení nepotvrzeno</td>", html=True)
        self.assertRedirects(response, reverse('invoices'))
        p = models.UserAttendance.objects.get(id=2115).representative_payment
        self.assertEquals(p.status, 1006)
        self.assertEquals(p.invoice.total_amount, amount_tax)
        pdf = PdfFileReader(p.invoice.invoice_pdf)
        pdf_string = pdf.pages[0].extractText()
        self.assertTrue("2010D001" in pdf_string)
        self.assertTrue("Celkem s DPH: %s,-" % amount_tax in pdf_string)
        self.assertTrue("1323575433" in pdf_string)
        self.assertTrue("Testing company" in pdf_string)

    def test_company_payment_no_t_shirt_size(self):
        user_attendance = models.UserAttendance.objects.get(id=2115)
        user_attendance.t_shirt_size = None
        user_attendance.save()
        self.company_payment(amount=130.0, amount_tax=157)

    def test_company_payment_paid_t_shirt_size(self):
        user_attendance = models.UserAttendance.objects.get(id=2115)
        user_attendance.t_shirt_size_id = 2
        user_attendance.save()
        self.company_payment(amount=230.0, amount_tax=278)

    def test_company_payment(self):
        self.company_payment(amount=130.0, amount_tax=157)

    @override_settings(
        FAKE_DATE=datetime.date(year=2011, month=4, day=1),
    )
    def test_company_payment_late(self):
        self.company_payment(amount=230.0, amount_tax=278)

    def test_company_payment_beneficiary(self):
        self.company_payment(beneficiary=True, amount=130.0, amount_tax=544)

    def test_dpnk_team_view_no_team_set(self):
        post_data = {
            'company_1': '1',
            'subsidiary': '',
            'team': '',
            'next': 'Next',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data)
        self.assertContains(response, 'error_1_id_team')
        self.assertContains(response, 'var value = undefined;')

    def test_dpnk_team_approval(self):
        ua = models.UserAttendance.objects.get(pk=1015)
        ua.approved_for_team = 'undecided'
        ua.save()
        post_data = {
            'approve': 'approve-1015',
            'reason-1015': '',
        }
        response = self.client.post(reverse('team_members'), post_data)
        self.assertContains(response, 'Členství uživatele Nick v týmu Testing team 1 bylo odsouhlaseno.')

    def test_dpnk_team_denial(self):
        ua = models.UserAttendance.objects.get(pk=1015)
        ua.approved_for_team = 'undecided'
        ua.save()
        post_data = {
            'approve': 'deny-1015',
            'reason-1015': 'reason',
        }
        response = self.client.post(reverse('team_members'), post_data)
        self.assertContains(response, 'Členství uživatele Nick ve vašem týmu bylo zamítnuto')

    def test_dpnk_team_denial_no_message(self):
        ua = models.UserAttendance.objects.get(pk=1015)
        ua.approved_for_team = 'undecided'
        ua.save()
        post_data = {
            'approve': 'deny-1015',
        }
        response = self.client.post(reverse('team_members'), post_data)
        self.assertContains(response, 'Při zamítnutí člena týmu musíte vyplnit zprávu.')

    def test_dpnk_team_denial_no_message_team_full(self):
        ua = models.UserAttendance.objects.get(pk=1015)
        ua.approved_for_team = 'undecided'
        ua.save()
        campaign = models.Campaign.objects.get(pk=339)
        campaign.max_team_members = 2
        campaign.save()
        post_data = {
            'approve': 'approve-1015',
        }
        response = self.client.post(reverse('team_members'), post_data)
        self.assertContains(response, 'Tým je již plný, další člen již nemůže být potvrzen.')

    def test_dpnk_team_invitation_current_user(self):
        post_data = {
            'email1': 'test@email.cz',
            'submit': 'odeslat',
        }
        response = self.client.post(reverse('pozvanky'), post_data, follow=True)
        self.assertContains(response, 'Odeslána pozvánka uživateli Null User na e-mail test@email.cz')
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test@email.cz'])
        self.assertEqual(str(msg.subject), 'Testing campaign - potvrzení registrace')

    def test_dpnk_team_invitation_same_team(self):
        post_data = {
            'email1': 'test2@test.cz',
            'submit': 'odeslat',
        }
        response = self.client.post(reverse('pozvanky'), post_data, follow=True)
        self.assertContains(response, 'Uživatel Nick byl přijat do vašeho týmu.')
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test2@test.cz'])
        self.assertEqual(str(msg.subject), 'Testing campaign - potvrzení ověření členství v týmu')

    def test_dpnk_team_invitation_unknown(self):
        post_data = {
            'email1': 'test-unknown@email.cz',
            'submit': 'odeslat',
        }
        response = self.client.post(reverse('pozvanky'), post_data, follow=True)
        self.assertContains(response, 'Odeslána pozvánka na e-mail test-unknown@email.cz')
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test-unknown@email.cz'])
        self.assertEqual(str(msg.subject), 'Testing campaign - pozvánka do týmu')

    def test_dpnk_company_admin_application(self):
        util.rebuild_denorm_models(models.Team.objects.filter(pk=2))
        response = self.client.get(reverse('company_admin_application'))
        post_data = {
            'motivation_company_admin': 'Testing position',
            'will_pay_opt_in': True,
            'personal_data_opt_in': True,
            'submit': 'Odeslat',
        }
        response = self.client.post(reverse('company_admin_application'), post_data)
        self.assertRedirects(response, reverse('profil'), fetch_redirect_response=False)
        company_admin = models.CompanyAdmin.objects.get(userprofile__user__username='test')
        self.assertEquals(company_admin.motivation_company_admin, 'Testing position')

    def test_dpnk_company_admin_application_existing_admin(self):
        user = models.User.objects.get(username='test1')
        models.CompanyAdmin.objects.create(
            administrated_company=self.user_attendance.team.subsidiary.company,
            userprofile=user.userprofile,
            campaign=self.user_attendance.campaign,
            company_admin_approved='approved',
        )
        response = self.client.get(reverse('company_admin_application'))
        self.assertContains(
            response,
            '<div class="alert alert-danger">Vaše organizce již svého koordinátora má: Null User, Null User, Testing User.</div>',
            html=True,
        )

    def test_dpnk_company_admin_application_create(self):
        models.CompanyAdmin.objects.all().delete()
        response = self.client.get(reverse('company_admin_application'))
        self.assertContains(
            response,
            '<label for="id_motivation_company_admin" class="control-label  requiredField"> Pár vět o vaší pozici<span class="asteriskField">*</span> </label>',
            html=True,
        )


class ChangeTeamViewTests(TestCase):
    def setUp(self):
        self.client = Client(HTTP_HOST="testing-campaign.example.com", HTTP_REFERER="test-referer")
        self.campaign = testing_campaign
        self.team = mommy.make(
            "Team",
            campaign=self.campaign,
        )

    def test_dpnk_team_change_me_undecided(self):
        """ If I my team membership is undecided, I have to be able to leave the team """
        UserAttendanceRecipe.make(approved_for_team='approved', campaign=self.campaign, team=self.team)
        user_attendance = UserAttendanceRecipe.make(approved_for_team='undecided', campaign=self.campaign, team=self.team)
        self.team.save()
        self.client.force_login(user_attendance.userprofile.user, settings.AUTHENTICATION_BACKENDS[0])
        self.assertEquals(self.team.member_count, 1)
        self.assertEquals(self.team.unapproved_member_count, 1)
        response = self.client.get(reverse('zmenit_tym'))
        self.assertEquals(response.status_code, 200)

    def test_dpnk_team_undecided(self):
        """ If I am olny approved team member of team where all others are undicided, I can't leave the team """
        UserAttendanceRecipe.make(approved_for_team='undecided', campaign=self.campaign, team=self.team)
        user_attendance = UserAttendanceRecipe.make(approved_for_team='approved', campaign=self.campaign, team=self.team)
        self.team.save()
        self.client.force_login(user_attendance.userprofile.user, settings.AUTHENTICATION_BACKENDS[0])
        self.assertEquals(self.team.member_count, 1)
        self.assertEquals(self.team.unapproved_member_count, 1)
        response = self.client.get(reverse('zmenit_tym'))
        self.assertContains(
            response,
            "Nemůžete opustit tým, ve kterém jsou samí neschválení členové. "
            "Napřed někoho schvalte a pak změňte tým.",
            status_code=403,
        )

    def test_dpnk_team_change_alone_undecided(self):
        """ If I am in the team alone, I can leave the team if I am undecided """
        user_attendance = UserAttendanceRecipe.make(approved_for_team='undecided', campaign=self.campaign, team=self.team)
        self.team.save()
        self.client.force_login(user_attendance.userprofile.user, settings.AUTHENTICATION_BACKENDS[0])
        self.assertEquals(self.team.member_count, 0)
        self.assertEquals(self.team.unapproved_member_count, 1)
        response = self.client.get(reverse('zmenit_tym'))
        self.assertEquals(response.status_code, 200)

    def test_dpnk_team_change_alone_approved(self):
        """ If I am in the team alone, I can leave the team if I am approved """
        user_attendance = UserAttendanceRecipe.make(approved_for_team='approved', campaign=self.campaign, team=self.team)
        self.team.save()
        self.client.force_login(user_attendance.userprofile.user, settings.AUTHENTICATION_BACKENDS[0])
        self.assertEquals(self.team.member_count, 1)
        self.assertEquals(self.team.unapproved_member_count, 0)
        response = self.client.get(reverse('zmenit_tym'))
        self.assertEquals(response.status_code, 200)


class RegistrationMixinTests(ViewsLogon):
    def test_dpnk_registration_mixin_team_alone(self):
        for team_member in self.user_attendance.team.all_members():
            if team_member != self.user_attendance:
                team_member.team = None
                team_member.save()
        self.user_attendance.track = None
        self.user_attendance.save()
        denorm.flush()
        response = self.client.get(reverse('registration_uncomplete'))
        self.assertContains(response, "Jste sám/sama v týmu")
        self.assertContains(response, "Nemáte vyplněnou vaši typickou trasu ani vzdálenost do práce.")

    def test_dpnk_registration_unapproved_users(self):
        for team_member in self.user_attendance.team.all_members():
            if team_member != self.user_attendance:
                team_member.approved_for_team = 'undecided'
                team_member.save()
        self.user_attendance.track = None
        self.user_attendance.save()
        denorm.flush()
        response = self.client.get(reverse('registration_uncomplete'))
        self.assertContains(response, "Ve vašem týmu jsou neschválení členové")

    def test_dpnk_registration_unapproved(self):
        self.user_attendance.approved_for_team = 'undecided'
        self.user_attendance.save()
        self.user_attendance.track = None
        self.user_attendance.save()
        denorm.flush()
        response = self.client.get(reverse('registration_uncomplete'))
        self.assertNotContains(response, "Ve vašem týmu jsou neschválení členové")
        self.assertContains(response, "Vaši kolegové v týmu Testing team 1")

    def test_dpnk_registration_denied(self):
        self.user_attendance.approved_for_team = 'denied'
        self.user_attendance.save()
        self.user_attendance.track = None
        self.user_attendance.save()
        denorm.flush()
        response = self.client.get(reverse('registration_uncomplete'))
        self.assertContains(response, "Vaše členství v týmu bylo bohužel zamítnuto")

    def test_dpnk_registration_no_payment(self):
        self.user_attendance.track = None
        self.user_attendance.save()
        for payment in self.user_attendance.payments():
            payment.status = models.Status.NEW
            payment.save()
        denorm.flush()
        response = self.client.get(reverse('registration_uncomplete'))
        self.assertContains(response, "Vaše platba typu ORGANIZACE PLATÍ FAKTUROU ještě nebyla vyřízena.")

    @patch('slumber.API')
    def test_dpnk_registration_questionnaire(self, slumber_api):
        m = MagicMock()
        m.feed.get.return_value = []
        slumber_api.return_value = m
        response = self.client.get(reverse('profil'))
        self.assertContains(response, "Nezapomeňte vyplnit odpovědi v následujících soutěžích: <a href='/cs/otazka/quest/'>Dotazník</a>!")

    @patch('slumber.API')
    def test_dpnk_registration_vouchers(self, slumber_api):
        m = MagicMock()
        m.feed.get.return_value = [
            {
                "content": "Test content",
                "title": "Test title",
                "excerpt": "Test excerpt",
                "url": "Test url",
            },
        ]
        slumber_api.return_value = m
        models.Voucher.objects.create(user_attendance=self.user_attendance, token="1234")
        response = self.client.get(reverse('profil'))
        self.assertContains(response, "<h3>Vouchery</h3>", html=True)
        self.assertContains(response, "<tr> <td> ReKola </td> <td> 1234 </td> </tr>", html=True)

    @patch('slumber.API')
    def test_dpnk_registration_company_admin_undecided(self, slumber_api):
        m = MagicMock()
        m.feed.get.return_value = []
        slumber_api.return_value = m
        util.rebuild_denorm_models(models.Team.objects.filter(pk=2))
        ca = models.CompanyAdmin.objects.get(userprofile=self.user_attendance.userprofile, campaign_id=339)
        ca.company_admin_approved = 'undecided'
        ca.save()
        response = self.client.get(reverse('profil'))
        denorm.flush()
        self.assertContains(response, "Vaše žádost o funkci koordinátora organizace čeká na vyřízení.")

    @patch('slumber.API')
    def test_dpnk_registration_company_admin_decided(self, slumber_api):
        m = MagicMock()
        m.feed.get.return_value = []
        slumber_api.return_value = m
        util.rebuild_denorm_models(models.Team.objects.filter(pk=2))
        ca = models.CompanyAdmin.objects.get(userprofile=self.user_attendance.userprofile, campaign_id=339)
        ca.company_admin_approved = 'denied'
        ca.save()
        response = self.client.get(reverse('profil'))
        self.assertContains(response, "Vaše žádost o funkci koordinátora organizace byla zamítnuta.")


class TrackViewTests(ViewsLogon):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches', 'trips']

    def test_dpnk_views_gpx_file(self):
        trip = mommy.make(
            models.Trip,
            user_attendance=self.user_attendance,
            date=datetime.date(year=2010, month=11, day=20),
            direction='trip_from',
            commute_mode='bicycle',
        )
        gpxfile = mommy.make(
            models.GpxFile,
            user_attendance=self.user_attendance,
            trip_date=datetime.date(year=2010, month=11, day=20),
            direction='trip_from',
        )

        address = reverse('gpx_file', kwargs={"id": gpxfile.pk})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(models.GpxFile.objects.get(pk=gpxfile.pk).trip, trip)

    def test_dpnk_views_gpx_file_no_trip(self):
        address = reverse('gpx_file', kwargs={"id": 2})
        response = self.client.get(address)
        self.assertContains(response, "Datum vykonání cesty")

    def test_dpnk_company_structure(self):
        util.rebuild_denorm_models([self.user_attendance])
        address = reverse("company_structure")
        response = self.client.get(address)
        self.assertContains(response, "Testing company")
        self.assertContains(response, "Testing User 1")
        self.assertContains(response, "test@test.cz")
        self.assertContains(response, "organizace platí fakturou")
        self.assertContains(response, "(Platba přijata)")

    def test_dpnk_views_track_gpx_file(self):
        address = reverse('upravit_trasu')
        with open('dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                'dont_want_insert_track': False,
                'track': '',
                'gpx_file': gpxfile,
                'submit': 'Odeslat',
            }
            response = self.client.post(address, post_data)
        self.assertRedirects(response, reverse('profil'), fetch_redirect_response=False)
        user_attendance = models.UserAttendance.objects.length().get(pk=1115)
        self.assertEquals(user_attendance.get_distance(), 13.32)

    def test_dpnk_views_track_gpx_file_route(self):
        address = reverse('upravit_trasu')
        with open('dpnk/test_files/route.gpx', 'rb') as gpxfile:
            post_data = {
                'dont_want_insert_track': False,
                'track': '',
                'gpx_file': gpxfile,
                'submit': 'Odeslat',
            }
            response = self.client.post(address, post_data)
        self.assertRedirects(response, reverse('profil'), fetch_redirect_response=False)
        user_attendance = models.UserAttendance.objects.length().get(pk=1115)
        self.assertEquals(user_attendance.get_distance(), 6.72)

    def test_dpnk_views_track(self):
        address = reverse('upravit_trasu')
        post_data = {
            'dont_want_insert_track': False,
            'gpx_file': '',
            'track':
                '{"type": "MultiLineString", "coordinates": [[[14.377684590344607, 50.104472624878724], [14.382855889324802, 50.104637777363834], '
                '[14.385232326511767, 50.10294493739811], [14.385398623470714, 50.102697199702064], [14.385446903233, 50.102236128912004], '
                '[14.38538253021666, 50.101957419789834]]]}',
            'submit': 'Odeslat',
        }
        response = self.client.post(address, post_data)
        self.assertRedirects(response, reverse('profil'), fetch_redirect_response=False)
        user_attendance = models.UserAttendance.objects.length().get(pk=1115)
        self.assertEquals(user_attendance.get_distance(), 0.74)

    def test_dpnk_views_track_only_distance(self):
        address = reverse('upravit_trasu')
        post_data = {
            'dont_want_insert_track': True,
            'distance': 12,
            'gpx_file': '',
            'submit': 'Odeslat',
        }
        response = self.client.post(address, post_data)
        self.assertRedirects(response, reverse('profil'), fetch_redirect_response=False)
        user_attendance = models.UserAttendance.objects.length().get(pk=1115)
        self.assertEquals(user_attendance.track, None)
        self.assertEquals(user_attendance.get_distance(), 12)

    def test_dpnk_views_track_no_track_distance(self):
        address = reverse('upravit_trasu')
        post_data = {
            'dont_want_insert_track': False,
            'gpx_file': '',
            'track': '',
            'submit': 'Odeslat',
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(response, "Zadejte trasu, nebo zaškrtněte, že trasu nechcete zadávat.")

    def test_dpnk_rest_gpx_gz(self):
        with open('dpnk/test_files/modranska-rokle.gpx.gz', 'rb') as gpxfile:
            post_data = {
                'trip_date': '2010-11-3',
                'direction': 'trip_to',
                'file': gpxfile,
            }
            response = self.client.post("/rest/gpx/", post_data, format='multipart', follow=True)
            self.assertEquals(response.status_code, 201)
        gpx_file = models.GpxFile.objects.get(trip_date=datetime.date(year=2010, month=11, day=3))
        self.assertEquals(gpx_file.direction, 'trip_to')
        self.assertEquals(gpx_file.length(), 13.32)

    def test_dpnk_rest_gpx(self):
        with open('dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                'trip_date': '2010-11-3',
                'direction': 'trip_to',
                'file': gpxfile,
            }
            response = self.client.post("/rest/gpx/", post_data, format='multipart', follow=True)
            self.assertEquals(response.status_code, 201)
        gpx_file = models.GpxFile.objects.get(trip_date=datetime.date(year=2010, month=11, day=3))
        self.assertEquals(gpx_file.direction, 'trip_to')
        self.assertEquals(gpx_file.length(), 13.32)

    def test_emission_calculator(self):
        address = reverse('emission_calculator')
        response = self.client.get(address)
        self.assertContains(response, "<h2>Emisní kalkulačka</h2>", html=True)
        self.assertContains(response, "<tr><td>Ujetá vzdálenost</td><td>161,9&nbsp;km</td></tr>", html=True)
        self.assertContains(response, "<tr><td>CO</td><td>117 280,4&nbsp;mg</td></tr>", html=True)
        self.assertContains(response, "<tr><td>NO<sub>X</sub></td><td>27 474,4&nbsp;mg</td></tr>", html=True)
        self.assertContains(response, "<tr><td>N<sub>2</sub>O</td><td>4 047,5&nbsp;mg</td></tr>", html=True)
        self.assertContains(response, "<tr><td>CH<sub>4</sub></td><td>1 246,6&nbsp;mg</td></tr>", html=True)
        self.assertContains(response, "<tr><td>SO<sub>2</sub></td><td>1 246,6&nbsp;mg</td></tr>", html=True)
        self.assertContains(response, "<tr><td>Pevné částice</td><td>5 666,5&nbsp;mg</td></tr>", html=True)
        self.assertContains(response, "<tr><td>Olovo</td><td>1,8&nbsp;mg</td></tr>", html=True)
        self.assertContains(response, '<h3>Popis emisní kalkulačky</h3>', html=True)

    def test_daily_distance_extra_json(self):
        address = reverse(views.daily_distance_extra_json)
        response = self.client.get(address)
        self.assertEquals(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "2010-11-01": {"distance": 5.0, "distance_bicycle": 0, "distance_foot": 5.0, "emissions_co2": 645.0},
                "2010-11-02": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-03": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-04": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-05": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-06": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-07": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-08": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-09": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-10": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-11": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-12": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-13": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-14": {"distance": 156.9, "distance_bicycle": 156.9, "distance_foot": 0, "emissions_co2": 20240.1},
                "2010-11-15": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-16": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-17": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-18": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-19": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
                "2010-11-20": {"distance": 0, "distance_bicycle": 0, "distance_foot": 0, "emissions_co2": 0},
            },
        )


class StatisticsTests(ViewsLogon):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches', 'trips']

    def test_statistics(self):
        address = reverse(views.statistics)
        response = self.client.get(address)
        self.assertEquals(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "pocet-zaplacenych": 2,
                "pocet-soutezicich": 2,
                "pocet-cest": 3,
                "pocet-cest-kolo": 2,
                "pocet-cest-pesky": 1,
                "pocet-prihlasenych": 6,
                "pocet-cest-dnes": 0,
                "ujeta-vzdalenost-dnes": 0,
                "ujeta-vzdalenost": 167.2,
                "ujeta-vzdalenost-pesky": 5.0,
                "usetrene-emise-co2": 21568.8,
                "ujeta-vzdalenost-kolo": 162.2,
                "pocet-spolecnosti": 1,
                "pocet-pobocek": 2,
            },
        )


class RidesDetailsTests(ViewsLogon):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches', 'trips']

    def test_dpnk_rides_details(self):
        response = self.client.get(reverse('rides_details'))
        self.assertContains(response, '/cs/gpx_file/1')
        self.assertContains(response, '5,0')
        self.assertContains(response, 'Chůze/běh')
        self.assertContains(response, 'Podrobný přehled jízd')
        self.assertContains(response, '1. listopadu 2009')
