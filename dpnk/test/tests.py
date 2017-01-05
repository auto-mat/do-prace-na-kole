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
from unittest.mock import MagicMock, patch

from PyPDF2 import PdfFileReader

import createsend

import denorm

import django
from django.core import mail
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import Client, RequestFactory, TestCase
from django.test.utils import override_settings

from dpnk import actions, company_admin_views, mailing, models, results, util, views
from dpnk.models import Campaign, CompanyAdmin, Competition, Payment, Team, User, UserAttendance, UserProfile
from dpnk.test.util import ClearCacheMixin, DenormMixin
from dpnk.test.util import print_response  # noqa

from freezegun import freeze_time

from model_mommy import mommy

from price_level import models as price_level_models

import settings


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class ViewsTests(DenormMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches', 'company_competition']

    def setUp(self):
        super().setUp()
        util.rebuild_denorm_models(Team.objects.filter(pk=1))
        self.client = Client(HTTP_HOST="testing-campaign.testserver")

    def test_login_view(self):
        address = reverse('login')
        response = self.client.get(address)
        self.assertContains(response, "Email (uživatelské jméno)")

        address = reverse('login', kwargs={'initial_email': "test@test.cz"})
        response = self.client.get(address)
        self.assertContains(response, "Email (uživatelské jméno)")
        self.assertContains(response, "test@test.cz")

    def test_admin_views_competition(self):
        self.client.force_login(User.objects.get(username='admin'), settings.AUTHENTICATION_BACKENDS[0])
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
        for payment in Payment.objects.all():
            payment.status = models.Status.DONE
            payment.save()
        util.rebuild_denorm_models(Team.objects.filter(pk=1))
        util.rebuild_denorm_models(UserAttendance.objects.filter(pk=1115))
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
        self.assertRedirects(response, reverse('company_structure'), target_status_code=403)
        user = User.objects.get(email='testadmin@test.cz')
        self.assertEquals(user.get_full_name(), "Company Admin")
        self.assertEquals(UserProfile.objects.get(user=user).telephone, '123456789')
        self.assertEquals(CompanyAdmin.objects.get(userprofile=user.userprofile).administrated_company.pk, 2)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['testadmin@test.cz'])
        self.assertEqual(str(msg.subject), 'Testing campaign - koordinátor organizace - potvrzení registrace')

    def test_dpnk_company_admin_registration_existing(self):
        user = User.objects.get(username='test1')
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
        self.assertContains(response, "Tato organizace již má svého koordinátora.")

    def test_dpnk_registration(self):
        address = reverse('registrace')
        post_data = {
            'email': 'test1@test.cz',
            'password1': 'test11',
            'password2': 'test11',
        }
        response = self.client.post(address, post_data)
        self.assertRedirects(response, reverse('upravit_profil'))
        user = User.objects.get(email='test1@test.cz')
        self.assertNotEquals(user, None)
        self.assertNotEquals(UserProfile.objects.get(user=user), None)
        self.assertNotEquals(UserAttendance.objects.get(userprofile__user=user), None)

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

    def test_dpnk_registration_token(self):
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
        user = User.objects.get(email='test1@test.cz')
        self.assertNotEquals(user, None)
        self.assertNotEquals(UserProfile.objects.get(user=user), None)
        ua = UserAttendance.objects.get(userprofile__user=user)
        self.assertNotEquals(ua, None)
        self.assertEquals(ua.team.pk, 1)

    @patch('slumber.API')
    def test_dpnk_userattendance_creation(self, slumber_api):
        slumber_api.feed.get = {}
        self.client.force_login(User.objects.get(username='user_without_attendance'), settings.AUTHENTICATION_BACKENDS[0])
        address = reverse('profil')
        response = self.client.get(address)
        self.assertRedirects(response, reverse('upravit_profil'))
        user_attendance = UserAttendance.objects.length().get(userprofile__user__username='user_without_attendance', campaign__pk=339)
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
        user_attendance = UserAttendance.objects.get(pk=1115)
        ret_mailing_id = "344ass"
        createsend.Subscriber.add = MagicMock(return_value=ret_mailing_id)
        mailing.add_or_update_user_synchronous(user_attendance)
        custom_fields = [
            OrderedDict((('Key', 'Mesto'), ('Value', 'testing-city'))),
            OrderedDict((('Key', 'Firemni_spravce'), ('Value', True))),
            OrderedDict((('Key', 'Stav_platby'), ('Value', None))),
            OrderedDict((('Key', 'Aktivni'), ('Value', True))),
            OrderedDict((('Key', 'Id'), ('Value', 1128))),
            OrderedDict((('Key', 'Novacek'), ('Value', False))),
            OrderedDict((('Key', 'Kampan'), ('Value', 'testing-campaign'))),
            OrderedDict((('Key', 'Vstoupil_do_souteze'), ('Value', False))),
            OrderedDict((('Key', 'Pocet_lidi_v_tymu'), ('Value', 3))),
            OrderedDict((('Key', 'Povoleni_odesilat_emaily'), ('Value', True))),
        ]
        createsend.Subscriber.add.assert_called_once_with('12345abcde', 'test@test.cz', 'Testing User 1', custom_fields, True)
        self.assertEqual(user_attendance.userprofile.mailing_id, ret_mailing_id)
        self.assertEqual(user_attendance.userprofile.mailing_hash, 'df8923401a70d112dd7d558e832b8e9d')

        createsend.Subscriber.update = MagicMock()
        mailing.add_or_update_user_synchronous(user_attendance)
        self.assertFalse(createsend.Subscriber.update.called)
        self.assertEqual(user_attendance.userprofile.mailing_hash, 'df8923401a70d112dd7d558e832b8e9d')

        custom_fields[0] = OrderedDict((('Key', 'Mesto'), ('Value', 'other-city')))
        user_attendance.team.subsidiary.city = models.City.objects.get(slug="other-city")
        user_attendance.team.subsidiary.save()
        createsend.Subscriber.get = MagicMock()
        createsend.Subscriber.update = MagicMock()
        mailing.add_or_update_user_synchronous(user_attendance)
        createsend.Subscriber.get.assert_called_once_with('12345abcde', ret_mailing_id)
        createsend.Subscriber.update.assert_called_once_with('test@test.cz', 'Testing User 1', custom_fields, True)
        self.assertEqual(user_attendance.userprofile.mailing_hash, 'b8dc6ea4e279fb052c19a2134cc9fb43')

        user_attendance.userprofile.user.is_active = False
        user_attendance.userprofile.user.save()
        createsend.Subscriber.get = MagicMock()
        createsend.Subscriber.delete = MagicMock(return_value=ret_mailing_id)
        mailing.add_or_update_user_synchronous(user_attendance)
        createsend.Subscriber.get.assert_called_once_with('12345abcde', ret_mailing_id)
        createsend.Subscriber.delete.assert_called_once_with()
        self.assertEqual(user_attendance.userprofile.mailing_id, ret_mailing_id)
        self.assertEqual(user_attendance.userprofile.mailing_hash, None)


