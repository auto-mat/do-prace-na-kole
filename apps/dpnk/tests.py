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
from django.test import TestCase, RequestFactory, TransactionTestCase, Client
from django.core.urlresolvers import reverse
from django.core import mail
from django.core.management import call_command
from django.test.utils import override_settings
from dpnk import results, models, mailing, views, filters
from dpnk.models import Competition, Team, UserAttendance, Campaign, User, UserProfile, Payment, CompanyAdmin
import datetime
import django
from django_admin_smoke_tests import tests
from model_mommy import mommy
import createsend
from freezegun import freeze_time
from unittest.mock import MagicMock, patch
from collections import OrderedDict
from PyPDF2 import PdfFileReader
import denorm


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class AdminTest(tests.AdminSiteSmokeTest):
    fixtures = ['campaign', 'views', 'users', 'test_results_data', 'transactions', 'batches']

    def get_request(self):
        request = super().get_request()
        request.subdomain = "testing-campaign"
        return request


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class ExportTests(TransactionTestCase):
    fixtures = ['campaign', 'views', 'users']

    def setUp(self):
        self.client = Client(HTTP_HOST="testing-campaign.testserver")
        self.assertTrue(self.client.login(username='admin', password='test'))
        call_command('denorm_init')
        call_command('denorm_rebuild')

    def tearDown(self):
        call_command('denorm_drop')

    def test_userattendance_export(self):
        address = "/admin/dpnk/userattendance/export/"
        post_data = {
            'file_format': 0,
        }
        response = self.client.post(address, post_data)
        self.assertContains(response, "test2@test.cz,Testing company")

    def test_company_export(self):
        address = "/admin/dpnk/company/export/"
        post_data = {
            'file_format': 0,
        }
        response = self.client.post(address, post_data)
        self.assertContains(response, "2,Testing company without admin,11111")

    def test_subsidiary_export(self):
        address = "/admin/dpnk/subsidiary/export/"
        post_data = {
            'file_format': 0,
        }
        response = self.client.post(address, post_data)
        self.assertContains(response, "1,1,1")


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class ViewsTests(TransactionTestCase):
    fixtures = ['campaign', 'views', 'users']

    def setUp(self):
        self.client = Client(HTTP_HOST="testing-campaign.testserver")
        call_command('denorm_init')

    def tearDown(self):
        call_command('denorm_drop')

    def test_admin_views_competition(self):
        self.assertTrue(self.client.login(username='admin', password='test'))
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
            'password1': 'test11',
            'password2': 'test11',
            'motivation_company_admin': 'some motivation',
            'telephone': 123456789,
            'first_name': 'Company',
            'last_name': 'Admin',
            'administrated_company': 2,
            'campaign': 339,
            'will_pay_opt_in': True,
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertRedirects(response, reverse('company_structure'), target_status_code=403)
        user = User.objects.get(email='testadmin@test.cz')
        self.assertEquals(user.get_full_name(),  "Company Admin")
        self.assertEquals(UserProfile.objects.get(user=user).telephone, '123456789')
        self.assertEquals(CompanyAdmin.objects.get(user=user).administrated_company.pk, 2)
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['testadmin@test.cz'])
        self.assertEqual(str(msg.subject), 'Testing campaign - firemní koordinátor - potvrzení registrace')

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

    def test_dpnk_userattendance_creation(self):
        self.assertTrue(self.client.login(username='user_without_attendance', password='test'))
        address = reverse('profil')
        response = self.client.get(address)
        self.assertRedirects(response, reverse('upravit_profil'))
        user_attendance = UserAttendance.objects.get(userprofile__user__username='user_without_attendance', campaign__pk=339)
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
        user_attendance = UserAttendance.objects.get(userprofile__user__username='test')
        ret_mailing_id = "344ass"
        createsend.Subscriber.add = MagicMock(return_value=ret_mailing_id)
        mailing.add_or_update_user_synchronous(user_attendance)
        custom_fields = [
            OrderedDict((('Key', 'Mesto'), ('Value', 'testing-city'))),
            OrderedDict((('Key', 'Firemni_spravce'), ('Value', True))),
            OrderedDict((('Key', 'Stav_platby'), ('Value', None))),
            OrderedDict((('Key', 'Aktivni'), ('Value', True))),
            OrderedDict((('Key', 'Novacek'), ('Value', False))),
            OrderedDict((('Key', 'Kampan'), ('Value', 'testing-campaign'))),
            OrderedDict((('Key', 'Vstoupil_do_souteze'), ('Value', False))),
            OrderedDict((('Key', 'Pocet_lidi_v_tymu'), ('Value', None))),
            OrderedDict((('Key', 'Povoleni_odesilat_emaily'), ('Value', True))),
        ]
        createsend.Subscriber.add.assert_called_once_with('12345abcde', 'test@test.cz', 'Testing User 1', custom_fields, True)
        self.assertEqual(user_attendance.userprofile.mailing_id, ret_mailing_id)
        self.assertEqual(user_attendance.userprofile.mailing_hash, '29b17908fe23eebd00d302d3c7a8a942')

        createsend.Subscriber.update = MagicMock()
        mailing.add_or_update_user_synchronous(user_attendance)
        self.assertFalse(createsend.Subscriber.update.called)
        self.assertEqual(user_attendance.userprofile.mailing_hash, '29b17908fe23eebd00d302d3c7a8a942')

        custom_fields[0] = OrderedDict((('Key', 'Mesto'), ('Value', 'other-city')))
        user_attendance.team.subsidiary.city = models.City.objects.get(slug="other-city")
        user_attendance.team.subsidiary.save()
        createsend.Subscriber.get = MagicMock()
        createsend.Subscriber.update = MagicMock()
        mailing.add_or_update_user_synchronous(user_attendance)
        createsend.Subscriber.get.assert_called_once_with('12345abcde', ret_mailing_id)
        createsend.Subscriber.update.assert_called_once_with('test@test.cz', 'Testing User 1', custom_fields, True)
        self.assertEqual(user_attendance.userprofile.mailing_hash, 'd3fb264e87e16cd13829c74eff4f15bb')

        user_attendance.userprofile.user.is_active = False
        user_attendance.userprofile.user.save()
        createsend.Subscriber.get = MagicMock()
        createsend.Subscriber.delete = MagicMock(return_value=ret_mailing_id)
        mailing.add_or_update_user_synchronous(user_attendance)
        createsend.Subscriber.get.assert_called_once_with('12345abcde', ret_mailing_id)
        createsend.Subscriber.delete.assert_called_once_with()
        self.assertEqual(user_attendance.userprofile.mailing_id, ret_mailing_id)
        self.assertEqual(user_attendance.userprofile.mailing_hash, None)


