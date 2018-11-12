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
from unittest.mock import ANY, patch

import denorm

import django
from django.core.management import call_command
from django.test import Client, RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import reverse

from dpnk import company_admin_views, models, util, views
from dpnk.test.util import ClearCacheMixin, DenormMixin
from dpnk.test.util import print_response  # noqa

from freezegun import freeze_time

from model_mommy import mommy

from price_level import models as price_level_models

from .mommy_recipes import testing_campaign


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
        self.assertEqual(payment.pay_type, "kb")

    def test_payment_unsuccesfull(self):
        kwargs = {"trans_id": self.trans_id, "session_id": self.session_id, "pay_type": "kb", "error": 123}
        address = reverse('payment_unsuccessfull', kwargs=kwargs)
        request = self.factory.get(address)
        request.user = self.user_attendance.userprofile.user
        request.user_attendance = self.user_attendance
        request.subdomain = "testing-campaign"
        views.PaymentResult.as_view()(request, success=False, **kwargs)
        payment = models.Payment.objects.get(session_id=self.session_id)
        self.assertEqual(payment.pay_type, "kb")
        self.assertEqual(payment.error, 123)

    def test_payment_redirect(self):
        kwargs = {"trans_id": self.trans_id, "session_id": self.session_id, "pay_type": "kb", "error": 123}
        address = reverse('payment_unsuccessfull', kwargs=kwargs)
        request = self.factory.get(address)
        request.user = self.user_attendance.userprofile.user
        request.user_attendance = self.user_attendance
        request.campaign = models.Campaign.objects.get(pk=338)
        response = views.PaymentResult.as_view()(request, success=False, **kwargs)
        self.assertEqual(response.url, 'http://testing-campaign.localhost:8000/platba_neuspesna/2055/2075-1J1455206457/kb/123/')
        payment = models.Payment.objects.get(session_id=self.session_id)
        self.assertEqual(payment.pay_type, None)
        self.assertEqual(payment.error, None)


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
        self.assertEqual(user.payment_status, 'no_admission')
        self.assertEqual(user.representative_payment, None)
        self.assertEqual(user.payment_class(), 'success')
        self.assertEqual(str(user.get_payment_status_display()), 'neplatí se')

    def test_payment_waiting(self):
        payment = models.Payment.objects.get(pk=4)
        payment.status = 1
        payment.save()
        denorm.flush()
        user = models.UserAttendance.objects.get(pk=1115)
        self.assertEqual(user.payment_status, 'waiting')
        self.assertEqual(user.representative_payment, payment)
        self.assertEqual(user.payment_class(), 'warning')
        self.assertEqual(str(user.get_payment_status_display()), 'nepotvrzeno')

    def test_payment_done(self):
        user = models.UserAttendance.objects.get(pk=1115)
        payment = models.Payment.objects.get(pk=4)
        self.assertEqual(user.payment_status, 'done')
        self.assertEqual(user.representative_payment, payment)
        self.assertEqual(user.payment_class(), 'success')
        self.assertEqual(str(user.get_payment_status_display()), 'zaplaceno')

    def test_payment_unknown(self):
        payment = models.Payment.objects.get(pk=4)
        payment.status = 123
        payment.save()
        denorm.flush()
        user = models.UserAttendance.objects.get(pk=1115)
        self.assertEqual(user.payment_status, 'unknown')
        self.assertEqual(user.representative_payment, payment)
        self.assertEqual(user.payment_class(), 'warning')
        self.assertEqual(str(user.get_payment_status_display()), 'neznámý')

    def test_payment_unknown_none(self):
        models.Payment.objects.all().delete()
        util.rebuild_denorm_models(models.Team.objects.filter(pk__in=[1, 3]))
        util.rebuild_denorm_models(models.UserAttendance.objects.filter(pk=1016))
        user = models.UserAttendance.objects.get(pk=1016)
        self.assertEqual(user.payment_status, 'none')
        self.assertEqual(user.representative_payment, None)
        self.assertEqual(user.payment_class(), 'error')
        self.assertEqual(str(user.get_payment_status_display()), 'žádné platby')


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
        self.assertEqual(payment.pay_type, "kb")
        self.assertEqual(payment.amount, 150)
        self.assertEqual(payment.status, 99)

    @patch('dpnk.views.logger')
    def test_dpnk_payment_status_bad_amount(self, mock_logger):
        response = self.payment_status_view(amount="15300", trans_sig='ae18ec7f141c252e692d470f4c1744c9')
        self.assertContains(response, "Bad amount", status_code=400)
        payment = models.Payment.objects.get(pk=3)
        self.assertEqual(payment.pay_type, None)
        self.assertEqual(payment.amount, 150)
        self.assertEqual(payment.status, 0)
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
        self.assertEqual(payment.pay_type, "kb")
        self.assertEqual(payment.amount, 151)

    def test_dpnk_payment_status_view_create(self):
        response = self.payment_status_view(
            session_id='2075-1J1455206434', amount="15100",
            sig='4f59d25cd3dadaf03bef947bb0d9e1b9', trans_sig='c490e30293fe0a96d08b62107accafe8',
            post_sig='445db4f3e11bfa16f0221b0272820058',
        )
        self.assertContains(response, "OK")
        payment = models.Payment.objects.get(session_id='2075-1J1455206434')
        self.assertEqual(payment.pay_type, "kb")
        self.assertEqual(payment.amount, 151)