class PaymentSuccessTests(ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users']

    def setUp(self):
        self.factory = RequestFactory()
        self.user_attendance = UserAttendance.objects.get(pk=1115)
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


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class RequestFactoryViewTests(ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users']

    def setUp(self):
        self.factory = RequestFactory()
        util.rebuild_denorm_models(Team.objects.filter(pk=1))
        self.user_attendance = UserAttendance.objects.get(pk=1115)
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

    def test_questionnaire_view_unknown(self):
        kwargs = {'questionnaire_slug': 'quest1'}
        address = reverse('questionnaire', kwargs=kwargs)
        request = self.factory.get(address)
        request.user = self.user_attendance.userprofile.user
        request.user_attendance = self.user_attendance
        request.subdomain = "testing-campaign"
        request.resolver_match = {"url_name": "questionnaire"}
        response = views.QuestionnaireView.as_view()(request, **kwargs)
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


class PaymentTests(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches']

    def setUp(self):
        super().setUp()
        util.rebuild_denorm_models(Team.objects.filter(pk=1))
        util.rebuild_denorm_models(UserAttendance.objects.filter(pk=1115))

    def test_no_payment_no_admission(self):
        campaign = Campaign.objects.get(pk=339)
        campaign.late_admission_fee = 0
        price_level_models.PriceLevel.objects.all().delete()
        campaign.save()
        UserAttendance.objects.get(pk=1115).save()
        denorm.flush()
        user = UserAttendance.objects.get(pk=1115)
        self.assertEquals(user.payment_status, 'no_admission')
        self.assertEquals(user.representative_payment, None)
        self.assertEquals(user.payment_class(), 'success')
        self.assertEquals(str(user.get_payment_status_display()), 'neplatí se')

    def test_payment_waiting(self):
        payment = Payment.objects.get(pk=4)
        payment.status = 1
        payment.save()
        denorm.flush()
        user = UserAttendance.objects.get(pk=1115)
        self.assertEquals(user.payment_status, 'waiting')
        self.assertEquals(user.representative_payment, payment)
        self.assertEquals(user.payment_class(), 'warning')
        self.assertEquals(str(user.get_payment_status_display()), 'nepotvrzeno')

    def test_payment_done(self):
        user = UserAttendance.objects.get(pk=1115)
        payment = Payment.objects.get(pk=4)
        self.assertEquals(user.payment_status, 'done')
        self.assertEquals(user.representative_payment, payment)
        self.assertEquals(user.payment_class(), 'success')
        self.assertEquals(str(user.get_payment_status_display()), 'zaplaceno')

    def test_payment_unknown(self):
        payment = Payment.objects.get(pk=4)
        payment.status = 123
        payment.save()
        denorm.flush()
        user = UserAttendance.objects.get(pk=1115)
        self.assertEquals(user.payment_status, 'unknown')
        self.assertEquals(user.representative_payment, payment)
        self.assertEquals(user.payment_class(), 'warning')
        self.assertEquals(str(user.get_payment_status_display()), 'neznámý')

    def test_payment_unknown_none(self):
        util.rebuild_denorm_models(Team.objects.filter(pk__in=[1, 3]))
        util.rebuild_denorm_models(UserAttendance.objects.filter(pk=1016))
        user = UserAttendance.objects.get(pk=1016)
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
        payment = Payment.objects.get(pk=3)
        self.assertEquals(payment.pay_type, "kb")
        self.assertEquals(payment.amount, 150)
        self.assertEquals(payment.status, 99)

    def test_dpnk_payment_status_bad_amount(self):
        response = self.payment_status_view(amount="15300", trans_sig='ae18ec7f141c252e692d470f4c1744c9')
        self.assertContains(response, "Bad amount", status_code=400)
        payment = Payment.objects.get(pk=3)
        self.assertEquals(payment.pay_type, None)
        self.assertEquals(payment.amount, 150)
        self.assertEquals(payment.status, 0)

    def test_dpnk_payment_status_view_create(self):
        response = self.payment_status_view(
            session_id='2075-1J1455206434', amount="15100",
            sig='4f59d25cd3dadaf03bef947bb0d9e1b9', trans_sig='c490e30293fe0a96d08b62107accafe8',
            post_sig='445db4f3e11bfa16f0221b0272820058',
        )
        self.assertContains(response, "OK")
        payment = Payment.objects.get(session_id='2075-1J1455206434')
        self.assertEquals(payment.pay_type, "kb")
        self.assertEquals(payment.amount, 151)


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class ViewsLogon(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches']

    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.testserver")
        self.client.force_login(User.objects.get(username='test'), settings.AUTHENTICATION_BACKENDS[0])
        util.rebuild_denorm_models(Team.objects.filter(pk=1))
        util.rebuild_denorm_models(UserAttendance.objects.filter(pk__in=[1115, 2115]))
        self.user_attendance = UserAttendance.objects.get(pk=1115)


class ViewsTestsLogon(ViewsLogon):
    def test_dpnk_team_view(self):
        response = self.client.get(reverse('zmenit_tym'))
        self.assertNotContains(response, "Testing company")
        self.assertContains(response, "Testing team 1")

    def test_dpnk_team_view_no_payment(self):
        Payment.objects.all().delete()
        denorm.flush()
        response = self.client.get(reverse('zmenit_tym'))
        self.assertContains(response, "Testing company")
        self.assertContains(response, "Testing team 1")
        Payment.objects.all().delete()

    def test_ajax_select(self):
        address = "/ajax_select/ajax_lookup/companies?term=tést"
        response = self.client.get(address)
        self.assertContains(response, "<span class=\'tag\'>Testing company</span>", html=True)
        self.assertContains(response, "<span class=\'tag\'>Testing company without admin</span>", html=True)

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

    def test_dpnk_team_invitation_team_last_campaign(self):
        Payment.objects.all().delete()
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
        m.feed.get.return_value = [{"content": "T-shirt description text"}]
        slumber_api.return_value = m
        models.PackageTransaction.objects.all().delete()
        models.Payment.objects.all().delete()
        util.rebuild_denorm_models(Team.objects.filter(pk=3))
        self.user_attendance.save()
        response = self.client.get(reverse('zmenit_tym'))
        self.assertContains(response, "id_company_text")
        self.assertContains(response, "id_subsidiary")

        post_data = {
            'company': '1',
            'subsidiary': '1',
            'team': '3',
            'next': 'Next',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)
        self.assertRedirects(response, reverse("zmenit_triko"))
        self.assertContains(response, "T-shirt description text")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(UserAttendance.objects.get(pk=1115).approved_for_team, "undecided")

    def test_dpnk_team_view_choose_empty_team(self):
        util.rebuild_denorm_models(Team.objects.all())
        models.PackageTransaction.objects.all().delete()
        models.Payment.objects.all().delete()
        self.user_attendance.approved_for_team = "undecided"
        self.user_attendance.save()
        post_data = {
            'company': '1',
            'subsidiary': '1',
            'team': '4',
            'prev': 'Prev',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)
        self.assertRedirects(response, reverse("upravit_profil"))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(UserAttendance.objects.get(pk=1115).approved_for_team, "approved")

    def test_dpnk_update_profile_view(self):
        util.rebuild_denorm_models(Team.objects.filter(pk=2))
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
        self.assertContains(response, "Tento email již je v našem systému zanesen.")

    def test_dpnk_team_view_choose_team_full(self):
        campaign = Campaign.objects.get(pk=339)
        campaign.max_team_members = 0
        campaign.save()
        post_data = {
            'company': '1',
            'subsidiary': '1',
            'team': '3',
            'next': 'Next',
        }
        models.PackageTransaction.objects.all().delete()
        models.Payment.objects.all().delete()
        self.user_attendance.save()
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)
        self.assertContains(response, "Tento tým již má plný počet členů")

    def test_dpnk_team_view_choose_team_out_of_campaign(self):
        post_data = {
            'company': '1',
            'subsidiary': '2',
            'team': '2',
            'next': 'Next',
        }
        models.PackageTransaction.objects.all().delete()
        models.Payment.objects.all().delete()
        self.user_attendance.save()
        response = self.client.post(reverse('zmenit_tym'), post_data)
        self.assertContains(response, "Zvolený tým není dostupný v aktuální kampani")

    def test_dpnk_team_view_choose_team_after_payment(self):
        post_data = {
            'company': '1',
            'subsidiary': '2',
            'team': '3',
            'next': 'Next',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data)
        self.assertContains(response, "Po zaplacení není možné měnit tým mimo pobočku")

    def test_dpnk_team_view_choose_nonexistent_city(self):
        post_data = {
            'company': '1',
            'subsidiary': '2',
            'id_team_selected': 'on',
            'team-name': 'Testing team last campaign',
            'team-campaign': 339,
            'next': 'Next',
        }
        models.PackageTransaction.objects.all().delete()
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)
        self.assertContains(response, "Zvolená pobočka je registrována ve městě, které v aktuální kampani nesoutěží.")

    def test_dpnk_team_undecided(self):
        models.PackageTransaction.objects.all().delete()
        for team_member in self.user_attendance.team.all_members():
            if team_member != self.user_attendance:
                team_member.approved_for_team = 'undecided'
                team_member.save()
        denorm.flush()
        team = models.Team.objects.get(pk=1)
        self.assertEquals(team.member_count, 1)
        self.assertEquals(team.unapproved_member_count, 2)
        response = self.client.get(reverse('zmenit_tym'))
        self.assertContains(
            response,
            "Nemůžete opustit tým, ve kterém jsou samí neschválení členové. "
            "Napřed někoho schvalte a pak změňte tým.",
            status_code=403,
        )

    def test_dpnk_team_change_alone(self):
        models.PackageTransaction.objects.all().delete()
        models.Payment.objects.all().delete()
        for team_member in self.user_attendance.team.all_members():
            if team_member != self.user_attendance:
                team_member.team = None
                team_member.save()
        self.user_attendance.approved_for_team = 'undecided'
        self.user_attendance.save()
        denorm.flush()
        team = models.Team.objects.get(pk=1)
        self.assertEquals(team.member_count, 0)
        self.assertEquals(team.unapproved_member_count, 1)
        response = self.client.get(reverse('zmenit_tym'))
        self.assertEquals(response.status_code, 200)

    def test_dpnk_t_shirt_size(self):
        post_data = {
            't_shirt_size': '1',
            'next': 'Next',
        }
        models.PackageTransaction.objects.all().delete()
        models.Payment.objects.all().delete()
        self.user_attendance.save()
        response = self.client.post(reverse('zmenit_triko'), post_data, follow=True)
        self.assertRedirects(response, reverse("typ_platby"))
        self.assertTrue(self.user_attendance.t_shirt_size.pk, 1)

    def test_dpnk_t_shirt_size_no_sizes(self):
        models.PackageTransaction.objects.all().delete()
        models.Payment.objects.all().delete()
        models.TShirtSize.objects.all().delete()
        self.user_attendance.t_shirt_size = None
        self.user_attendance.save()
        self.user_attendance.campaign.save()
        denorm.flush()
        response = self.client.get(reverse('zmenit_triko'))
        self.assertRedirects(response, reverse("typ_platby"), target_status_code=403)

    @patch('slumber.API')
    def test_dpnk_t_shirt_size_no_sizes_no_admission(self, slumber_api):
        slumber_api.feed.get = {}
        models.PackageTransaction.objects.all().delete()
        models.Payment.objects.all().delete()
        models.TShirtSize.objects.all().delete()
        self.user_attendance.t_shirt_size = None
        self.user_attendance.save()
        price_level_models.PriceLevel.objects.all().delete()
        self.user_attendance.campaign.save()
        denorm.flush()
        response = self.client.get(reverse('zmenit_triko'), follow=True)
        self.assertRedirects(response, reverse("profil"))

    def test_dpnk_t_shirt_size_no_team(self):
        models.PackageTransaction.objects.all().delete()
        models.Payment.objects.all().delete()
        self.user_attendance.save()
        self.user_attendance.team = None
        self.user_attendance.save()
        response = self.client.get(reverse('zmenit_triko'))
        self.assertContains(response, "Velikost trička nemůžete měnit, dokud nemáte zvolený tým.", status_code=403)

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
            'company': '1',
            'subsidiary': '1',
            'team-campaign': '339',
            'id_team_selected': 'on',
            'next': 'Další',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)

        self.assertRedirects(response, reverse("pozvanky"))
        self.assertContains(response, "Tým Created team úspěšně vytvořen")
        user = UserAttendance.objects.get(pk=1115)
        self.assertEquals(user.team.name, "Created team")
        self.assertEquals(user.team.subsidiary.address.street, "Created street")
        self.assertEquals(user.team.subsidiary.company.name, "Created company")
        self.assertEquals(UserAttendance.objects.get(pk=1115).approved_for_team, "approved")

    @patch('slumber.API')
    def company_payment(self, slumber_api, amount, amount_tax, beneficiary=False):
        slumber_instance = slumber_api.return_value
        slumber_instance.feed.get.return_value = {"10816": {"content": "Emission calculator description text"}}
        response = self.client.get(reverse('company_admin_pay_for_users'))
        self.assertContains(response, "%s Kč: Registered User 1 (test-registered@test.cz)" % amount)
        post_data = {
            'paing_for': '2115',
            'submit': 'Odeslat',
        }
        response = self.client.post(reverse('company_admin_pay_for_users'), post_data, follow=True)
        self.assertRedirects(response, reverse('company_structure'))
        p = UserAttendance.objects.get(id=2115).representative_payment
        self.assertEquals(p.status, models.Status.COMPANY_ACCEPTS)

        response = self.client.get(reverse('invoices'))
        self.assertContains(response, "<td>Registered User 1</td>", html=True)
        self.assertContains(response, "<td>%i,0 Kč</td>" % amount, html=True)

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
        p = UserAttendance.objects.get(id=2115).representative_payment
        self.assertEquals(p.status, 1006)
        self.assertEquals(p.invoice.total_amount, amount_tax)
        pdf = PdfFileReader(p.invoice.invoice_pdf)
        pdf_string = pdf.pages[0].extractText()
        self.assertTrue("Celkem s DPH: %s,-" % amount_tax in pdf_string)
        self.assertTrue("1323575433" in pdf_string)
        self.assertTrue("Testing company" in pdf_string)

    def test_company_payment_no_t_shirt_size(self):
        user_attendance = UserAttendance.objects.get(id=2115)
        user_attendance.t_shirt_size = None
        user_attendance.save()
        self.company_payment(amount=130.0, amount_tax=157)

    def test_company_payment_paid_t_shirt_size(self):
        user_attendance = UserAttendance.objects.get(id=2115)
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
            'company': '1',
            'subsidiary': '',
            'team': '',
            'next': 'Next',
        }
        response = self.client.post(reverse('zmenit_tym'), post_data)
        self.assertContains(response, 'error_1_id_team')
        self.assertContains(response, 'var value = undefined;')

    def test_dpnk_team_approval(self):
        ua = UserAttendance.objects.get(pk=1015)
        ua.approved_for_team = 'undecided'
        ua.save()
        post_data = {
            'approve': 'approve-1015',
            'reason-1015': '',
        }
        response = self.client.post(reverse('team_members'), post_data)
        self.assertContains(response, 'Členství uživatele Nick v týmu Testing team 1 bylo odsouhlaseno.')

    def test_dpnk_team_denial(self):
        ua = UserAttendance.objects.get(pk=1015)
        ua.approved_for_team = 'undecided'
        ua.save()
        post_data = {
            'approve': 'deny-1015',
            'reason-1015': 'reason',
        }
        response = self.client.post(reverse('team_members'), post_data)
        self.assertContains(response, 'Členství uživatele Nick ve vašem týmu bylo zamítnuto')

    def test_dpnk_team_denial_no_message(self):
        ua = UserAttendance.objects.get(pk=1015)
        ua.approved_for_team = 'undecided'
        ua.save()
        post_data = {
            'approve': 'deny-1015',
        }
        response = self.client.post(reverse('team_members'), post_data)
        self.assertContains(response, 'Při zamítnutí člena týmu musíte vyplnit zprávu.')

    def test_dpnk_team_invitation_current_user(self):
        post_data = {
            'email1': 'test@email.cz',
            'submit': 'odeslat',
        }
        response = self.client.post(reverse('pozvanky'), post_data, follow=True)
        self.assertContains(response, 'Odeslána pozvánka uživateli Null User na email test@email.cz')
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
        self.assertContains(response, 'Odeslána pozvánka na email test-unknown@email.cz')
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test-unknown@email.cz'])
        self.assertEqual(str(msg.subject), 'Testing campaign - pozvánka do týmu')

    def test_dpnk_company_admin_application(self):
        util.rebuild_denorm_models(Team.objects.filter(pk=2))
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
        user = User.objects.get(username='test1')
        models.CompanyAdmin.objects.create(
            administrated_company=self.user_attendance.team.subsidiary.company,
            userprofile=user.userprofile,
            campaign=self.user_attendance.campaign,
            company_admin_approved='approved',
        )
        response = self.client.get(reverse('company_admin_application'))
        self.assertContains(response, 'Vaše organizce již svého koordinátora má: Null User, Null User, Testing User.')

    def test_dpnk_company_admin_application_create(self):
        models.CompanyAdmin.objects.all().delete()
        response = self.client.get(reverse('company_admin_application'))
        self.assertContains(
            response,
            '<label for="id_motivation_company_admin" class="control-label  requiredField"> Zaměstnanecká pozice<span class="asteriskField">*</span> </label>',
            html=True,
        )


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
        slumber_api.feed.get = {}
        response = self.client.get(reverse('profil'))
        self.assertContains(response, "Nezapomeňte vyplnit odpovědi v následujících soutěžích: <a href='/cs/otazka/quest/'>Dotazník</a>!")

    @patch('slumber.API')
    def test_dpnk_registration_vouchers(self, slumber_api):
        slumber_api.feed.get = {}
        models.Voucher.objects.create(user_attendance=self.user_attendance, token="1234")
        response = self.client.get(reverse('profil'))
        self.assertContains(response, "<h3>Vouchery</h3>", html=True)
        self.assertContains(response, "<tr> <td> ReKola </td> <td> 1234 </td> </tr>", html=True)

    @patch('slumber.API')
    def test_dpnk_registration_company_admin_undecided(self, slumber_api):
        slumber_api.feed.get = {}
        util.rebuild_denorm_models(Team.objects.filter(pk=2))
        ca = models.CompanyAdmin.objects.get(userprofile=self.user_attendance.userprofile, campaign_id=339)
        ca.company_admin_approved = 'undecided'
        ca.save()
        response = self.client.get(reverse('profil'))
        denorm.flush()
        self.assertContains(response, "Vaše žádost o funkci koordinátora organizace čeká na vyřízení.")

    @patch('slumber.API')
    def test_dpnk_registration_company_admin_decided(self, slumber_api):
        slumber_api.feed.get = {}
        util.rebuild_denorm_models(Team.objects.filter(pk=2))
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
        user_attendance = UserAttendance.objects.length().get(pk=1115)
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
        user_attendance = UserAttendance.objects.length().get(pk=1115)
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
        user_attendance = UserAttendance.objects.length().get(pk=1115)
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
        user_attendance = UserAttendance.objects.length().get(pk=1115)
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

    @patch('slumber.API')
    def test_emission_calculator(self, slumber_api):
        m = MagicMock()
        m.feed.get.return_value = [{"content": "Emission calculator description text"}]
        slumber_api.return_value = m
        address = reverse('emission_calculator')
        response = self.client.get(address)
        self.assertContains(response, "Emisní kalkulačka")
        self.assertContains(response, "<tr><td>Ujetá vzdálenost</td><td>161,9&nbsp;km</td></tr>", html=True)
        self.assertContains(response, "<tr><td>CO</td><td>117 280,4&nbsp;mg</td></tr>", html=True)
        self.assertContains(response, "<tr><td>NO<sub>X</sub></td><td>27 474,4&nbsp;mg</td></tr>", html=True)
        self.assertContains(response, "<tr><td>N<sub>2</sub>O</td><td>4 047,5&nbsp;mg</td></tr>", html=True)
        self.assertContains(response, "<tr><td>CH<sub>4</sub></td><td>1 246,6&nbsp;mg</td></tr>", html=True)
        self.assertContains(response, "<tr><td>SO<sub>2</sub></td><td>1 246,6&nbsp;mg</td></tr>", html=True)
        self.assertContains(response, "<tr><td>Pevné částice</td><td>5 666,5&nbsp;mg</td></tr>", html=True)
        self.assertContains(response, "<tr><td>Olovo</td><td>1,8&nbsp;mg</td></tr>", html=True)
        self.assertContains(response, '<div id="calculator_description">Emission calculator description text</div>', html=True)

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
        self.user_attendance = UserAttendance.objects.get(pk=1115)

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
)
class ViewsTestsRegistered(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches', 'trips']

    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_HOST="testing-campaign.testserver")
        self.client.force_login(User.objects.get(username='test'), settings.AUTHENTICATION_BACKENDS[0])
        util.rebuild_denorm_models(Team.objects.filter(pk=1))
        util.rebuild_denorm_models(UserAttendance.objects.filter(pk=1115))
        self.user_attendance = UserAttendance.objects.get(pk=1115)
        self.assertTrue(self.user_attendance.entered_competition())

    @override_settings(
        MEDIA_ROOT="dpnk/test_files",
    )
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

    @override_settings(
        MEDIA_ROOT="dpnk/test_files",
    )
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
        self.assertContains(response, '<img src="%sDSC00002.JPG.360x360_q85.jpg" width="360" height="270">' % settings.MEDIA_URL, html=True)
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
        self.assertContains(response, 'Žádná akce není.')

    @patch('slumber.API')
    def test_dpnk_profile_page_link(self, slumber_api):
        models.Answer.objects.filter(pk__in=(2, 3, 4)).delete()
        slumber_api.feed.get = {}
        response = self.client.get(reverse('profil'))
        self.assertContains(response, '<a href="%sDSC00002.JPG" target="_blank">DSC00002.JPG</a>' % settings.MEDIA_URL, html=True)
        self.assertContains(response, 'Všechny příspěvky z této soutěže')

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=11, day=8),
    )
    @patch('slumber.API')
    def test_dpnk_rides_view_key_error(self, slumber_api):
        "Test if the rides saves, when between loading and sending the form date changes."
        "The non-active days should not be saved, but active days should be saved"
        post_data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '2',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-id': 101,
            'form-0-commute_mode': 'by_other_vehicle',
            'form-0-distance': '6',
            'form-0-direction': 'trip_from',
            'form-0-user_attendance': 1115,
            'form-0-date': '2010-11-01',
            'initial-form-0-date': '2010-11-01',
            'form-1-id': 103,
            'form-1-commute_mode': 'bicycle',
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
        user_attendance = UserAttendance.objects.get(pk=1115)
        self.assertEquals(user_attendance.trip_length_total, 39.0)
        self.assertEquals(user_attendance.team.get_length(), 13.0)

    @patch('slumber.API')
    def test_dpnk_rides_view(self, slumber_api):
        slumber_api.feed.get = {}
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
            'form-0-commute_mode': 'by_foot',
            'form-0-distance': '28.89',
            'form-0-direction': 'trip_to',
            'form-0-user_attendance': 1115,
            'form-0-date': '2010-11-01',
            'initial-form-0-date': '2010-11-01',
            'form-2-id': '',
            'form-2-commute_mode': 'bicycle',
            'form-2-distance': '2,34',
            'form-2-direction': 'trip_from',
            'form-2-user_attendance': 1115,
            'form-2-date': '2010-11-01',
            'initial-form-2-date': '2010-11-01',
            'form-3-id': '',
            'form-3-commute_mode': 'no_work',
            'form-3-distance': '',
            'form-3-direction': 'trip_to',
            'form-3-user_attendance': 1115,
            'form-3-date': '2010-11-02',
            'initial-form-3-date': '2010-11-02',
            'form-1-id': 103,
            'form-1-commute_mode': 'by_other_vehicle',
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
            '<div>Ujetá započítaná vzdálenost: 31,23&nbsp;km (<a href="/cs/jizdy-podrobne/">Podrobný přehled jízd</a>)</div>',
            html=True,
        )
        self.assertContains(
            response,
            '<div>Pravidelnost: 66,7&nbsp;%</div>',
            html=True,
        )
        self.assertContains(
            response,
            '<div>Ušetřené množství oxidu uhličitého: 4 028,7&nbsp;g (<a href="/cs/emisni_kalkulacka/">Emisní kalkulačka</a>)</div>',
            html=True,
        )
        self.assertEquals(self.user_attendance.user_trips.count(), 7)
        self.assertEquals(models.Trip.objects.get(pk=101).distance, 28.89)

        trip1 = models.Trip.objects.get(pk=103)
        self.assertEquals(trip1.distance, 3)
        self.assertEquals(trip1.user_attendance.pk, 1115)
        self.assertEquals(trip1.commute_mode, "by_other_vehicle")
        self.assertEquals(trip1.date, datetime.date(year=2010, month=11, day=2))

        trip2 = models.Trip.objects.get(date=datetime.date(year=2010, month=11, day=1), direction='trip_from')
        self.assertEquals(trip2.commute_mode, 'bicycle')
        self.assertEquals(trip2.user_attendance.pk, 1115)
        self.assertEquals(trip2.distance, 2.34)

        trip3 = models.Trip.objects.get(date=datetime.date(year=2010, month=11, day=2), direction='trip_to')
        self.assertEquals(trip3.commute_mode, 'no_work')
        self.assertEquals(trip3.user_attendance.pk, 1115)
        self.assertEquals(trip3.distance, None)

        denorm.flush()
        user_attendance = UserAttendance.objects.get(pk=1115)
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
        util.rebuild_denorm_models(Team.objects.all())
        for competition in models.Competition.objects.all():
            competition.recalculate_results()
        competition = models.Competition.objects.filter(slug="quest")
        actions.normalize_questionnqire_admissions(None, None, competition)
        competition.get().recalculate_results()
        response = self.client.get(reverse('competitions'))
        self.assertContains(response, 'vnitrofiremní soutěž na pravidelnost jednotlivců organizace Testing company')
        self.assertContains(response, '<p>1. místo z 1 společností</p>', html=True)
        self.assertContains(response, 'soutěž na vzdálenost jednotlivců  ve městě Testing city')
        self.assertContains(response, 'Vyplnit odpovědi')

    def test_dpnk_competitions_page_change(self):
        response = self.client.get(reverse('competitions'))
        self.assertContains(response, 'soutěž na vzdálenost jednotlivců')
        self.assertContains(response, 'Vyplnit odpovědi')

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
        util.rebuild_denorm_models(Team.objects.all())
        for competition in models.Competition.objects.all():
            competition.recalculate_results()
        competition = models.Competition.objects.filter(slug="quest")
        actions.normalize_questionnqire_admissions(None, None, competition)
        competition.get().recalculate_results()
        response = self.client.get(reverse('competitions'))
        self.assertContains(response, '<i>dotazník jednotlivců</i>', html=True)
        self.assertContains(response, "<p>2. místo z 1 týmů</p>", html=True)
        self.assertContains(response, "<p>1,4&nbsp;%</p>", html=True)
        self.assertContains(response, "<p>1 z 69 jízd</p>", html=True)
        self.assertContains(response, "<p>1. místo z 1 jednotlivců</p>", html=True)
        self.assertContains(response, "<p>5&nbsp;km</p>", html=True)
        self.assertContains(response, "<p>1. místo z 1 jednotlivců</p>", html=True)
        self.assertContains(response, "<p>16,2b.</p>", html=True)