class PaymentSuccessTests(TestCase):
    fixtures = ['campaign', 'views', 'users']

    def setUp(self):
        self.factory = RequestFactory()
        self.user_attendance = UserAttendance.objects.get(userprofile__user__username='test')
        self.session_id = "2075-1J1455206457"
        self.trans_id = "2055"
        models.Payment.objects.create(
            session_id=self.session_id,
            user_attendance=self.user_attendance,
            amount=150
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


class FilterTests(TestCase):
    fixtures = ['campaign', 'views', 'users']

    def setUp(self):
        self.factory = RequestFactory()
        self.user_attendance = UserAttendance.objects.get(userprofile__user__username='test')
        self.session_id = "2075-1J1455206457"
        self.trans_id = "2055"
        models.Payment.objects.create(
            session_id=self.session_id,
            user_attendance=self.user_attendance,
            amount=150
        )

    def test_email_filter_blank(self):
        request = self.factory.get("")
        f = filters.EmailFilter(request, {"email": "duplicate"}, models.User, None)
        q = f.queryset(request, models.User.objects.all())
        self.assertEquals(q.count(), 0)

    def test_email_filter_duplicate(self):
        request = self.factory.get("")
        f = filters.EmailFilter(request, {"email": "blank"}, models.User, None)
        q = f.queryset(request, models.User.objects.all())
        self.assertEquals(q.count(), 0)

    def test_has_team_filter_yes(self):
        request = self.factory.get("")
        f = filters.HasTeamFilter(request, {"user_has_team": "yes"}, models.UserAttendance, None)
        q = f.queryset(request, models.UserAttendance.objects.all())
        self.assertEquals(q.count(), 3)

    def test_has_team_filter_no(self):
        request = self.factory.get("")
        f = filters.HasTeamFilter(request, {"user_has_team": "no"}, models.UserAttendance, None)
        q = f.queryset(request, models.UserAttendance.objects.all())
        self.assertEquals(q.count(), 2)

    def test_is_for_company_yes(self):
        request = self.factory.get("")
        f = filters.IsForCompanyFilter(request, {"is_for_company": "yes"}, models.Competition, None)
        q = f.queryset(request, models.Competition.objects.all())
        self.assertEquals(q.count(), 0)

    def test_is_for_company_no(self):
        request = self.factory.get("")
        f = filters.IsForCompanyFilter(request, {"is_for_company": "no"}, models.Competition, None)
        q = f.queryset(request, models.Competition.objects.all())
        self.assertEquals(q.count(), 3)

    def test_has_rides_filter_yes(self):
        request = self.factory.get("")
        f = filters.HasRidesFilter(request, {"has_rides": "yes"}, models.UserAttendance, None)
        q = f.queryset(request, models.UserAttendance.objects.all())
        self.assertEquals(q.count(), 1)

    def test_has_rides_filter_no(self):
        request = self.factory.get("")
        f = filters.HasRidesFilter(request, {"has_rides": "no"}, models.UserAttendance, None)
        q = f.queryset(request, models.UserAttendance.objects.all())
        self.assertEquals(q.count(), 4)

    def test_has_voucher_filter_yes(self):
        request = self.factory.get("")
        f = filters.HasVoucherFilter(request, {"has_voucher": "yes"}, models.UserAttendance, None)
        q = f.queryset(request, models.UserAttendance.objects.all())
        self.assertEquals(q.count(), 0)

    def test_has_voucher_filter_no(self):
        request = self.factory.get("")
        f = filters.HasVoucherFilter(request, {"has_voucher": "no"}, models.UserAttendance, None)
        q = f.queryset(request, models.UserAttendance.objects.all())
        self.assertEquals(q.count(), 5)

    def test_campaign_filter_campaign(self):
        request = self.factory.get("")
        request.subdomain = "testing-campaign"
        f = filters.CampaignFilter(request, {"campaign": "testing-campaign"}, models.UserAttendance, None)
        q = f.queryset(request, models.UserAttendance.objects.all())
        self.assertEquals(q.count(), 4)

    def test_campaign_filter_none(self):
        request = self.factory.get("")
        request.subdomain = "testing-campaign"
        f = filters.CampaignFilter(request, {"campaign": "none"}, models.UserAttendance, None)
        q = f.queryset(request, models.UserAttendance.objects.all())
        self.assertEquals(q.count(), 0)

    def test_campaign_filter_without_subdomain(self):
        request = self.factory.get("")
        f = filters.CampaignFilter(request, {"campaign": "none"}, models.UserAttendance, None)
        q = f.queryset(request, models.UserAttendance.objects.all())
        self.assertEquals(q.count(), 0)

    def test_campaign_filter_unknown_campaign(self):
        request = self.factory.get("")
        request.subdomain = "asdf"
        f = filters.CampaignFilter(request, {}, models.UserAttendance, None)
        q = f.queryset(request, models.UserAttendance.objects.all())
        self.assertEquals(q.count(), 0)

    def test_campaign_filter_all(self):
        request = self.factory.get("")
        request.subdomain = "testing-campaign"
        f = filters.CampaignFilter(request, {"campaign": "all"}, models.UserAttendance, None)
        q = f.queryset(request, models.UserAttendance.objects.all())
        self.assertEquals(q.count(), 5)


class PaymentTests(TransactionTestCase):
    fixtures = ['campaign', 'views', 'users', 'transactions', 'batches']

    def setUp(self):
        call_command('denorm_init')
        call_command('denorm_rebuild')

    def tearDown(self):
        call_command('denorm_drop')

    def test_no_payment_no_admission(self):
        campaign = Campaign.objects.get(pk=339)
        campaign.late_admission_fee = 0
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
class PayuTests(TransactionTestCase):
    fixtures = ['campaign', 'views', 'users', 'transactions', 'batches']

    def setUp(self):
        self.client = Client(HTTP_HOST="testing-campaign.testserver")

    @patch('http.client.HTTPSConnection.request')
    @patch('http.client.HTTPSConnection.getresponse')
    def payment_status_view(
            self, payu_response, payu_request, session_id='2075-1J1455206433',
            amount="15000", trans_sig='ae6f4b9f8fbdbb506edf4eeb1cebcee0', sig='1af62397cfb6e6de5295325801239e4f',
            post_sig="b6b29bb8437f9e2486fbe5555673372d"):
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
            'pos_id=2075-1&session_id=%(session_id)s&ts=1290254400&sig=%(trans_sig)s' % {"trans_sig": post_sig, "session_id": session_id},
            {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
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
            post_sig='445db4f3e11bfa16f0221b0272820058')
        self.assertContains(response, "OK")
        payment = Payment.objects.get(session_id='2075-1J1455206434')
        self.assertEquals(payment.pay_type, "kb")
        self.assertEquals(payment.amount, 151)


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class ViewsTestsLogon(TransactionTestCase):
    fixtures = ['campaign', 'views', 'users', 'transactions', 'batches']

    def setUp(self):
        self.client = Client(HTTP_HOST="testing-campaign.testserver")
        self.assertTrue(self.client.login(username='test', password='test'))
        call_command('denorm_init')
        call_command('denorm_rebuild')
        self.user_attendance = UserAttendance.objects.get(userprofile__user__username='test')

    def tearDown(self):
        call_command('denorm_drop')

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

    def test_dpnk_team_view_choose(self):
        post_data = {
            'company': '1',
            'subsidiary': '1',
            'team': '1',
            'next': 'Next',
        }
        models.PackageTransaction.objects.all().delete()
        response = self.client.post(reverse('zmenit_tym'), post_data, follow=True)
        self.assertRedirects(response, reverse("zmenit_triko"))

    def test_dpnk_t_shirt_size(self):
        post_data = {
            't_shirt_size': '1',
            'next': 'Next',
        }
        models.PackageTransaction.objects.all().delete()
        models.Payment.objects.all().delete()
        response = self.client.post(reverse('zmenit_triko'), post_data, follow=True)
        self.assertRedirects(response, reverse("typ_platby"))
        self.assertTrue(self.user_attendance.t_shirt_size.pk, 1)

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

    def test_dpnk_payment_type_without_company_admin(self):
        post_data = {
            'payment_type': 'company',
            'next': 'Next',
        }
        models.Payment.objects.all().delete()
        models.CompanyAdmin.objects.all().delete()
        denorm.flush()
        response = self.client.post(reverse('typ_platby'), post_data)
        self.assertContains(response, "Váš zaměstnavatel Testing company nemá zvoleného koordinátor společnosti.")

        post_data['payment_type'] = 'member'
        response = self.client.post(reverse('typ_platby'), post_data, follow=True)
        self.assertRedirects(response, reverse("registration_uncomplete"))
        self.assertContains(response, "Vaše členství v klubu přátel ještě bude muset být schváleno")
        self.assertEquals(models.Payment.objects.get().pay_type, 'am')

    def test_dpnk_team_view_create(self):
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

    def company_payment(self, beneficiary=False):
        post_data = {
            'paing_for': '1115',
            'submit': 'Odeslat',
        }
        response = self.client.post(reverse('company_admin_pay_for_users'), post_data, follow=True)
        self.assertRedirects(response, reverse('company_structure'))
        p = Payment.objects.get(pk=4)
        self.assertEquals(p.status, 1005)

        response = self.client.get(reverse('invoices'))
        self.assertContains(response, "Testing User 1")

        post_data = {
            'create_invoice': 'on',
            'submit': 'Odeslat',
            'order_number': 1323575433,
        }
        if beneficiary:
            post_data['company_pais_benefitial_fee'] = "on"
        response = self.client.post(reverse('invoices'), post_data, follow=True)
        self.assertRedirects(response, reverse('invoices'))
        p = Payment.objects.get(pk=4)
        self.assertEquals(p.status, 1006)
        if beneficiary:
            self.assertEquals(p.invoice.total_amount, 544)
        else:
            self.assertEquals(p.invoice.total_amount, 175)
        pdf = PdfFileReader(p.invoice.invoice_pdf)
        pdf_string = pdf.pages[0].extractText()
        if beneficiary:
            self.assertTrue("Celkem: 450,-" in pdf_string)
        else:
            self.assertTrue("Celkem: 145,-" in pdf_string)
        self.assertTrue("1323575433" in pdf_string)
        self.assertTrue("Testing company" in pdf_string)

    def test_company_payment(self):
        self.company_payment()

    def test_company_payment_beneficiary(self):
        self.company_payment(beneficiary=True)

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

    def test_dpnk_company_admin_application(self):
        post_data = {
            'motivation_company_admin': 'Testing position',
            'will_pay_opt_in': True,
            'submit': 'Odeslat',
        }
        response = self.client.post(reverse('company_admin_application'), post_data, follow=True)
        self.assertRedirects(response, reverse('profil'))
        company_admin = models.CompanyAdmin.objects.get(user__username='test')
        self.assertEquals(company_admin.motivation_company_admin, 'Testing position')

    def test_dpnk_views_gpx_file(self):
        trip = mommy.make(models.Trip, user_attendance=self.user_attendance, date=datetime.date(year=2010, month=11, day=20), direction='trip_from')
        gpxfile = mommy.make(models.GpxFile, user_attendance=self.user_attendance, trip_date=datetime.date(year=2010, month=11, day=20), direction='trip_from')

        address = reverse('gpx_file', kwargs={"id": gpxfile.pk})
        response = self.client.get(address)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(models.GpxFile.objects.get(pk=gpxfile.pk).trip, trip)


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=12, day=1),
)
class ViewsTestsRegistered(TransactionTestCase):
    fixtures = ['campaign', 'views', 'users', 'transactions', 'batches']

    def setUp(self):
        self.client = Client(HTTP_HOST="testing-campaign.testserver")
        self.assertTrue(self.client.login(username='test', password='test'))
        call_command('denorm_init')
        call_command('denorm_rebuild')
        self.user_attendance = UserAttendance.objects.get(userprofile__user__username='test')
        self.assertTrue(self.user_attendance.entered_competition())

    def tearDown(self):
        call_command('denorm_drop')

    def test_dpnk_rides_view(self):
        response = self.client.get(reverse('profil'))
        self.assertContains(response, 'form-0-commute_mode')
        self.assertContains(response, 'form-1-commute_mode')
        self.assertEquals(self.user_attendance.user_trips.count(), 1)
        post_data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-id': 1,
            'form-0-commute_mode': 'by_foot',
            'form-0-distance': '28.89',
            'form-0-user_attendance': 12,
            'form-0-direction': 'trip_to',
            'form-0-user_attendance': 1115,
            'form-0-date': datetime.date(year=2010, month=12, day=1),
            'form-1-id': '',
            'form-1-commute_mode': 'bicycle',
            'form-1-distance': '2',
            'form-1-user_attendance': 1115,
            'form-1-direction': 'trip_from',
            'form-1-date': datetime.date(year=2010, month=12, day=1),
            'submit': 'Odeslat',
        }
        response = self.client.post(reverse('profil'), post_data, follow=True)
        self.assertContains(response, 'form-1-commute_mode')
        self.assertEquals(self.user_attendance.user_trips.count(), 2)
        self.assertEquals(models.Trip.objects.get(pk=1).distance, 28.89)
        self.assertEquals(models.Trip.objects.exclude(pk=1).get().commute_mode, 'bicycle')
        denorm.flush()
        user_attendance = UserAttendance.objects.get(userprofile__user__username='test')
        self.assertEquals(user_attendance.trip_length_total, 30.89)
        self.assertEquals(user_attendance.team.get_length(), 10.296666666666667)

    def test_dpnk_views_create_gpx_file(self):
        date = datetime.date(year=2010, month=12, day=1)
        direction = "trip_from"
        trip = mommy.make(models.Trip, user_attendance=self.user_attendance, date=date, direction=direction)
        address = reverse('gpx_file_create', kwargs={"date": date, "direction": direction})
        with open('apps/dpnk/test_files/modranska-rokle.gpx', 'rb') as gpxfile:
            post_data = {
                'file': gpxfile,
                'direction': direction,
                'trip_date': date,
                'user_attendance': self.user_attendance.pk,
                'submit': 'Odeslat',
            }
            response = self.client.post(address, post_data, follow=True)
            self.assertRedirects(response, reverse('profil'))
        gpxfile = models.GpxFile.objects.get(trip_date=date, direction=direction, user_attendance=self.user_attendance)
        trip = models.Trip.objects.get(pk=trip.pk)
        self.assertEquals(trip.distance, 13.32)


