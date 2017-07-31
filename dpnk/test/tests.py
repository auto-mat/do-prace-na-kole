# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2015 o.s. Auto*Mat
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
from unittest.mock import ANY, MagicMock, patch

import denorm

import django
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import Client, RequestFactory, TestCase
from django.test.utils import override_settings

from dpnk import actions, company_admin_views, models, util, views
from dpnk.test.util import ClearCacheMixin, DenormMixin
from dpnk.test.util import print_response  # noqa

from freezegun import freeze_time

from price_level import models as price_level_models

import settings


class PaymentSuccessTests(ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users']

    def setUp(self):
        self.factory = RequestFactory()
        self.user_attendance = models.UserAttendance.objects.get(pk=1115)
        self.session_id = "2075-1J1455206457"
        self.trans_id = "2055"
        models.Payment.objects.create(
            session_id=self.session_id,
            user_attendance=self.user_attendance,
            amount=150,
        )

    def test_payment_succesfull(self):
        kwargs = {"trans_id": self.trans_id, "session_id": self.session_id, "pay_type": "kb"}
        address = reverse('payment_successfull', kwargs=kwargs)
        request = self.factory.get(address)
        request.user = self.user_attendance.userprofile.user
        request.user_attendance = self.user_attendance
        request.subdomain = "testing-campaign"
        views.PaymentResult.as_view()(request, success=True, **kwargs)
        payment = models.Payment.objects.get(session_id=self.session_id)
        self.assertEquals(payment.pay_type, "kb")

    def test_payment_unsuccesfull(self):
        kwargs = {"trans_id": self.trans_id, "session_id": self.session_id, "pay_type": "kb", "error": 123}
        address = reverse('payment_unsuccessfull', kwargs=kwargs)
        request = self.factory.get(address)
        request.user = self.user_attendance.userprofile.user
        request.user_attendance = self.user_attendance
        request.subdomain = "testing-campaign"
        views.PaymentResult.as_view()(request, success=False, **kwargs)
        payment = models.Payment.objects.get(session_id=self.session_id)
        self.assertEquals(payment.pay_type, "kb")
        self.assertEquals(payment.error, 123)


class PaymentTests(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches']

    def setUp(self):
        super().setUp()
        util.rebuild_denorm_models(models.Team.objects.filter(pk=1))
        util.rebuild_denorm_models(models.UserAttendance.objects.filter(pk=1115))

    def test_no_payment_no_admission(self):
        campaign = models.Campaign.objects.get(pk=339)
        price_level_models.PriceLevel.objects.all().delete()
        campaign.save()
        models.UserAttendance.objects.get(pk=1115).save()
        denorm.flush()
        user = models.UserAttendance.objects.get(pk=1115)
        self.assertEquals(user.payment_status, 'no_admission')
        self.assertEquals(user.representative_payment, None)
        self.assertEquals(user.payment_class(), 'success')
        self.assertEquals(str(user.get_payment_status_display()), 'neplatí se')

    def test_payment_waiting(self):
        payment = models.Payment.objects.get(pk=4)
        payment.status = 1
        payment.save()
        denorm.flush()
        user = models.UserAttendance.objects.get(pk=1115)
        self.assertEquals(user.payment_status, 'waiting')
        self.assertEquals(user.representative_payment, payment)
        self.assertEquals(user.payment_class(), 'warning')
        self.assertEquals(str(user.get_payment_status_display()), 'nepotvrzeno')

    def test_payment_done(self):
        user = models.UserAttendance.objects.get(pk=1115)
        payment = models.Payment.objects.get(pk=4)
        self.assertEquals(user.payment_status, 'done')
        self.assertEquals(user.representative_payment, payment)
        self.assertEquals(user.payment_class(), 'success')
        self.assertEquals(str(user.get_payment_status_display()), 'zaplaceno')

    def test_payment_unknown(self):
        payment = models.Payment.objects.get(pk=4)
        payment.status = 123
        payment.save()
        denorm.flush()
        user = models.UserAttendance.objects.get(pk=1115)
        self.assertEquals(user.payment_status, 'unknown')
        self.assertEquals(user.representative_payment, payment)
        self.assertEquals(user.payment_class(), 'warning')
        self.assertEquals(str(user.get_payment_status_display()), 'neznámý')

    def test_payment_unknown_none(self):
        models.Payment.objects.all().delete()
        util.rebuild_denorm_models(models.Team.objects.filter(pk__in=[1, 3]))
        util.rebuild_denorm_models(models.UserAttendance.objects.filter(pk=1016))
        user = models.UserAttendance.objects.get(pk=1016)
        self.assertEquals(user.payment_status, 'none')
        self.assertEquals(user.representative_payment, None)
        self.assertEquals(user.payment_class(), 'error')
        self.assertEquals(str(user.get_payment_status_display()), 'žádné platby')


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
    PAYU_KEY_1='123456789',
    PAYU_KEY_2='98764321',
)
@freeze_time("2010-11-20 12:00")
class PayuTests(ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches']

    def setUp(self):
        self.client = Client(HTTP_HOST="testing-campaign.testserver")

    @patch('http.client.HTTPSConnection.request')
    @patch('http.client.HTTPSConnection.getresponse')
    def payment_status_view(
        self, payu_response, payu_request, session_id='2075-1J1455206433',
        amount="15000", trans_sig='ae6f4b9f8fbdbb506edf4eeb1cebcee0', sig='1af62397cfb6e6de5295325801239e4f',
        post_sig="b6b29bb8437f9e2486fbe5555673372d",
    ):
        payment_post_data = OrderedDict([
            ('pos_id', '2075-1'),
            ('session_id', session_id),
            ('ts', '1'),
        ])
        payment_post_data['sig'] = sig
        payment_return_value = OrderedDict([
            ("trans_pos_id", "2075-1"),
            ("trans_session_id", session_id),
            ("trans_order_id", "321"),
            ("trans_status", "99"),
            ("trans_amount", amount),
            ("trans_desc", "desc"),
            ("trans_ts", "1"),
        ])
        payment_return_value['trans_sig'] = trans_sig
        payment_return_value.update([
            ("trans_pay_type", "kb"),
            ("trans_recv", "2016-1-1"),
        ])
        payment_return_value_bytes = bytes("\n".join(["%s: %s" % (u, payment_return_value[u]) for u in payment_return_value]), "utf-8")
        payu_response.return_value.read.return_value = payment_return_value_bytes
        response = self.client.post(reverse('payment_status'), payment_post_data)
        payu_request.assert_called_with(
            'POST',
            '/paygw/UTF/Payment/get/txt/',
            'pos_id=2075-1&session_id=%(session_id)s&ts=1290254400&sig=%(trans_sig)s' % {"trans_sig": post_sig, "session_id": session_id, },
            {
                'Content-type': 'application/x-www-form-urlencoded',
                'Accept': 'text/plain',
            },
        )
        return response

    def test_dpnk_payment_status_view(self):
        response = self.payment_status_view()
        self.assertContains(response, "OK")
        payment = models.Payment.objects.get(pk=3)
        self.assertEquals(payment.pay_type, "kb")
        self.assertEquals(payment.amount, 150)
        self.assertEquals(payment.status, 99)

    @patch('dpnk.views.logger')
    def test_dpnk_payment_status_bad_amount(self, mock_logger):
        response = self.payment_status_view(amount="15300", trans_sig='ae18ec7f141c252e692d470f4c1744c9')
        self.assertContains(response, "Bad amount", status_code=400)
        payment = models.Payment.objects.get(pk=3)
        self.assertEquals(payment.pay_type, None)
        self.assertEquals(payment.amount, 150)
        self.assertEquals(payment.status, 0)
        mock_logger.error.assert_called_with(
            "Payment amount doesn't match",
            extra={
                'request': ANY,
                'pay_type': None,
                'expected_amount': 150,
                'payment_response': ANY,
                'status': 0,
            },
        )

    def test_dpnk_payment_status_view_create_round(self):
        """ Test that payment amount is rounded to whole crowns """
        response = self.payment_status_view(
            session_id='2075-1J1455206434', amount="15150",
            sig='4f59d25cd3dadaf03bef947bb0d9e1b9', trans_sig='5a1fa473feba5dcd7c0d8bd21b1aecec',
            post_sig='445db4f3e11bfa16f0221b0272820058',
        )
        self.assertContains(response, "OK")
        payment = models.Payment.objects.get(session_id='2075-1J1455206434')
        self.assertEquals(payment.pay_type, "kb")
        self.assertEquals(payment.amount, 151)

    def test_dpnk_payment_status_view_create(self):
        response = self.payment_status_view(
            session_id='2075-1J1455206434', amount="15100",
            sig='4f59d25cd3dadaf03bef947bb0d9e1b9', trans_sig='c490e30293fe0a96d08b62107accafe8',
            post_sig='445db4f3e11bfa16f0221b0272820058',
        )
        self.assertContains(response, "OK")
        payment = models.Payment.objects.get(session_id='2075-1J1455206434')
        self.assertEquals(payment.pay_type, "kb")
        self.assertEquals(payment.amount, 151)


def create_get_request(factory, user, post_data={}, address="", subdomain="testing-campaign"):
    request = factory.get(address, post_data)
    request.user = user
    request.subdomain = subdomain
    return request


def create_post_request(factory, user, post_data={}, address="", subdomain="testing-campaign"):
    request = factory.post(address, post_data)
    request.user = user
    request.subdomain = subdomain
    return request


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=12, day=1),
)
class TestCompanyAdminViews(ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'company_competition']

    def setUp(self):
        self.factory = RequestFactory()
        self.user_attendance = models.UserAttendance.objects.get(pk=1115)

    def test_dpnk_company_admin_create_competition(self):
        post_data = {
            'name': 'testing company competition',
            'competition_type': 'length',
            'competitor_type': 'single_user',
            'submit': 'Odeslat',
        }
        request = create_post_request(self.factory, self.user_attendance.userprofile.user, post_data)
        response = company_admin_views.CompanyCompetitionView.as_view()(request, success=True)
        self.assertEquals(response.url, reverse('company_admin_competitions'))
        competition = models.Competition.objects.get(
            company=self.user_attendance.get_asociated_company_admin().first().administrated_company,
            competition_type='length',
        )
        self.assertEquals(competition.name, 'testing company competition')

        slug = competition.slug
        post_data['name'] = 'testing company competition fixed'
        request = create_post_request(self.factory, self.user_attendance.userprofile.user, post_data)
        response = company_admin_views.CompanyCompetitionView.as_view()(request, success=True, competition_slug=slug)
        self.assertEquals(response.url, reverse('company_admin_competitions'))
        competition = models.Competition.objects.get(
            company=self.user_attendance.get_asociated_company_admin().first().administrated_company,
            competition_type='length',
        )
        self.assertEquals(competition.name, 'testing company competition fixed')

    def test_dpnk_company_admin_create_competition_name_exists(self):
        post_data = {
            'name': 'Pravidelnost společnosti',
            'competition_type': 'length',
            'competitor_type': 'single_user',
            'submit': 'Odeslat',
        }
        request = create_post_request(self.factory, self.user_attendance.userprofile.user, post_data)
        response = company_admin_views.CompanyCompetitionView.as_view()(request, success=True)
        self.assertContains(response, "<strong>Položka Soutěžní kategorie s touto hodnotou v poli Jméno soutěže již existuje.</strong>", html=True)

    @override_settings(
        MAX_COMPETITIONS_PER_COMPANY=0,
    )
    def test_dpnk_company_admin_create_competition_max_competitions(self):
        request = create_get_request(self.factory, self.user_attendance.userprofile.user)
        request.resolver_match = {"url_name": "company_admin_competition"}
        response = company_admin_views.CompanyCompetitionView.as_view()(request, success=True)
        self.assertContains(response, "Překročen maximální počet soutěží pro organizaci.")

    def test_dpnk_company_admin_create_competition_no_permission(self):
        request = create_get_request(self.factory, self.user_attendance.userprofile.user)
        request.resolver_match = {"url_name": "company_admin_competition"}
        response = company_admin_views.CompanyCompetitionView.as_view()(request, success=True, competition_slug="FQ-LB")
        self.assertContains(response, "K editování této soutěže nemáte oprávnění.")

    def test_dpnk_company_admin_competitions_view(self):
        request = create_get_request(self.factory, self.user_attendance.userprofile.user)
        request.resolver_match = {"url_name": "company_admin_competitions"}
        response = company_admin_views.CompanyCompetitionsShowView.as_view()(request, success=True)
        self.assertContains(response, "Pravidelnost společnosti")


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=2),
    MEDIA_ROOT="dpnk/test_files",
)
class ViewsTestsRegistered(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches', 'trips']

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
        actions.normalize_questionnqire_admissions(None, None, competition)
        competition.get().recalculate_results()
        address = reverse('questionnaire_answers_all', kwargs={'competition_slug': "quest"})
        response = self.client.get(address)
        self.assertContains(response, '<a href="%smodranska-rokle.gpx" target="_blank">modranska-rokle.gpx</a>' % settings.MEDIA_URL, html=True)
        self.assertContains(response, '<img src="%sDSC00002.JPG.250x250_q85.jpg" width="250" height="188">' % settings.MEDIA_URL, html=True)
        self.assertContains(response, 'Answer without attachment')
        self.assertContains(response, 'Bez přílohy')

    @patch('slumber.API')
    def test_dpnk_profile_page(self, slumber_mock):
        models.Answer.objects.filter(pk__in=(2, 3, 4)).delete()
        m = MagicMock()
        m.feed.get.return_value = (
            {
                'published': '2010-01-01',
                'start_date': '2010-01-01',
                'url': 'http://www.test.cz',
                'title': 'Testing title',
                'excerpt': 'Testing excerpt',
                'image': 'http://www.test.cz',
            },
        )
        slumber_mock.return_value = m
        response = self.client.get(reverse('profil'))
        self.assertContains(
            response,
            '<img src="%sDSC00002.JPG.360x360_q85.jpg" width="360" height="270" alt="Příspěvek do kreativní soutěže">' % settings.MEDIA_URL,
            html=True,
        )
        self.assertContains(response, '<a href="http://www.dopracenakole.cz/locations/testing-city">Testing city</a>', html=True)
        self.assertContains(response, 'Novinky ve městě')
        self.assertContains(response, 'Testing title')
        self.assertContains(response, 'Testing excerpt')

    @patch('slumber.API')
    def test_dpnk_profile_page_blank_feed(self, slumber_mock):
        models.Answer.objects.filter(pk__in=(2, 3, 4)).delete()
        m = MagicMock()
        m.feed.get.return_value = []
        slumber_mock.return_value = m
        response = self.client.get(reverse('profil'))
        self.assertContains(
            response,
            '<div class="dpnk-content-box"></div>',
            html=True,
        )

    @patch('slumber.API')
    def test_dpnk_profile_page_link(self, slumber_api):
        models.Answer.objects.filter(pk__in=(2, 3, 4)).delete()
        m = MagicMock()
        m.feed.get.return_value = []
        slumber_api.return_value = m
        response = self.client.get(reverse('profil'))
        self.assertContains(
            response,
            '<a href="/questionnaire_answers/quest/" title="Všechny příspěvky z této soutěže">'
            '<img src="%sDSC00002.JPG.360x360_q85.jpg" width="360" height="270" alt="Příspěvek do kreativní soutěže">'
            '</a>' % settings.MEDIA_URL,
            html=True,
        )

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=11, day=8),
    )
    @patch('slumber.API')
    def test_dpnk_rides_view_key_error(self, slumber_api):
        m = MagicMock()
        m.feed.get.return_value = []
        slumber_api.return_value = m
        "Test if the rides saves, when between loading and sending the form date changes."
        "The non-active days should not be saved, but active days should be saved"
        post_data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '2',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-id': 101,
            'form-0-commute_mode': 3,
            'form-0-distance': '6',
            'form-0-direction': 'trip_from',
            'form-0-user_attendance': 1115,
            'form-0-date': '2010-11-01',
            'initial-form-0-date': '2010-11-01',
            'form-1-id': 103,
            'form-1-commute_mode': 1,
            'form-1-distance': '34',
            'form-1-direction': 'trip_from',
            'form-1-user_attendance': 1115,
            'form-1-date': '2010-11-02',
            'initial-form-1-date': '2010-11-02',
            'submit': 'Odeslat',
        }
        response = self.client.post(reverse('profil'), post_data, follow=True)
        self.assertContains(response, 'form-0-commute_mode')
        self.assertContains(response, 'form-3-commute_mode')
        self.assertContains(response, '<th colspan="2" scope="row" class="date"> út 2. 11. <span>2010</span> </th>', html=True)
        self.assertContains(response, '<th colspan="2" scope="row" class="date"> st 3. 11. <span>2010</span></th>', html=True)
        self.assertEquals(self.user_attendance.user_trips.count(), 5)
        self.assertEquals(models.Trip.objects.get(pk=101).distance, 5)
        self.assertEquals(models.Trip.objects.get(pk=103).distance, 34)

        denorm.flush()
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        self.assertEquals(user_attendance.trip_length_total, 39.0)
        self.assertEquals(user_attendance.team.get_length(), 13.0)

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=11, day=1),
    )
    @patch('slumber.API')
    def test_dpnk_rides_view_key_error_km(self, slumber_api):
        """ Test, that if user sends "6,0 km", the application wont fail. """
        m = MagicMock()
        m.feed.get.return_value = []
        slumber_api.return_value = m
        post_data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-id': 101,
            'form-0-commute_mode': 2,
            'form-0-distance': '6,0 km',
            'form-0-direction': 'trip_from',
            'form-0-user_attendance': 1115,
            'form-0-date': '2010-11-01',
            'initial-form-0-date': '2010-11-01',
            'form-1-id': None,
            'form-1-commute_mode': 1,
            'form-1-distance': '34',
            'form-1-direction': 'trip_to',
            'form-1-user_attendance': 1115,
            'form-1-date': '2010-11-01',
            'initial-form-1-date': '2010-11-01',
            'submit': 'Uložit jízdy',
        }
        response = self.client.post(reverse('profil'), post_data, follow=True)
        self.assertContains(
            response,
            '<div class="alert alert-danger alert-dismissable alert-link">'
            '    <button class="close" type="button" data-dismiss="alert" aria-hidden="true">&#215;</button>'
            '    Zadejte číslo.<br>'
            '    Musíte vyplnit vzdálenost'
            '</div>',
            html=True,
        )

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=11, day=1),
    )
    @patch('slumber.API')
    def test_dpnk_rides_view_key_error_not_enough_km_by_foot(self, slumber_api):
        """ Test, that if user sends "1,2 km", it is too few when choosen type by foot. """
        m = MagicMock()
        m.feed.get.return_value = []
        slumber_api.return_value = m
        post_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-id': 101,
            'form-0-commute_mode': 2,
            'form-0-distance': '1,2',
            'form-0-direction': 'trip_from',
            'form-0-user_attendance': 1115,
            'form-0-date': '2010-11-01',
            'initial-form-0-date': '2010-11-01',
            'initial-form-1-date': '2010-11-01',
            'submit': 'Uložit jízdy',
        }
        response = self.client.post(reverse('profil'), post_data, follow=True)
        self.assertContains(
            response,
            '<button class="close" type="button" data-dismiss="alert" aria-hidden="true">&#215;</button>',
            html=True,
        )

    @patch('slumber.API')
    def test_dpnk_rides_view(self, slumber_api):
        m = MagicMock()
        m.feed.get.return_value = []
        slumber_api.return_value = m
        response = self.client.get(reverse('profil'))
        self.assertContains(response, 'form-0-commute_mode')
        self.assertContains(response, 'form-1-commute_mode')
        self.assertEquals(self.user_attendance.user_trips.count(), 5)
        post_data = {
            'form-TOTAL_FORMS': '4',
            'form-INITIAL_FORMS': '2',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-id': 101,
            'form-0-commute_mode': 2,
            'form-0-distance': '28.89',
            'form-0-direction': 'trip_to',
            'form-0-user_attendance': 1115,
            'form-0-date': '2010-11-01',
            'initial-form-0-date': '2010-11-01',
            'form-2-id': '',
            'form-2-commute_mode': 1,
            'form-2-distance': '2,34',
            'form-2-direction': 'trip_from',
            'form-2-user_attendance': 1115,
            'form-2-date': '2010-11-01',
            'initial-form-2-date': '2010-11-01',
            'form-3-id': '',
            'form-3-commute_mode': 4,
            'form-3-distance': '',
            'form-3-direction': 'trip_to',
            'form-3-user_attendance': 1115,
            'form-3-date': '2010-11-02',
            'initial-form-3-date': '2010-11-02',
            'form-1-id': 103,
            'form-1-commute_mode': 3,
            'form-1-distance': '3',
            'form-1-direction': 'trip_from',
            'form-1-user_attendance': 1116,
            'form-1-date': '2010-11-04',
            'initial-form-1-date': '2010-11-04',
            'submit': 'Odeslat',
        }
        response = self.client.post(reverse('profil'), post_data, follow=True)
        self.assertContains(response, 'form-1-commute_mode')
        self.assertContains(
            response,
            '<td>Uražená započítaná vzdálenost: 31,23&nbsp;km (<a href="/jizdy-podrobne/">Podrobný přehled jízd</a>)</td>',
            html=True,
        )
        self.assertContains(
            response,
            '<td>Pravidelnost: 66,7&nbsp;%</td>',
            html=True,
        )
        self.assertContains(
            response,
            '<td>Ušetřené množství oxidu uhličitého: 4 028,7&nbsp;g (<a href="/emisni_kalkulacka/">Emisní kalkulačka</a>)</td>',
            html=True,
        )
        self.assertEquals(self.user_attendance.user_trips.count(), 7)
        self.assertEquals(models.Trip.objects.get(pk=101).distance, 28.89)

        trip1 = models.Trip.objects.get(pk=103)
        self.assertEquals(trip1.distance, 3)
        self.assertEquals(trip1.user_attendance.pk, 1115)
        self.assertEquals(trip1.commute_mode.slug, "by_other_vehicle")
        self.assertEquals(trip1.date, datetime.date(year=2010, month=11, day=2))

        trip2 = models.Trip.objects.get(date=datetime.date(year=2010, month=11, day=1), direction='trip_from')
        self.assertEquals(trip2.commute_mode.slug, 'bicycle')
        self.assertEquals(trip2.user_attendance.pk, 1115)
        self.assertEquals(trip2.distance, 2.34)

        trip3 = models.Trip.objects.get(date=datetime.date(year=2010, month=11, day=2), direction='trip_to')
        self.assertEquals(trip3.commute_mode.slug, 'no_work')
        self.assertEquals(trip3.user_attendance.pk, 1115)
        self.assertEquals(trip3.distance, None)

        denorm.flush()
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        self.assertEquals(user_attendance.trip_length_total, 31.23)
        self.assertEquals(user_attendance.team.get_length(), 10.41)

    def test_dpnk_views_create_gpx_file(self):
        date = datetime.date(year=2010, month=11, day=1)
        direction = "trip_from"
        address = reverse('gpx_file_create', kwargs={"date": date, "direction": direction})
        with open('dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                'file': gpxfile,
                'direction': direction,
                'trip_date': date,
                'user_attendance': self.user_attendance.pk,
                'submit': 'Odeslat',
            }
            response = self.client.post(address, post_data)
            self.assertRedirects(response, reverse('profil'), fetch_redirect_response=False)
        gpxfile = models.GpxFile.objects.get(trip_date=date, direction=direction, user_attendance=self.user_attendance)
        self.assertEquals(gpxfile.trip.distance, 13.32)

    def test_dpnk_views_create_gpx_file_inactive_day(self):
        date = datetime.date(year=2010, month=12, day=1)
        direction = "trip_from"
        address = reverse('gpx_file_create', kwargs={"date": date, "direction": direction})
        with open('dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                'file': gpxfile,
                'direction': direction,
                'trip_date': date,
                'user_attendance': self.user_attendance.pk,
                'submit': 'Odeslat',
            }
            response = self.client.post(address, post_data)
            self.assertRedirects(response, reverse('profil'), fetch_redirect_response=False)
        gpxfile = models.GpxFile.objects.get(trip_date=date, direction=direction, user_attendance=self.user_attendance)
        self.assertEquals(gpxfile.trip.distance, None)

    def test_dpnk_competitions_page(self):
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        util.rebuild_denorm_models(models.Team.objects.all())
        for competition in models.Competition.objects.all():
            competition.recalculate_results()
        competition = models.Competition.objects.filter(slug="quest")
        actions.normalize_questionnqire_admissions(None, None, competition)
        competition.get().recalculate_results()
        response = self.client.get(reverse('competitions'))
        self.assertContains(response, 'vnitrofiremní soutěž na pravidelnost jednotlivců organizace Testing company')
        self.assertContains(response, '<p>1. místo z 1 společností</p>', html=True)
        self.assertContains(response, 'soutěž na vzdálenost jednotlivců  ve městě Testing city')

    def test_dpnk_competitions_page_change(self):
        response = self.client.get(reverse('competitions'))
        self.assertContains(
            response,
            '<i>soutěž na vzdálenost jednotlivců  ve městě Testing city pro muže pro cesty s prostředky Kolo, Chůze/běh</i>',
            html=True,
        )
        self.assertContains(response, '<h4>Výkonnost společností</h4>', html=True)
        self.assertContains(response, '<a href="/vysledky_souteze/FQ-LB/#row-1">Výsledky</a>', html=True)

    def test_dpnk_questionnaire_competitions_page_change(self):
        response = self.client.get(reverse('questionnaire_competitions'))
        self.assertContains(response, '<h4>Dotazník</h4>', html=True)
        self.assertContains(response, '<a href="/otazka/quest/">Vyplnit odpovědi</a>', html=True)
        self.assertContains(response, '<i>dotazník týmů  ve městě Testing city</i>', html=True)

    @override_settings(
        FAKE_DATE=datetime.date(year=2009, month=11, day=20),
    )
    def test_dpnk_competitions_page_before(self):
        response = self.client.get(reverse('competitions'))
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
        actions.normalize_questionnqire_admissions(None, None, competition)
        competition.get().recalculate_results()
        response = self.client.get(reverse('questionnaire_competitions'))
        self.assertContains(response, '<i>dotazník jednotlivců</i>', html=True)
        self.assertContains(response, "<p>16,2b.</p>", html=True)
        response = self.client.get(reverse('competitions'))
        self.assertContains(response, "<p>1. místo z 1 týmů</p>", html=True)
        self.assertContains(response, "<p>1,4&nbsp;%</p>", html=True)
        self.assertContains(response, "<p>1 z 69 jízd</p>", html=True)
        self.assertContains(response, "<p>1. místo z 2 jednotlivců</p>", html=True)
        self.assertContains(response, "<p>5,0&nbsp;km</p>", html=True)