class TestTeams(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users']

    def setUp(self):
        super().setUp()
        util.rebuild_denorm_models(Team.objects.filter(pk=1))
        util.rebuild_denorm_models(UserAttendance.objects.filter(pk=1115))

    def test_member_count_update(self):
        team = Team.objects.get(id=1)
        self.assertEqual(team.member_count, 3)
        campaign = Campaign.objects.get(pk=339)
        user = User.objects.create(first_name="Third", last_name="User", username="third_user")
        userprofile = UserProfile.objects.create(user=user)
        UserAttendance.objects.create(team=team, campaign=campaign, userprofile=userprofile, approved_for_team='approved')
        denorm.flush()
        team = Team.objects.get(id=1)
        self.assertEqual(team.member_count, 4)


class ResultsTests(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'test_results_data', 'trips']

    def setUp(self):
        super().setUp()
        util.rebuild_denorm_models(Team.objects.filter(pk=1))
        util.rebuild_denorm_models(UserAttendance.objects.filter(pk=1115))

    def test_get_competitors(self):
        team = Team.objects.get(id=1)
        query = results.get_competitors(Competition.objects.get(id=0))
        self.assertListEqual(list(query.all()), [team])

    def test_get_userprofile_length(self):
        user_attendance = UserAttendance.objects.get(pk=1115)
        competition = Competition.objects.get(id=5)
        result = results.get_userprofile_length([user_attendance], competition)
        self.assertEquals(result, 5.0)

        result = user_attendance.trip_length_total
        self.assertEquals(result, 5.0)

    @override_settings(
        FAKE_DATE=datetime.date(year=2010, month=11, day=20),
    )
    def test_get_userprofile_frequency(self):
        user_attendance = UserAttendance.objects.get(pk=1115)
        competition = Competition.objects.get(id=3)

        result = user_attendance.get_rides_count_denorm
        self.assertEquals(result, 1)

        result = user_attendance.get_working_rides_base_count()
        self.assertEquals(result, 31)

        result = user_attendance.frequency
        self.assertEquals(result, 0.0222222222222222)

        result = user_attendance.team.frequency
        self.assertEquals(result, 0.0075187969924812)

        result = user_attendance.team.get_rides_count_denorm
        self.assertEquals(result, 1)

        result = user_attendance.team.get_working_trips_count()
        self.assertEquals(result, 91)

        result = results.get_working_trips_count(user_attendance, competition)
        self.assertEquals(result, 23)

        result = results.get_userprofile_frequency(user_attendance, competition)
        self.assertEquals(result, (1, 23, 1 / 23.0))

        result = results.get_team_frequency(user_attendance.team.members(), competition)
        self.assertEquals(result, (1, 69, 1 / 69.0))


class ModelTests(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches']

    def setUp(self):
        super().setUp()
        util.rebuild_denorm_models(Team.objects.filter(pk=1))

    def test_payment_type_string(self):
        user_attendance = UserAttendance.objects.get(pk=1115)
        user_attendance.save()
        call_command('denorm_flush')
        self.assertEquals(user_attendance.payment_type_string(), "ORGANIZACE PLATÍ FAKTUROU")

    def test_payment_type_string_none_type(self):
        user_attendance = UserAttendance.objects.get(pk=1115)
        user_attendance.representative_payment = Payment(pay_type=None)
        self.assertEquals(user_attendance.payment_type_string(), None)


class DenormTests(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches']

    def test_name_with_members(self):
        util.rebuild_denorm_models(Team.objects.filter(pk__in=[2, 3]))
        user_attendance = UserAttendance.objects.get(pk=1115)
        user_attendance.team.save()
        call_command('denorm_flush')
        self.assertEquals(user_attendance.team.name_with_members, "Testing team 1 (Nick, Testing User 1, Registered User 1)")
        self.assertEquals(user_attendance.team.unapproved_member_count, 0)
        self.assertEquals(user_attendance.team.member_count, 3)
        user_attendance.userprofile.nickname = "Testing nick"
        user_attendance.userprofile.save()
        call_command('denorm_flush')
        user_attendance = UserAttendance.objects.get(pk=1115)
        self.assertEquals(user_attendance.team.name_with_members, "Testing team 1 (Nick, Testing nick, Registered User 1)")
        self.assertEquals(user_attendance.team.unapproved_member_count, 0)
        self.assertEquals(user_attendance.team.member_count, 3)

    def test_name_with_members_delete_userattendance(self):
        user_attendance = UserAttendance.objects.get(pk=1115)
        user_attendance.team.save()
        models.Payment.objects.all().delete()
        call_command('denorm_flush')
        self.assertEquals(user_attendance.team.name_with_members, "Testing team 1 (Nick, Testing User 1, Registered User 1)")
        self.assertEquals(user_attendance.team.unapproved_member_count, 0)
        self.assertEquals(user_attendance.team.member_count, 3)
        user_attendance.delete()
        call_command('denorm_flush')
        team = Team.objects.get(pk=1)
        self.assertEquals(team.name_with_members, "Testing team 1 (Nick, Registered User 1)")
        self.assertEquals(team.unapproved_member_count, 0)
        self.assertEquals(team.member_count, 2)

    def test_related_company_admin(self):
        user_attendance = UserAttendance.objects.get(pk=1027)
        company_admin = models.CompanyAdmin.objects.create(userprofile=user_attendance.userprofile, campaign_id=338)
        self.assertEquals(user_attendance.related_company_admin, None)
        call_command('denorm_flush')
        user_attendance = UserAttendance.objects.get(pk=1027)
        self.assertEquals(user_attendance.related_company_admin, company_admin)


class RunChecksTestCase(ClearCacheMixin, TestCase):
    def test_checks(self):
        django.setup()
        from django.core import checks
        all_issues = checks.run_checks()
        errors = [str(e) for e in all_issues if e.level >= checks.ERROR]
        if errors:
            self.fail('checks failed:\n' + '\n'.join(errors))  # pragma: no cover