def create_get_request(factory, user_attendance, post_data={}, address="", subdomain="testing-campaign"):
    request = factory.get(address, post_data)
    request.user = user_attendance.userprofile.user
    request.user_attendance = user_attendance
    request.campaign = user_attendance.campaign
    request.subdomain = subdomain
    return request


def create_post_request(factory, user_attendance, post_data={}, address="", subdomain="testing-campaign"):
    request = factory.post(address, post_data)
    request.user = user_attendance.userprofile.user
    request.user_attendance = user_attendance
    request.campaign = user_attendance.campaign
    request.subdomain = subdomain
    return request


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=12, day=1),
)
class TestCompanyAdminViews(ClearCacheMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.company = mommy.make("Company")
        self.user_attendance = mommy.make(
            "UserAttendance",
            userprofile__company_admin__campaign=testing_campaign,
            userprofile__company_admin__administrated_company=self.company,
            campaign=testing_campaign,
            team__campaign=testing_campaign,
        )
        mommy.make(
            "Competition",
            name='Pravidelnost společnosti',
            slug='FA-%s-pravidelnost-spolecnosti' % testing_campaign().pk,
            company=self.company,
            campaign=testing_campaign,
        )

    def test_dpnk_company_admin_create_competition(self):
        post_data = {
            'name': 'testing company competition',
            'competition_type': 'length',
            'competitor_type': 'single_user',
            'submit': 'Odeslat',
        }
        request = create_post_request(self.factory, self.user_attendance, post_data)
        response = company_admin_views.CompanyCompetitionView.as_view()(request, success=True)
        self.assertEqual(response.url, reverse('company_admin_competitions'))
        competition = models.Competition.objects.get(name='testing company competition')
        self.assertEqual(competition.slug, 'FA-%s-testing-company-competition' % competition.campaign.pk)

    def test_dpnk_company_admin_edit_competition(self):
        post_data = {
            'name': 'testing company competition fixed',
            'competition_type': 'length',
            'competitor_type': 'single_user',
            'submit': 'Odeslat',
        }
        request = create_post_request(self.factory, self.user_attendance, post_data)
        response = company_admin_views.CompanyCompetitionView.as_view()(
            request,
            success=True,
            competition_slug='FA-%s-pravidelnost-spolecnosti' % testing_campaign().pk,
        )
        self.assertEqual(response.url, reverse('company_admin_competitions'))
        competition = models.Competition.objects.get(name='testing company competition fixed')
        self.assertEqual(competition.slug, 'FA-%s-pravidelnost-spolecnosti' % testing_campaign().pk)

    def test_dpnk_company_admin_create_competition_name_exists(self):
        post_data = {
            'name': 'Pravidelnost společnosti',
            'competition_type': 'length',
            'competitor_type': 'single_user',
            'submit': 'Odeslat',
        }
        request = create_post_request(self.factory, self.user_attendance, post_data)
        response = company_admin_views.CompanyCompetitionView.as_view()(request, success=True)
        self.assertContains(response, "<strong>Položka Soutěžní kategorie s touto hodnotou v poli Jméno soutěže již existuje.</strong>", html=True)

    @override_settings(
        MAX_COMPETITIONS_PER_COMPANY=0,
    )
    def test_dpnk_company_admin_create_competition_max_competitions(self):
        request = create_get_request(self.factory, self.user_attendance)
        request.resolver_match = {"url_name": "company_admin_competition"}
        response = company_admin_views.CompanyCompetitionView.as_view()(request, success=True)
        self.assertContains(response, "Překročen maximální počet soutěží pro organizaci.")

    def test_dpnk_company_admin_create_competition_no_permission(self):
        mommy.make("Competition", slug="FQ-LB")
        request = create_get_request(self.factory, self.user_attendance)
        request.resolver_match = {"url_name": "company_admin_competition"}
        response = company_admin_views.CompanyCompetitionView.as_view()(request, success=True, competition_slug="FQ-LB")
        self.assertContains(response, "K editování této soutěže nemáte oprávnění.")

    def test_dpnk_company_admin_competitions_view(self):
        request = create_get_request(self.factory, self.user_attendance)
        request.resolver_match = {"url_name": "company_admin_competitions"}
        response = company_admin_views.CompanyCompetitionsShowView.as_view()(request, success=True)
        self.assertContains(response, "Pravidelnost společnosti")


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
        self.assertEqual(user_attendance.payment_type_string(), "ORGANIZACE PLATÍ FAKTUROU")

    def test_payment_type_string_none_type(self):
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        user_attendance.representative_payment = models.Payment(pay_type=None)
        self.assertEqual(user_attendance.payment_type_string(), None)


class DenormTests(DenormMixin, ClearCacheMixin, TestCase):
    fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches']

    def test_name_with_members(self):
        util.rebuild_denorm_models(models.Team.objects.filter(pk__in=[2, 3]))
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        user_attendance.team.save()
        call_command('denorm_flush')
        self.assertEqual(user_attendance.team.name_with_members, "Testing team 1 (Nick, Testing User 1, Registered User 1)")
        self.assertEqual(user_attendance.team.unapproved_member_count, 0)
        self.assertEqual(user_attendance.team.member_count, 3)
        user_attendance.userprofile.nickname = "Testing nick"
        user_attendance.userprofile.save()
        call_command('denorm_flush')
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        self.assertEqual(user_attendance.team.name_with_members, "Testing team 1 (Nick, Testing nick, Registered User 1)")
        self.assertEqual(user_attendance.team.unapproved_member_count, 0)
        self.assertEqual(user_attendance.team.member_count, 3)

    def test_name_with_members_delete_userattendance(self):
        user_attendance = models.UserAttendance.objects.get(pk=1115)
        user_attendance.team.save()
        call_command('denorm_flush')
        self.assertEqual(user_attendance.team.name_with_members, "Testing team 1 (Nick, Testing User 1, Registered User 1)")
        self.assertEqual(user_attendance.team.unapproved_member_count, 0)
        self.assertEqual(user_attendance.team.member_count, 3)
        user_attendance.payments().delete()
        user_attendance.delete()
        call_command('denorm_flush')
        team = models.Team.objects.get(pk=1)
        self.assertEqual(team.name_with_members, "Testing team 1 (Nick, Registered User 1)")
        self.assertEqual(team.unapproved_member_count, 0)
        self.assertEqual(team.member_count, 2)

    def test_related_company_admin(self):
        user_attendance = models.UserAttendance.objects.get(pk=1027)
        company_admin = models.CompanyAdmin.objects.create(userprofile=user_attendance.userprofile, campaign_id=338)
        self.assertEqual(user_attendance.related_company_admin, None)
        call_command('denorm_flush')
        user_attendance = models.UserAttendance.objects.get(pk=1027)
        self.assertEqual(user_attendance.related_company_admin, company_admin)


class RunChecksTestCase(ClearCacheMixin, TestCase):
    def test_checks(self):
        django.setup()
        from django.core import checks
        all_issues = checks.run_checks()
        errors = [str(e) for e in all_issues if e.level >= checks.ERROR]
        if errors:
            self.fail('checks failed:\n' + '\n'.join(errors))  # pragma: no cover