class TestTeams(TestCase):
    fixtures = ['campaign', 'users']

    def setUp(self):
        call_command('denorm_init')
        call_command('denorm_rebuild')

    def tearDown(self):
        call_command('denorm_drop')

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


class ResultsTests(TestCase):
    fixtures = ['users', 'campaign', 'test_results_data']

    def setUp(self):
        call_command('denorm_init')
        call_command('denorm_rebuild')

    def tearDown(self):
        call_command('denorm_drop')

    def test_get_competitors(self):
        team = Team.objects.get(id=1)
        query = results.get_competitors(Competition.objects.get(id=0))
        self.assertListEqual(list(query.all()), [team])


class ModelTests(TestCase):
    fixtures = ['users', 'campaign', 'transactions', 'batches']

    def setUp(self):
        call_command('denorm_init')

    def tearDown(self):
        call_command('denorm_drop')

    def test_payment_type_string(self):
        user_attendance = UserAttendance.objects.get(userprofile__user__username='test')
        user_attendance.save()
        call_command('denorm_flush')
        self.assertEquals(user_attendance.payment_type_string(), "FIRMA PLATÍ FAKTUROU")

    def test_payment_type_string_none_type(self):
        user_attendance = UserAttendance.objects.get(userprofile__user__username='test')
        user_attendance.representative_payment = Payment(pay_type=None)
        self.assertEquals(user_attendance.payment_type_string(), None)


class DenormTests(TestCase):
    fixtures = ['users', 'campaign', 'transactions', 'batches']

    def setUp(self):
        call_command('denorm_init')

    def tearDown(self):
        call_command('denorm_drop')

    def test_name_with_members(self):
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


class RunChecksTestCase(TestCase):
    def test_checks(self):
        django.setup()
        from django.core import checks
        all_issues = checks.run_checks()
        errors = [str(e) for e in all_issues if e.level >= checks.ERROR]
        if errors:
            self.fail('checks failed:\n' + '\n'.join(errors))