class TestTeams(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions']

    def setUp(self):
        super().setUp()
        util.rebuild_denorm_models(models.UserAttendance.objects.filter(pk__in=[1115, 2115, 1015]))
        util.rebuild_denorm_models(models.Team.objects.filter(pk=1))

    def test_member_count_update(self):
        team = models.Team.objects.get(id=1)
        self.assertEqual(team.member_count, 3)
        campaign = models.Campaign.objects.get(pk=339)
        user = models.User.objects.create(first_name="Third", last_name="User", username="third_user")
        userprofile = models.UserProfile.objects.create(user=user)
        user_attendance = models.UserAttendance.objects.create(team=team, campaign=campaign, userprofile=userprofile, approved_for_team='approved')
        models.Payment.objects.create(status=99, amount=1, user_attendance=user_attendance)
        denorm.flush()
        team = models.Team.objects.get(id=1)
        self.assertEqual(team.member_count, 4)


class ModelTests(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches']

    def setUp(self):
        super().setUp()
        util.rebuild_denorm_models(models.Team.objects.filter(pk=1))

    def test_payment_type_string(self):
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        user_attendance.save()
        call_command('denorm_flush')
        self.assertEquals(user_attendance.payment_type_string(), "ORGANIZACE PLATÍ FAKTUROU")

    def test_payment_type_string_none_type(self):
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        user_attendance.representative_payment = models.Payment(pay_type=None)
        self.assertEquals(user_attendance.payment_type_string(), None)


class DenormTests(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches']

    def test_name_with_members(self):
        util.rebuild_denorm_models(models.Team.objects.filter(pk__in=[2, 3]))
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        user_attendance.team.save()
        call_command('denorm_flush')
        self.assertEquals(user_attendance.team.name_with_members, "Testing team 1 (Nick, Testing User 1, Registered User 1)")
        self.assertEquals(user_attendance.team.unapproved_member_count, 0)
        self.assertEquals(user_attendance.team.member_count, 3)
        user_attendance.userprofile.nickname = "Testing nick"
        user_attendance.userprofile.save()
        call_command('denorm_flush')
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        self.assertEquals(user_attendance.team.name_with_members, "Testing team 1 (Nick, Testing nick, Registered User 1)")
        self.assertEquals(user_attendance.team.unapproved_member_count, 0)
        self.assertEquals(user_attendance.team.member_count, 3)

    def test_name_with_members_delete_userattendance(self):
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        user_attendance.team.save()
        call_command('denorm_flush')
        self.assertEquals(user_attendance.team.name_with_members, "Testing team 1 (Nick, Testing User 1, Registered User 1)")
        self.assertEquals(user_attendance.team.unapproved_member_count, 0)
        self.assertEquals(user_attendance.team.member_count, 3)
        user_attendance.payments().delete()
        user_attendance.delete()
        call_command('denorm_flush')
        team = models.Team.objects.get(pk=1)
        self.assertEquals(team.name_with_members, "Testing team 1 (Nick, Registered User 1)")
        self.assertEquals(team.unapproved_member_count, 0)
        self.assertEquals(team.member_count, 2)

    def test_related_company_admin(self):
        user_attendance = models.UserAttendance.objects.get(pk=1027)
        company_admin = models.CompanyAdmin.objects.create(userprofile=user_attendance.userprofile, campaign_id=338)
        self.assertEquals(user_attendance.related_company_admin, None)
        call_command('denorm_flush')
        user_attendance = models.UserAttendance.objects.get(pk=1027)
        self.assertEquals(user_attendance.related_company_admin, company_admin)


class RunChecksTestCase(ClearCacheMixin, TestCase):
    def test_checks(self):
        django.setup()
        from django.core import checks
        all_issues = checks.run_checks()
        errors = [str(e) for e in all_issues if e.level >= checks.ERROR]
        if errors:
            self.fail('checks failed:\n' + '\n'.join(errors))  # pragma: no cover
