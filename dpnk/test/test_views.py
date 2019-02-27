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
from unittest.mock import ANY, MagicMock, call, patch

from PyPDF2 import PdfFileReader

from ddt import data, ddt

import denorm

from django.contrib.gis.db.models.functions import Length
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.test import Client, RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import reverse

from dpnk import models, util, views
from dpnk.test.util import ClearCacheMixin, DenormMixin
from dpnk.test.util import print_response  # noqa

from model_mommy import mommy

import settings

from t_shirt_delivery.models import PackageTransaction

from .mommy_recipes import CampaignRecipe, PriceLevelRecipe, UserAttendancePaidRecipe, UserAttendanceRecipe, campaign_get_or_create, testing_campaign


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class ViewsLogon(DenormMixin, ClearCacheMixin, TestCase):
    """ Tests in which the user is logged in """
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches']

    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.testserver")
        self.client.force_login(models.User.objects.get(username='test'), settings.AUTHENTICATION_BACKENDS[0])
        util.rebuild_denorm_models(models.UserAttendance.objects.filter(pk__in=[1015, 1115, 2115, 1016]))
        util.rebuild_denorm_models(models.Team.objects.filter(pk=1))
        self.user_attendance = models.UserAttendance.objects.get(pk=1115)


@override_settings(
    PAYU_POS_ID="123321",
)
class CompetitionsViewTests(ViewsLogon):
    def test_competition_rules(self):
        address = reverse('competition-rules-city', kwargs={'city_slug': "testing-city"})
        response = self.client.get(address)
        self.assertContains(response, "Testing campaign - Pravidla soutěží - Testing city")
        self.assertContains(response, "Competition vykonnostr rules")
        self.assertContains(response, "soutěž na vzdálenost jednotlivců  ve městě Testing city")
        self.assertContains(response, "soutěž na vzdálenost týmů  ve městě Testing city pro muže")

    def test_competition_results(self):
        address = reverse('competition-results-city', kwargs={'city_slug': "testing-city"})
        response = self.client.get(address)
        self.assertContains(response, "Testing campaign - Výsledky soutěží - Testing city")
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
        self.assertContains(
            response,
            '<td colspan="5">Registrace nebyla dokončena, nepočítá se do výsledků.</td>',
            html=True,
        )
        self.assertContains(response, '30')
        self.assertContains(response, '156,9&nbsp;km')

    def test_edit_team(self):
        address = reverse('edit_team')
        response = self.client.get(address)
        self.assertContains(response, 'Upravit údaje týmu')
        self.assertContains(response, 'Testing team 1')

    def test_upload_team_photo(self):
        address = reverse('upload_team_photo')
        with open('dpnk/test_files/DSC00002.JPG', 'rb') as fd:
            post_data = {
                'image': fd,
            }
            response = self.client.post(address, post_data)
        self.assertEqual(response.status_code, 200)

    def test_daily_chart(self):
        address = reverse(views.daily_chart)
        response = self.client.get(address)
        self.assertContains(response, '<img src=\'http://chart.apis.google.com/chart?chxl=0:|1:|2010-11-20|')

    def test_update_team(self):
        address = reverse('zmenit_tym')
        response = self.client.get(address)
        self.assertContains(response, 'Napište svému firemnímu koordinátorovi na e-mail ')
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
        self.assertContains(response, 'Uživatelské jméno, které Vám sdělí zákazník')
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
        self.assertEqual(response.status_code, 200)

    def test_bike_repair_post_nonexistent_user(self):
        address = reverse('bike_repair')
        post_data = {
            "user_attendance": "test test",
            "description": "Bike repair note",
            "submit": "Odeslat",
        }
        response = self.client.post(address, post_data)
        self.assertContains(response, 'Takový uživatel neexistuje')
        self.assertEqual(response.status_code, 200)

    def test_bike_repair_post_last_campaign(self):
        address = reverse('bike_repair')
        post_data = {
            "user_attendance": "test@test.cz",
            "description": "Bike repair note",
            "submit": "Odeslat",
        }
        response = self.client.post(address, post_data)
        self.assertContains(response, 'Tento uživatel není nováček, soutěžil již v předcházejících kampaních: Testing campaign - last year')
        self.assertEqual(response.status_code, 200)

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
    def test_registration_access(self, slumber_api):
        slumber_instance = slumber_api.return_value
        slumber_instance.feed.get.return_value = self.feed_value
        address = reverse('registration_access')
        response = self.client.get(address)
        self.assertRedirects(response, reverse('profil'), status_code=302)


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class BaseViewsTests(ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions']

    def setUp(self):
        self.client = Client(HTTP_HOST="testing-campaign.testserver")
        self.client.force_login(models.User.objects.get(username='test'), settings.AUTHENTICATION_BACKENDS[0])

    def test_chaining(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.filter(pk__in=[1115, 2115, 1015]))
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
            [{'value': 4, 'display': 'Empty team'}, {'value': 1, 'display': 'Testing team 1 (Nick, Testing User 1, Registered User 1)'}],
        )

    def test_chaining_subsidiary(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.filter(pk__in=[1115, 2115, 1015]))
        util.rebuild_denorm_models(models.Team.objects.filter(pk__in=(1, 4)))
        denorm.flush()
        kwargs = {
            'app': 'dpnk',
            'model': 'Subsidiary',
            'field': 'company',
            'foreign_key_app_name': 'dpnk',
            'foreign_key_model_name': 'Subsidiary',
            'foreign_key_field_name': 'company',
            'value': '1',
        }
        address = reverse('chained_filter', kwargs=kwargs)
        response = self.client.get(address)
        self.assertJSONEqual(
            response.content.decode(),
            [
                {'display': 'Ulice 1, 111 11 Praha - Testing city', 'value': 1},
                {'display': 'Ulice 2, 222 22 Brno - Other city', 'value': 2},
            ],
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
        self.price_level = mommy.make(
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
        self.user_attendance.campaign.save()
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
            '<div class="alert alert-success">Vaši platbu jsme úspěšně přijali.</div>',
            html=True,
            status_code=403,
        )

    def test_dpnk_payment_type_no_admission_fee(self):
        self.price_level.delete()
        self.user_attendance.save()
        response = self.client.get(reverse('typ_platby'))
        self.assertContains(
            response,
            '<div class="alert alert-success">Startovné se neplatí.</div>',
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
            '<div class="alert alert-warning">'
            'Platbu ještě musí schválit koordinátor Vaší organizace '
            '<a href="mailto:foo@email.com">foo@email.com</a>.',
            html=True,
        )
        self.assertEqual(models.Payment.objects.get().pay_type, 'fc')

    def test_dpnk_payment_type_no_t_shirt(self):
        post_data = {
            'payment_type': 'company',
            'next': 'Next',
        }
        self.user_attendance.t_shirt_size = None
        self.user_attendance.save()
        self.assertTrue(self.user_attendance.campaign.has_any_tshirt)
        response = self.client.post(reverse('typ_platby'), post_data, follow=True)
        self.assertContains(
            response,
            "<div class=\"alert alert-warning\">Zatím není co platit. "
            "Nejdříve se <a href='/tym/'>přidejte k týmu</a> a <a href='/zmenit_triko/'>vyberte tričko</a>.</div>",
            status_code=403,
            html=True,
        )

    def test_dpnk_payment_type_without_company_admin(self):
        post_data = {
            'payment_type': 'company',
            'next': 'Next',
        }
        response = self.client.post(reverse('typ_platby'), post_data)
        self.assertContains(
            response,
            "Váš zaměstnavatel Testing company nemá zvoleného firemního koordinátora nebo neumožňuje platbu za zaměstnance.",
        )

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
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'trips', 'commute_mode']

    def test_distance(self):
        trips = models.Trip.objects.all()
        distance = views.distance_all_modes(trips)
        self.assertEqual(
            distance,
            {
                'distance__sum': 167.2,
                'distance_bicycle': 162.2,
                'distance_foot': 5.0,
                'count__sum': 3,
                'count_bicycle': 2,
                'count_foot': 1,
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class CompetitionResultsViewTests(ClearCacheMixin, DenormMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches', 'company_competition', 'test_results_data', 'trips']

    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.testserver")

    @patch('dpnk.views.logger')
    def test_dpnk_competition_results_unknown(self, mock_logger):
        address = reverse('competition_results', kwargs={'competition_slug': 'unexistent_competition'})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 404)

    def test_dpnk_competition_results_vykonnost_tymu(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        models.Competition.objects.get(slug="vykonnost-tymu").recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'vykonnost-tymu'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Výkonnost týmů:")
        self.assertContains(
            response,
            '<th scope="col" id="result_divident-9">Po&shy;čet za&shy;po&shy;čí&shy;ta&shy;ných ki&shy;lo&shy;me&shy;trů</th>',
            html=True,
        )

    def test_dpnk_competition_results_quest_not_finished(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        competition = models.Competition.objects.filter(slug="quest")
        competition.get().recalculate_results()
        address = reverse('competition_results', kwargs={'competition_slug': 'quest'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Dotazník:")
        self.assertContains(response, "Výsledky této soutěže se nezobrazují")

    def test_dpnk_competition_results_TF(self):
        address = reverse('competition_results', kwargs={'competition_slug': 'TF'})
        response = self.client.get(address)
        self.assertContains(response, "Výsledky v soutěži Team frequency:")


class ViewsTestsMommy(ClearCacheMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.example.com")

    def test_competitor_counts(self):
        city = mommy.make("City", name="Foo city")
        PriceLevelRecipe.make()
        user_attendances = [
            UserAttendancePaidRecipe.make(team=None),
            UserAttendancePaidRecipe.make(
                team__subsidiary__city=city,
                user_trips=[mommy.make("Trip", direction="trip_to", distance=2, commute_mode_id=2)],
            ),
            UserAttendancePaidRecipe.make(
                team__subsidiary__city=city,
                user_trips=[mommy.make("Trip", direction="trip_to", distance=3)],
            ),
        ]
        for ua in user_attendances:
            ua.save()
        response = self.client.get(reverse('competitor_counts'))
        self.assertContains(
            response,
            "<tr>"
            "   <td>Foo city</td>"
            "   <td>2</td>"
            "   <td>3.0</td>"
            "   <td>2.0</td>"
            "   <td>5.0</td>"
            "   <td>1</td>"
            "   <td>1</td>"
            "   <td>645.0</td>"
            "</tr>",
            html=True,
        )
        self.assertContains(
            response,
            "<tr><td>bez vybraného města</td><td>1</td><td></td><td></td><td></td><td></td><td></td><td></td></tr>",
            html=True,
        )
        self.assertContains(
            response,
            "<tr>"
            "   <th>celkem</th>"
            "   <th>3</th>"
            "   <th>3,0</th>"
            "   <th>2,0</th>"
            "   <th>5,0</th>"
            "   <th>1</th>"
            "   <th>1</th>"
            "   <th>645,0</th>"
            "</tr>",
            html=True,
        )


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
        self.assertContains(response, "E-mail")

        address = reverse('login', kwargs={'initial_email': "test@test.cz"})
        response = self.client.get(address)
        self.assertContains(response, "E-mail")
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

    def test_dpnk_company_admin_registration(self):
        address = reverse('register_admin')
        post_data = {
            'email': 'testadmin@test.cz',
            'password1': 'password11',
            'password2': 'password11',
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
        self.assertEqual(user.get_full_name(), "Company Admin")
        self.assertEqual(models.UserProfile.objects.get(user=user).telephone, '123456789')
        self.assertEqual(models.CompanyAdmin.objects.get(userprofile=user.userprofile).administrated_company.pk, 2)
        self.assertEqual(len(mail.outbox), 3)
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
            'password1': 'password11',
            'password2': 'password11',
        }
        response = self.client.post(address, post_data)
        self.assertRedirects(response, reverse('upravit_profil'))
        user = models.User.objects.get(email='test1@test.cz')
        self.assertNotEqual(user, None)
        self.assertNotEqual(models.UserProfile.objects.get(user=user), None)
        self.assertNotEqual(models.UserAttendance.objects.get(userprofile__user=user), None)

    def test_dpnk_registration_access(self):
        address = reverse('registration_access')
        response = self.client.get(address)
        self.assertContains(response, "Zadejte svůj e-mail")
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
            'password1': 'password11',
            'password2': 'password11',
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
        user_attendance = models.UserAttendance.objects.annotate(
            length=Length('track'),
        ).get(
            userprofile__user__username='user_without_attendance',
            campaign__pk=339,
        )
        self.assertEqual(user_attendance.userprofile.user.pk, 1041)
        self.assertEqual(user_attendance.get_distance(), 156.9)


class RegistrationPhaseTests(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.example.com")
        self.campaign = mommy.make("dpnk.campaign", slug="testing-campaign")

    def test_dpnk_registration_no_phase(self):
        response = self.client.get(reverse('registrace'))
        self.assertContains(
            response,
            '<div class="alert alert-danger">Tato stránka nemůže být v této kampani zobrazena. Neexistuje v ní fáze registrační.</div>',
            html=True,
            status_code=403,
        )

    @override_settings(
        FAKE_DATE=datetime.date(year=2020, month=10, day=1),
    )
    def test_dpnk_registration_after_phase(self):
        mommy.make(
            "dpnk.Phase",
            phase_type="registration",
            date_from="2011-01-01",
            date_to="2011-02-01",
            campaign=self.campaign,
        )
        response = self.client.get(reverse('registrace'))
        self.assertContains(
            response,
            '<div class="alert alert-danger">Registrace již byla ukončena.</div>',
            html=True,
            status_code=403,
        )

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=10, day=1),
    )
    def test_dpnk_registration_before_phase(self):
        mommy.make(
            "dpnk.Phase",
            phase_type="registration",
            date_from="2011-01-01",
            date_to="2011-02-01",
            campaign=self.campaign,
        )
        response = self.client.get(reverse('registrace'))
        self.assertContains(
            response,
            '<div class="alert alert-danger">Registrace ještě nezačala.<br/>Registrovat se budete moct od 01.01.2011</div>',
            html=True,
            status_code=403,
        )


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
            'password1': 'password11',
            'password2': 'password11',
        }
        response = self.client.post(address, post_data)
        self.assertRedirects(response, reverse('upravit_profil'))
        user = models.User.objects.get(email='test1@test.cz')
        self.assertNotEqual(user, None)
        self.assertNotEqual(models.UserProfile.objects.get(user=user), None)
        ua = models.UserAttendance.objects.get(userprofile__user=user)
        self.assertNotEqual(ua, None)
        self.assertEqual(ua.team.pk, 1)

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
            'password1': 'password11',
            'password2': 'password11',
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
        self.assertEqual(ua.team, None)


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

    def test_questionnaire_view_unauthenticated(self):
        self.client = Client(HTTP_HOST="testing-campaign.testserver")
        kwargs = {'questionnaire_slug': 'quest'}
        address = reverse('questionnaire', kwargs=kwargs)
        response = self.client.get(address)
        self.assertRedirects(response, '/login?next=/otazka/quest/')

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
        setattr(request, 'session', 'session')
        self.messages = FallbackStorage(request)
        setattr(request, '_messages', self.messages)
        request.user = self.user_attendance.userprofile.user
        request.user_attendance = self.user_attendance
        request.subdomain = "testing-campaign"
        response = views.QuestionnaireView.as_view()(request, **kwargs)
        self.assertEqual(response.url, reverse("profil"))

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


class ViewsLogonMommy(TestCase):
    def get_user_attendance(self):
        return UserAttendanceRecipe.make()

    def setUp(self):
        super().setUp()
        self.user_attendance = self.get_user_attendance()
        self.client = Client(HTTP_HOST="testing-campaign.example.com")
        self.client.force_login(self.user_attendance.userprofile.user, settings.AUTHENTICATION_BACKENDS[0])


@override_settings(
    FAKE_DATE=datetime.date(2010, 11, 20),
)
class TestRidesView(ViewsLogonMommy):
    def get_user_attendance(self):
        testing_campaing = campaign_get_or_create(
            slug="testing-campaign",
            name='Testing campaign',
            minimum_rides_base=10000,
            track_required=False,
        )
        user_attendance = UserAttendanceRecipe.make(
            campaign=testing_campaing,
            userprofile__sex='male',
            userprofile__user__first_name='Foo',
            userprofile__user__last_name='User',
            userprofile__user__email='foo@bar.cz',
            userprofile__telephone='12345',
            personal_data_opt_in=True,
            team__name="Foo team",
            approved_for_team='approved',
        )
        mommy.make(
            'CityInCampaign',
            campaign=testing_campaing,
            city=user_attendance.team.subsidiary.city,
        )
        return user_attendance


class TestRegisterCompanyView(ViewsLogonMommy):
    def test_get(self):
        response = self.client.get(
            reverse('register_company'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertContains(
            response,
            '<label for="id_name" class="col-form-label  requiredField">'
            'Název společnosti'
            '<span class="asteriskField">*</span>'
            '</label>',
            html=True,
        )

    def test_create(self):
        post_data = {
            'ico': '12345679',
            'name': 'Foo name',
        }
        response = self.client.post(
            reverse('register_company'),
            post_data,
            follow=True,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        company = models.Company.objects.get(name="Foo name")
        self.assertJSONEqual(
            response.content.decode(),
            {"status": "ok", "name": "Foo name", "id": company.id},
        )

    def test_duplicate_ico(self):
        """ Test, that duplicate IČO error is reported to the user """
        mommy.make('Company', ico='12345679')
        post_data = {
            'ico': '12345679',
        }
        response = self.client.post(
            reverse('register_company'),
            post_data,
            follow=True,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertContains(
            response,
            "<strong>Toto pole je vyžadováno.</strong>",
            html=True,
        )
        self.assertContains(
            response,
            "<strong>Organizace s tímto IČO již existuje, nezakládemte prosím novou, ale vyberte jí prosím ze seznamu</strong>",
            html=True,
        )

    def test_invalid_ico(self):
        """ Test, that duplicate IČO error is reported to the user """
        mommy.make('Company', ico='1234')
        post_data = {
            'ico': '1234',
        }
        response = self.client.post(
            reverse('register_company'),
            post_data,
            follow=True,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertContains(
            response,
            "<strong>Toto pole je vyžadováno.</strong>",
            html=True,
        )
        self.assertContains(
            response,
            "<strong>IČO není zadáno ve správném formátu. Zkontrolujte že číslo má osm číslic a případně ho doplňte nulami zleva.</strong>",
            html=True,
        )


class TestRegisterSubsidiaryView(ViewsLogonMommy):
    def test_create(self):
        city = mommy.make('City')
        mommy.make('CityInCampaign', city=city, campaign=self.user_attendance.campaign)
        mommy.make('PSC', psc=12345)
        company = mommy.make('Company')
        post_data = {
            "company": company.id,
            "city": city.id,
            "address_recipient": "Foo recipient",
            "address_street": "Foo street",
            "address_street_number": "123",
            "address_psc": "12345",
            "address_city": "Foo city",
        }
        response = self.client.post(
            reverse('register_subsidiary', args=(company.id,)),
            post_data,
            follow=True,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        subsidiary = models.Subsidiary.objects.get(company=company)
        self.assertEqual(subsidiary.address.street_number, "123")
        self.assertEqual(subsidiary.address.recipient, "Foo recipient")
        self.assertJSONEqual(
            response.content.decode(),
            {"status": "ok", "id": subsidiary.id},
        )

    def test_psc_failing(self):
        company = mommy.make('Company')
        post_data = {
            "address_psc": "123",
        }
        response = self.client.post(
            reverse('register_subsidiary', args=(company.id,)),
            post_data,
            follow=True,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertContains(
            response,
            "<strong>PSČ musí být pěticiferné číslo</strong>",
            html=True,
        )

    def test_psc_failing_no_integer(self):
        company = mommy.make('Company')
        post_data = {
            "address_psc": "FOO",
        }
        response = self.client.post(
            reverse('register_subsidiary', args=(company.id,)),
            post_data,
            follow=True,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertContains(
            response,
            "<strong>PSČ musí být pěticiferné číslo</strong>",
            html=True,
        )


class TestDiplomasView(ViewsLogonMommy):
    def setUp(self):
        super().setUp()

    def shared_checks(self, response):
        self.assertNotContains(
            response,
            "None",
        )
        self.assertContains(
            response,
            "Testing campaign",
        )

    def test_basic(self):
        self.team = mommy.make(
            "Team",
            name="Foo team",
            campaign=self.user_attendance.campaign,
            subsidiary__city__name="Foo city",
        )
        self.user_attendance.team = self.team
        self.user_attendance.save()
        response = self.client.get(reverse('diplomas'))
        self.shared_checks(response)
        self.assertContains(response, "Foo team")

    def test_no_team(self):
        response = self.client.get(reverse('diplomas'))
        self.shared_checks(response)


class TestRegisterTeamView(ViewsLogonMommy):
    def setUp(self):
        self.subsidiary = mommy.make('Subsidiary')
        super().setUp()

    def test_create(self):
        post_data = {
            'name': 'Foo name',
            'subsidiary': self.subsidiary.id,
            'campaign': self.user_attendance.campaign.id,
        }
        response = self.client.post(
            reverse('register_team', args=(self.subsidiary.id,)),
            post_data,
            follow=True,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        team = models.Team.objects.get(name="Foo name")
        self.assertJSONEqual(
            response.content.decode(),
            {"status": "ok", "name": "Foo name", "id": team.id},
        )

    def test_get(self):
        response = self.client.get(reverse('register_team', args=(self.subsidiary.id,)))
        self.assertContains(
            response,
            '<input type="text" name="name" maxlength="50" class="textinput textInput form-control" required id="id_name" />',
            html=True,
        )

    def test_get_previous_team(self):
        self.user_attendance.campaign.previous_campaign = mommy.make('Campaign')
        self.user_attendance.campaign.save()
        mommy.make(
            'UserAttendance',
            campaign=self.user_attendance.campaign.previous_campaign,
            userprofile=self.user_attendance.userprofile,
            team__name='Previous foo team',
            team__campaign=self.user_attendance.campaign.previous_campaign,
        )
        response = self.client.get(reverse('register_team', args=(self.subsidiary.id,)))
        self.assertContains(
            response,
            '<input type="text" name="name" value="Previous foo team" maxlength="50" '
            'class="textinput textInput form-control" required id="id_name" />',
            html=True,
        )

    def test_get_previous_no_team(self):
        self.user_attendance.campaign.previous_campaign = mommy.make('Campaign')
        self.user_attendance.campaign.save()
        mommy.make(
            'UserAttendance',
            campaign=self.user_attendance.campaign.previous_campaign,
            userprofile=self.user_attendance.userprofile,
        )
        response = self.client.get(reverse('register_team', args=(self.subsidiary.id,)))
        self.assertContains(
            response,
            '<input type="text" name="name" maxlength="50" class="textinput textInput form-control" required id="id_name" />',
            html=True,
        )


class ViewsTestsLogon(ViewsLogon):
    def test_dpnk_team_view(self):
        response = self.client.get(reverse('zmenit_tym'))
        self.assertContains(response, "Testing company")
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
                    {"value": "Testing company", "label": "Testing company (IČO: 11111)", "id": 1},
                    {"value": "Testing company without admin", "label": "Testing company without admin (IČO: 11111)", "id": 2},
                ],
                "meta": {
                    "more": "Zobrazit další výsledky",
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
        address = reverse('change_team_invitation', kwargs={'token': token, 'initial_email': email})
        response = self.client.get(address)
        self.assertContains(
            response,
            "<div>Přejete si být zařazeni do týmu Testing team 1 (Nick, Testing User 1, Registered User 1)?</div>",
            html=True,
        )

    def test_dpnk_team_invitation_full(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.filter(pk__in=[1016]))
        util.rebuild_denorm_models(models.Team.objects.filter(pk=3))
        self.user_attendance.campaign.max_team_members = 1
        self.user_attendance.campaign.save()
        token = "token123215"
        team = models.Team.objects.get(invitation_token=token)
        team.save()
        denorm.flush()
        email = self.user_attendance.userprofile.user.email
        address = reverse('change_team_invitation', kwargs={'token': token, 'initial_email': email})
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
        address = reverse('change_team_invitation', kwargs={'token': "token123214", 'initial_email': email})
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
        address = reverse('change_team_invitation', kwargs={'token': token, 'initial_email': email})
        response = self.client.get(address)
        self.assertContains(response, "<h2>Pozvánka do týmu</h2>", html=True)

        post_data = {
            "question": "on",
            "submit": "Odeslat",
            "team": self.user_attendance.team.id,
            "campaign": self.user_attendance.campaign.id,
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(response, "<h2>Vyberte jiný tým</h2>", html=True)

    def test_dpnk_team_invitation_post_no_last_team(self):
        token = self.user_attendance.team.invitation_token
        self.user_attendance.team = None
        self.user_attendance.save()
        email = self.user_attendance.userprofile.user.email
        address = reverse('change_team_invitation', kwargs={'token': token, 'initial_email': email})
        response = self.client.get(address)
        self.assertContains(response, "<h2>Pozvánka do týmu</h2>", html=True)

        post_data = {
            "question": "on",
            "submit": "Odeslat",
            "campaign": self.user_attendance.campaign.id,
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(
            response,
            '<div class="alert alert-success">Tým úspěšně změněn</div>',
            html=True,
        )

    def test_dpnk_team_invitation_confirmation_unchecked(self):
        token = self.user_attendance.team.invitation_token
        email = self.user_attendance.userprofile.user.email
        address = reverse('change_team_invitation', kwargs={'token': token, 'initial_email': email})

        post_data = {
            "submit": "Odeslat",
        }
        response = self.client.post(address, post_data, follow=True)

        self.assertContains(
            response,
            '<span id="error_1_id_question" class="invalid-feedback"><strong>Toto pole je vyžadováno.</strong></span>',
            html=True,
        )

    def test_dpnk_team_invitation_bad_email(self):
        token = self.user_attendance.team.invitation_token
        response = self.client.get(
            reverse('change_team_invitation', kwargs={'token': token, 'initial_email': 'invitation_test@email.com'}),
            follow=True,
        )
        self.assertRedirects(response, "/login/invitation_test@email.com/?next=/tym/token123213/invitation_test@email.com/")
        self.assertContains(response, "invitation_test@email.com")

    def test_dpnk_team_invitation_unknown_team(self):
        response = self.client.get(reverse('change_team_invitation', kwargs={'token': 'asdf', 'initial_email': 'invitation_test@email.com'}))
        self.assertContains(response, "Tým nenalezen", status_code=403)

    def test_dpnk_team_invitation_logout(self):
        self.client.logout()
        token = self.user_attendance.team.invitation_token
        response = self.client.get(reverse('change_team_invitation', kwargs={'token': token, 'initial_email': 'invitation_test@email.com'}))
        self.assertRedirects(response, "%s?next=/tym/%s/invitation_test%%40email.com/" % (reverse('login'), token))

    @override_settings(
        DEBUG=True,
    )
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
            'user-email': 'testing@email.cz',
            'user-first_name': 'Testing',
            'user-last_name': 'Name',
            'userprofile-language': 'cs',
            'userprofile-mailing_opt_in': 'True',
            'userprofile-nickname': 'My super nick',
            'userattendance-personal_data_opt_in': 'True',
            'userprofile-sex': 'male',
            'userprofile-telephone': '111222333',
            'next': 'Další',
        }
        address = reverse('upravit_profil')
        response = self.client.post(address, post_data, follow=True)
        self.assertRedirects(response, reverse("zmenit_tym"))
        self.assertContains(response, "My super nick")

    def test_dpnk_update_profile_view_no_sex(self):
        post_data = {
            'userprofile-sex': 'unknown',
            'next': 'Další',
        }
        address = reverse('upravit_profil')
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(response, "Pohlaví")

    def test_dpnk_update_profile_view_email_exists(self):
        post_data = {
            'user-email': 'test2@test.cz',
            'next': 'Další',
        }
        address = reverse('upravit_profil')
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(response, "Tento e-mail již je v našem systému zanesen.")

    @patch('slumber.API')
    def company_payment(self, slumber_api, amount, amount_tax, beneficiary=False):
        models.Payment.objects.get(id=17).delete()
        denorm.flush()
        slumber_instance = slumber_api.return_value
        slumber_instance.feed.get.return_value = [{"content": "Emission calculator description text"}]
        response = self.client.get(reverse('company_admin_pay_for_users'))
        self.assertContains(
            response,
            '<tr>'
            '<td>'
            '<input class="tableselectmultiple selectable-checkbox form-check-input" '
            'id="id_paing_for_0" name="paing_for" type="checkbox" value="2115"/>'
            '</td>'
            '<td>%s</td>'
            '<td>Registered</td>'
            '<td>User 1</td>'
            '<td></td>'
            '<td>test-registered@test.cz</td>'
            '<td>Testing city</td>'
            '</tr>' % (str(amount).replace(".", ",")),
            html=True,
        )
        post_data = {
            'paing_for': '2115',
            'submit': 'Odeslat',
        }
        response = self.client.post(reverse('company_admin_pay_for_users'), post_data, follow=True)
        self.assertRedirects(response, reverse('company_admin_pay_for_users'))
        p = models.UserAttendance.objects.get(id=2115).representative_payment
        self.assertEqual(p.status, models.Status.COMPANY_ACCEPTS)

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
        self.assertEqual(p.status, 1006)
        self.assertEqual(p.invoice.total_amount, amount_tax)
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
        self.company_payment(beneficiary=True, amount=130.0, amount_tax=545)

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
        self.assertContains(response, 'Členství uživatele Nick ve Vašem týmu bylo zamítnuto')

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
        self.assertContains(response, 'Uživatel Nick byl přijat do Vašeho týmu.')
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
        self.assertEqual(str(msg.subject), "Testing campaign - pozvánka do týmu / you've been invited to join a team")

    def test_dpnk_team_no_team(self):
        """ Test, that invitation shows warning if the team is not set """
        self.user_attendance.team = None
        self.user_attendance.save()
        response = self.client.get(reverse('pozvanky'))
        self.assertContains(
            response,
            '<div class="alert alert-danger">Pokud jeli napřed tak je dohoňte a <a href="/tym/">přidejte se k týmu</a>.</div>',
            html=True,
            status_code=403,
        )

    def test_dpnk_team_get(self):
        """ Test number of team members for invitation """
        response = self.client.get(reverse('pozvanky'))
        self.assertContains(
            response,
            "<p>Pozvěte přátele z práce, aby podpořili Váš tým, který může mít až 5 členů.</p>",
            html=True,
        )

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
        self.assertEqual(company_admin.motivation_company_admin, 'Testing position')

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
            '<label for="id_motivation_company_admin" class="col-form-label  requiredField">'
            'S kým máme tu čest?'
            '<span class="asteriskField">*</span>'
            '</label>',
            html=True,
        )


class ChangeTeamViewTests(TestCase):
    blank_team_html = """<select
        name="team"
        name="team"
        data-value="null"
        data-url="/chaining/filter/dpnk/Team/team_in_campaign_testing-campaign/subsidiary/dpnk/Subsidiary/company"
        data-empty_label="--------"
        data-auto_choose="false"
        id="id_team"
        class="chainedselect form-control chained-fk"
        data-chainfield="subsidiary"
        required>
        </select>"""

    def setUp(self):
        self.client = Client(HTTP_HOST="testing-campaign.example.com", HTTP_REFERER="test-referer")
        self.campaign = testing_campaign()
        self.team = mommy.make(
            "Team",
            name="Foo name",
            campaign=self.campaign,
            subsidiary__city__name="Foo city",
        )
        mommy.make('CityInCampaign', city=self.team.subsidiary.city, campaign=self.campaign)
        self.user_attendance = UserAttendanceRecipe.make(campaign=self.campaign, team=self.team)
        self.client.force_login(self.user_attendance.userprofile.user, settings.AUTHENTICATION_BACKENDS[0])

    def test_dpnk_team_change_me_undecided(self):
        """ If I my team membership is undecided, I have to be able to leave the team """
        self.user_attendance.approved_for_team = 'undecided'
        self.user_attendance.save()
        UserAttendanceRecipe.make(approved_for_team='approved', campaign=self.campaign, team=self.team)
        self.team.save()
        self.assertEqual(self.team.member_count, 1)
        self.assertEqual(self.team.unapproved_member_count, 1)
        response = self.client.get(reverse('zmenit_tym'))
        self.assertEqual(response.status_code, 200)

    def test_dpnk_team_undecided(self):
        """ If I am the only approved team member of a team where all others are undicided, I can't leave the team """
        self.user_attendance.approved_for_team = 'approved'
        self.user_attendance.save()
        UserAttendanceRecipe.make(approved_for_team='undecided', campaign=self.campaign, team=self.team)
        self.team.save()
        self.assertEqual(self.team.member_count, 1)
        self.assertEqual(self.team.unapproved_member_count, 1)
        response = self.client.get(reverse('zmenit_tym'))
        self.assertContains(
            response,
            "Nemůžete opustit tým, ve kterém jsou samí neschválení členové. "
            "Napřed někoho schvalte a pak změňte tým.",
            status_code=403,
        )

    def test_dpnk_team_change_alone_undecided(self):
        """ If I am in the team alone, I can leave the team if I am undecided """
        self.user_attendance.approved_for_team = 'undecided'
        self.user_attendance.save()
        self.team.save()
        self.assertEqual(self.team.member_count, 0)
        self.assertEqual(self.team.unapproved_member_count, 1)
        response = self.client.get(reverse('zmenit_tym'))
        self.assertEqual(response.status_code, 200)

    def test_dpnk_team_change_alone_approved(self):
        """ If I am in the team alone, I can leave the team if I am approved """
        self.user_attendance.approved_for_team = 'approved'
        self.user_attendance.save()
        self.team.save()
        self.assertEqual(self.team.member_count, 1)
        self.assertEqual(self.team.unapproved_member_count, 0)
        response = self.client.get(reverse('zmenit_tym'))
        self.assertEqual(response.status_code, 200)

    def test_get(self):
        response = self.client.get(reverse('zmenit_tym'))
        self.assertContains(
            response,
            '<option value="%s" selected>Foo name</option>' % self.team.id,
            html=True,
        )

    def test_get_one_team_member(self):
        """ Test that user chooses only subsidiary when in campaign with 1 team member """
        self.campaign.max_team_members = 1
        self.campaign.save()
        response = self.client.get(reverse('zmenit_tym'))
        self.assertNotContains(
            response,
            '<option value="%s" selected>Foo name</option>' % self.team.id,
            html=True,
        )
        self.assertNotContains(
            response,
            '<option value="%s" selected=""> - Foo city</option>' % self.team.subsidiary.id,
            html=True,
        )

    def test_get_blank(self):
        self.user_attendance.team = None
        self.user_attendance.save()
        response = self.client.get(reverse('zmenit_tym'))
        self.assertContains(  # Test blank select
            response,
            self.blank_team_html,
            html=True,
        )

    def test_get_previous(self):
        """ Test that team with same name as in last year is preselected """
        previous_campaign = CampaignRecipe.make()
        self.campaign.previous_campaign = previous_campaign
        self.campaign.save()
        UserAttendanceRecipe.make(
            campaign=previous_campaign,
            userprofile=self.user_attendance.userprofile,
            team__subsidiary__company__name="Foo company lasts",
            team__campaign=previous_campaign,
        )
        self.user_attendance.team = None
        self.user_attendance.save()
        address = reverse('zmenit_tym')
        response = self.client.get(address)

        self.assertContains(
            response,
            '<input type="text" name="company_0" value="Foo company lasts" '
            'data-selectable-allow-new="false" id="id_company_0" autocomplete="off"'
            'class="autocompletewidget form-control" data-selectable-type="text" '
            'required data-selectable-url="/selectable/dpnk-companylookup/" />',
            html=True,
        )

    def test_get_previous_none_team(self):
        """ Test that team with same name asi in last year doesn't exist, no team is preselected """
        previous_campaign = CampaignRecipe.make()
        self.campaign.previous_campaign = previous_campaign
        self.campaign.save()
        UserAttendanceRecipe.make(
            campaign=previous_campaign,
            userprofile=self.user_attendance.userprofile,
            team__name="Foo team lasts",
            team__campaign=previous_campaign,
        )
        self.user_attendance.team = None
        self.user_attendance.save()
        address = reverse('zmenit_tym')
        response = self.client.get(address)

        self.assertContains(  # No team is preselected
            response,
            self.blank_team_html,
            html=True,
        )

    def test_get_previous_different_company(self):
        """ Test that team with same name asi in last year exists, but is in different company, no team is preselected """
        previous_campaign = CampaignRecipe.make()
        previous_campaign = CampaignRecipe.make()
        self.campaign.previous_campaign = previous_campaign
        self.campaign.save()
        UserAttendanceRecipe.make(
            campaign=previous_campaign,
            userprofile=self.user_attendance.userprofile,
            team__name="Foo team lasts",
            team__campaign=previous_campaign,
        )
        mommy.make(
            "Team",
            name="Foo team lasts",
            campaign=self.campaign,
            subsidiary__company=mommy.make("Company"),
        )
        self.user_attendance.team = None
        self.user_attendance.save()
        address = reverse('zmenit_tym')
        response = self.client.get(address)

        self.assertContains(  # No team is preselected
            response,
            self.blank_team_html,
            html=True,
        )

    def test_change(self):
        city = mommy.make('City')
        mommy.make('CityInCampaign', city=city, campaign=self.campaign)
        new_team = mommy.make('Team', campaign=self.campaign, subsidiary__city=city)
        post_data = {
            "team": new_team.id,
            "subsidiary": new_team.subsidiary.id,
            "company_0": "Foo",
            "company_1": new_team.subsidiary.company.id,
            'next': 'Další',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)

        self.assertRedirects(response, reverse('pozvanky'))
        self.user_attendance.refresh_from_db()
        self.assertEqual(self.user_attendance.team, new_team)
        self.assertEqual(self.user_attendance.approved_for_team, "approved")

    def test_change_one_team_member(self):
        """ Test that user chooses only subsidiary when in campaign with 1 team member """
        self.campaign.max_team_members = 1
        self.campaign.save()
        new_subsidiary = mommy.make('Subsidiary', address_street="Foo street", city=self.team.subsidiary.city)
        post_data = {
            "subsidiary": new_subsidiary.id,
            "company_0": "Foo",
            "company_1": new_subsidiary.company.id,
            'next': 'Další',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)

        self.assertRedirects(response, reverse('zmenit_triko'))
        self.team.refresh_from_db()
        self.assertEqual(self.team, self.team)
        self.assertEqual(self.team.subsidiary, new_subsidiary)

    def test_change_one_team_member_without_team(self):
        """ Test that user chooses only subsidiary when in campaign with 1 team member """
        self.user_attendance.team = None
        self.user_attendance.save()
        self.campaign.max_team_members = 1
        self.campaign.save()
        new_subsidiary = mommy.make('Subsidiary', address_street="Foo street", city=self.team.subsidiary.city)
        post_data = {
            "subsidiary": new_subsidiary.id,
            "company_0": "Foo",
            "company_1": new_subsidiary.company.id,
            'next': 'Další',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)

        self.assertRedirects(response, reverse('zmenit_triko'))
        self.user_attendance.refresh_from_db()
        self.assertNotEqual(self.team, self.user_attendance.team)  # User is in new team
        self.assertEqual(self.user_attendance.team.subsidiary, new_subsidiary)

    def test_change_team_has_users(self):
        city = mommy.make('City')
        mommy.make('CityInCampaign', city=city, campaign=self.campaign)
        new_team = mommy.make(
            'Team',
            campaign=self.campaign,
            subsidiary__city=city,
            users=[UserAttendancePaidRecipe.make(userprofile__user__email="test@email.cz")],
        )
        new_team.save()
        post_data = {
            "team": new_team.id,
            "subsidiary": new_team.subsidiary.id,
            "company_0": "Foo",
            "company_1": new_team.subsidiary.company.id,
            'next': 'Další',
        }
        mail.outbox = []
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)

        self.assertRedirects(response, reverse('upravit_profil'))
        self.assertEqual(self.user_attendance.approved_for_team, "undecided")
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test@email.cz'])
        self.assertEqual(str(msg.subject), 'Testing campaign - žádost o ověření členství')

    @patch('dpnk.forms.logger')
    def test_team_out_of_campaign(self, mock_logger):
        city = mommy.make('City')
        other_campaign = mommy.make("Campaign")
        mommy.make('CityInCampaign', city=city, campaign=other_campaign)
        new_team = mommy.make('Team', campaign=other_campaign, subsidiary__city=city)
        post_data = {
            "team": new_team.id,
            "subsidiary": new_team.subsidiary.id,
            "company_0": "Foo",
            "company_1": new_team.subsidiary.company.id,
            'next': 'Další',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data)
        assert mock_logger.error.mock_calls == [
            call("Team not in campaign", extra={'team': new_team.id, 'subdomain': 'testing-campaign'}),
            call("Subsidiary in city that doesn't belong to this campaign", extra={'subsidiary': new_team.subsidiary}),
        ]
        self.assertContains(response, "Zvolený tým není dostupný v aktuální kampani")

    @patch('dpnk.forms.logger')
    def test_choose_nonexistent_city(self, mock_logger):
        city = mommy.make('City')
        other_campaign = mommy.make("Campaign")
        mommy.make('CityInCampaign', city=city, campaign=other_campaign)
        new_team = mommy.make('Team', campaign=self.campaign, subsidiary__city=city)
        post_data = {
            "team": new_team.id,
            "subsidiary": new_team.subsidiary.id,
            "company_0": "Foo",
            "company_1": new_team.subsidiary.company.id,
            'next': 'Další',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)
        mock_logger.error.assert_called_with("Subsidiary in city that doesn't belong to this campaign", extra={'subsidiary': ANY})
        self.assertContains(response, "Zvolená pobočka je registrována ve městě, které v aktuální kampani nesoutěží.")

    def test_no_team_set(self):
        company = mommy.make('Company')
        post_data = {
            'company_1': company.id,
            'subsidiary': '',
            'team': '',
            'next': 'Další',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data)
        self.assertContains(response, 'error_1_id_team')
        self.assertContains(
            response,
            '<select '
            'class="chainedselect form-control is-invalid chained-fk" '
            'data-auto_choose="false" '
            'data-chainfield="subsidiary" '
            'data-empty_label="--------" '
            'data-url="/chaining/filter/dpnk/Team/team_in_campaign_testing-campaign/subsidiary/dpnk/Subsidiary/company" '
            'data-value="null" '
            'id="id_team" '
            'name="team" '
            'name="team" '
            'required'
            '> </select>',
            html=True,
        )

    @patch('dpnk.models.team.logger')
    def test_choose_full_team(self, mock_logger):
        self.campaign.max_team_members = 2
        self.campaign.save()
        city = mommy.make('City')
        mommy.make('CityInCampaign', city=city, campaign=self.campaign)
        new_team = mommy.make(
            'Team',
            subsidiary__city=city,
            campaign=self.campaign,
            users=UserAttendancePaidRecipe.make(_quantity=3),
        )
        new_team.save()
        post_data = {
            "team": new_team.id,
            "subsidiary": new_team.subsidiary.id,
            "company_0": "Foo",
            "company_1": new_team.subsidiary.company.id,
            'next': 'Další',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)
        mock_logger.error.assert_called_with("Too many members in team", extra={'team': ANY})
        self.assertContains(response, "Tento tým již má plný počet členů")


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
        self.assertContains(response, '<a href="/upravit_trasu/">Vyplnit typickou trasu</a>', html=True)

    def test_dpnk_registration_unapproved_users(self):
        for team_member in self.user_attendance.team.all_members():
            if team_member != self.user_attendance:
                team_member.approved_for_team = 'undecided'
                team_member.save()
        self.user_attendance.track = None
        self.user_attendance.save()
        denorm.flush()
        response = self.client.get(reverse('registration_uncomplete'))
        self.assertContains(response, "Ve Vašem týmu jsou neschválení členové")

    def test_dpnk_registration_unapproved(self):
        self.user_attendance.approved_for_team = 'undecided'
        self.user_attendance.save()
        self.user_attendance.track = None
        self.user_attendance.save()
        denorm.flush()
        response = self.client.get(reverse('registration_uncomplete'))
        self.assertNotContains(response, "Ve Vašem týmu jsou neschválení členové")
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
        self.assertContains(
            response,
            "Nezapomeňte vyplnit odpovědi v následujících soutěžích: "
            "<a href='/otazka/dotaznik-spolecnosti/'>Dotazník společností</a>, "
            "<a href='/otazka/team-questionnaire/'>Dotazník týmů</a>!",
        )

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


class TripViewTests(ViewsLogon):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches', 'trips', 'commute_mode']

    def test_trip_view(self):
        trip = mommy.make(
            models.Trip,
            user_attendance=self.user_attendance,
            date=datetime.date(year=2010, month=11, day=20),
            direction='trip_from',
            commute_mode_id=1,
        )

        address = reverse('trip', kwargs={"date": trip.date, "direction": trip.direction})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)

    def test_trip_create(self):
        address = reverse('trip', kwargs={"date": datetime.date(year=2010, month=11, day=20), "direction": 'trip_from'})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)

    def test_trip_invalid_date(self):
        address = reverse('trip', kwargs={"date": "foo", 'direction': 'trip_to'})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 403)

    def test_trip_inactive_date(self):
        address = reverse('trip', kwargs={"date": datetime.date(year=2000, month=11, day=20), 'direction': 'trip_to'})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 404)

    def test_trip_invalid_direction(self):
        address = reverse('trip', kwargs={"date": datetime.date(year=2010, month=11, day=20), 'direction': 'foo'})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 403)

    def test_dpnk_views_trip_no_track_city(self):
        """ Test, that the location is changed accordingly to the user's city. """
        self.user_attendance.team.subsidiary.city = mommy.make("City", location="POINT(14.42 50.08)")
        self.user_attendance.team.subsidiary.save()

        trip = mommy.make(
            models.Trip,
            user_attendance=self.user_attendance,
            date=datetime.date(year=2010, month=11, day=20),
            direction='trip_from',
            commute_mode_id=1,
        )

        address = reverse('trip', kwargs={"date": trip.date, "direction": trip.direction})
        response = self.client.get(address)
        self.assertContains(response, '"center": [50.08, 14.42]')

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
        self.assertEqual(response.status_code, 302)
        user_attendance = models.UserAttendance.objects.get(pk=self.user_attendance.pk)
        self.assertEqual(user_attendance.get_distance(), 13.32)

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
        self.assertEqual(response.status_code, 302)
        user_attendance = models.UserAttendance.objects.get(pk=self.user_attendance.pk)
        self.assertEqual(user_attendance.get_distance(), 6.72)

    def test_dpnk_views_track_gpx_file_parsing_error(self):
        """ Test that error message is shown to the user where non-gpx file is submitted """
        address = reverse('upravit_trasu')
        with open('dpnk/test_files/DSC00002.JPG', 'rb') as gpxfile:
            post_data = {
                'dont_want_insert_track': False,
                'track': '',
                'gpx_file': gpxfile,
                'submit': 'Odeslat',
            }
            response = self.client.post(address, post_data)
        self.assertContains(
            response,
            '<strong>Chyba při načítání GPX souboru. Jste si jistí, že jde o GPX soubor?</strong>',
            html=True,
        )

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
        user_attendance = models.UserAttendance.objects.get(pk=self.user_attendance.pk)
        self.assertEqual(user_attendance.get_distance(), 0.74)

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
        user_attendance = models.UserAttendance.objects.get(pk=self.user_attendance.pk)
        self.assertEqual(user_attendance.track, None)
        self.assertEqual(user_attendance.get_distance(), 12)

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
        self.assertEqual(response.status_code, 200)
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
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches', 'trips', 'commute_mode']

    def test_statistics(self):
        address = reverse(views.statistics)
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "pocet-zaplacenych": 4,
                "pocet-soutezicich": 4,
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
        self.assertContains(response, '/trip/2010-11-14/trip_from')
        self.assertContains(response, '5,0')
        self.assertContains(response, 'Chůze/běh')
        self.assertContains(response, 'Podrobný přehled jízd')
        self.assertContains(response, '1. listopadu 2010')


@ddt
class TestNotLoggedIn(TestCase):
    """ Test, that views in which user must be logged on redirects to login page. """
    def setUp(self):
        self.client = Client(HTTP_HOST="testing-campaign.example.com")
        self.campaign = testing_campaign()

    @data(
        "application",
        "bike_repair",
        "company_admin_application",
        "company_admin_competition",
        "company_admin_competitions",
        "company_admin_related_competitions",
        "company_structure",
        "competitions",
        "edit_company",
        "edit_team",
        "emission_calculator",
        "other_team_members_results",
        "package",
        "pozvanky",
        "profil",
        "calendar",
        "questionnaire_competitions",
        "register_company",
        "registration_uncomplete",
        "rides_details",
        "team_members",
        "upravit_profil",
        "upravit_trasu",
        "zaslat_zadost_clenstvi",
        "zmenit_tym",
    )
    def test_not_logged_in(self, view):
        response = self.client.get(reverse(view))
        self.assertRedirects(response, '/login?next=%s' % reverse(view))

    def test_invoices(self):
        mommy.make(
            "dpnk.Phase",
            campaign=testing_campaign,
            phase_type="invoices",
            date_from="2010-1-1",
        )
        view = 'invoices'
        response = self.client.get(reverse(view))
        self.assertRedirects(response, '/login?next=%s' % reverse(view))

    @data(
        "company_admin_pay_for_users",
        "payment",
        "payment_beneficiary",
        "typ_platby",
    )
    def test_not_logged_in_payment_phase(self, view):
        mommy.make(
            "dpnk.Phase",
            campaign=testing_campaign,
            phase_type="payment",
            date_from="2010-1-1",
        )
        response = self.client.get(reverse(view))
        self.assertRedirects(response, '/login?next=%s' % reverse(view))


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=2),
    MEDIA_ROOT="dpnk/test_files",
)
class ViewsTestsRegistered(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches', 'trips', 'commute_mode']

    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.testserver")
        self.client.force_login(models.User.objects.get(username='test'), settings.AUTHENTICATION_BACKENDS[0])
        util.rebuild_denorm_models(models.Team.objects.filter(pk=1))
        util.rebuild_denorm_models(models.UserAttendance.objects.filter(pk__in=[1115, 2115, 1015]))
        self.user_attendance = models.UserAttendance.objects.get(pk=1115)
        self.assertTrue(self.user_attendance.entered_competition())

    def test_dpnk_questionnaire_answers(self):
        competition = models.Competition.objects.filter(slug="quest")
        competition.get().recalculate_results()
        address = reverse('questionnaire_answers_all', kwargs={'competition_slug': "quest"})
        response = self.client.get(address)
        self.assertContains(response, '<a href="%smodranska-rokle.gpx" target="_blank">modranska-rokle.gpx</a>' % settings.MEDIA_URL, html=True)
        self.assertContains(response, '<img src="%sDSC00002.JPG.250x250_q85.jpg" width="250" height="188">' % settings.MEDIA_URL, html=True)
        self.assertContains(response, 'Answer without attachment')
        self.assertContains(response, 'Bez přílohy')


    def test_dpnk_views_create_trip(self):
        date = datetime.date(year=2010, month=11, day=2)
        direction = "trip_to"
        address = reverse('trip', kwargs={"date": str(date), "direction": direction})
        with open('dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                'gpx_file': gpxfile,
                'direction': direction,
                'date': date,
                'commute_mode': 1,
                'user_attendance': self.user_attendance.pk,
                'origin': reverse('calendar'),
                'submit': 'Odeslat',
            }
            response = self.client.post(address, post_data)
        self.assertRedirects(response, reverse("calendar"))
        trip = models.Trip.objects.get(date=date, direction=direction, user_attendance=self.user_attendance)
        self.assertEqual(trip.distance, 13.32)

    def test_dpnk_views_create_trip_error(self):
        address = reverse('trip', kwargs={"date": "foo bad date", "direction": "trip_from"})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 403)

    def test_dpnk_views_create_trip_inactive_day(self):
        date = datetime.date(year=2010, month=12, day=1)
        direction = "trip_from"
        address = reverse('trip', kwargs={"date": date, "direction": direction})
        with open('dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                'gpx_file': gpxfile,
                'direction': direction,
                'date': date,
                'user_attendance': self.user_attendance.pk,
                'submit': 'Odeslat',
            }
            response = self.client.post(address, post_data)
            self.assertEqual(response.status_code, 405)
        exists = models.Trip.objects.filter(date=date, direction=direction, user_attendance=self.user_attendance).exists()
        self.assertEqual(exists, False)

    def test_dpnk_competitions_page(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        util.rebuild_denorm_models(models.Team.objects.all())
        for competition in models.Competition.objects.all():
            competition.recalculate_results()
        competition = models.Competition.objects.filter(slug="quest")
        competition.get().recalculate_results()
        response = self.client.get(reverse('competitions'))
        self.assertContains(response, 'vnitrofiremní soutěž na pravidelnost jednotlivců organizace Testing company')
        self.assertContains(response, '<p>1. místo z 1 organizací</p>', html=True)

    def test_dpnk_length_competitions_page(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        util.rebuild_denorm_models(models.Team.objects.all())
        for competition in models.Competition.objects.all():
            competition.recalculate_results()
        competition = models.Competition.objects.filter(slug="quest")
        competition.get().recalculate_results()
        response = self.client.get(reverse('length_competitions'))
        self.assertContains(response, 'soutěž na vzdálenost jednotlivců  ve městě Testing city')

    def test_dpnk_competitions_page_change(self):
        response = self.client.get(reverse('competitions'))
        self.assertContains(response, '<a href="/vysledky_souteze/FQ-LB/#row-0">Výsledky</a>', html=True)

    def test_dpnk_length_competitions_page_change(self):
        response = self.client.get(reverse('length_competitions'))
        self.assertContains(response, '<h4>Výkonnost společností</h4>', html=True)
        self.assertContains(
            response,
            '<i>soutěž na vzdálenost jednotlivců  ve městě Testing city pro muže pro cesty s prostředky Kolo, Chůze/běh</i>',
            html=True,
        )

    def test_dpnk_questionnaire_competitions_page_change(self):
        response = self.client.get(reverse('questionnaire_competitions'))
        self.assertContains(response, '<h4>Dotazník</h4>', html=True)
        self.assertContains(response, '<a href="/otazka/quest/">Vyplnit odpovědi</a>', html=True)
        self.assertContains(response, '<i>dotazník týmů  ve městě Testing city</i>', html=True)

    @override_settings(
        FAKE_DATE=datetime.date(year=2009, month=11, day=20),
    )
    def test_dpnk_competitions_page_before(self):
        response = self.client.get(reverse('length_competitions'))
        self.assertContains(response, 'Výkonnost ve městě')
        self.assertContains(response, 'Tato soutěž ještě nezačala')

    @override_settings(
        FAKE_DATE=datetime.date(year=2016, month=11, day=20),
    )
    def test_dpnk_competitions_page_finished(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        util.rebuild_denorm_models(models.Team.objects.all())
        for competition in models.Competition.objects.all():
            competition.recalculate_results()
        competition = models.Competition.objects.filter(slug="quest")
        competition.get().recalculate_results()
        response = self.client.get(reverse('questionnaire_competitions'))
        self.assertContains(response, '<i>dotazník jednotlivců</i>', html=True)
        self.assertContains(response, "<p>16,2b.</p>", html=True)
        response = self.client.get(reverse('competitions'))
        self.assertContains(response, "<p>1. místo z 1 týmů</p>", html=True)
        self.assertContains(response, "<p>2,9&nbsp;%</p>", html=True)
        self.assertContains(response, "<p>2 z 69 jízd</p>", html=True)
        self.assertContains(response, "<p>1. místo z 2 jednotlivců</p>", html=True)
        response = self.client.get(reverse('length_competitions'))
        self.assertContains(response, "<p>161,9&nbsp;km</p>", html=True)


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=2),
    MEDIA_ROOT="dpnk/test_files",
)
@ddt
class ViewsTestsUnregistered(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches', 'trips']

    def setUp(self):
        super().setUp()
        models.Payment.objects.all().delete()
        self.client = Client(HTTP_HOST="testing-campaign.testserver")
        self.client.force_login(models.User.objects.get(username='test'), settings.AUTHENTICATION_BACKENDS[0])

        util.rebuild_denorm_models(models.Team.objects.filter(pk__in=[1, 3]))
        util.rebuild_denorm_models(models.UserAttendance.objects.filter(pk__in=[1115, 2115, 1015]))
        self.user_attendance = models.UserAttendance.objects.get(pk=1115)
        self.assertNotEqual(self.user_attendance.entered_competition_reason(), True)

    @data(
        ('profil', {}),
        ('rides_details', {}),
        ('calendar', {}),
        # New trip
        ('trip', {"date": "2010-11-2", "direction": "trip_to"}),
        # Existing trip
        ('trip', {"date": "2010-11-2", "direction": "trip_from"}),
        # Old existing trip
        ('trip', {"date": "2009-11-1", "direction": "trip_to"}),
    )
    def test_registration_redirects(self, view):
        name, kwargs = view
        address = reverse(name, kwargs=kwargs)
        response = self.client.get(address)
        self.assertRedirects(response, reverse("typ_platby"), msg_prefix="%s did not redirect to 'typ_platby'" % address)
