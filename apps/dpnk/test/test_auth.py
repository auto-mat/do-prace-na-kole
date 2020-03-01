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
import base64

from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse

from dpnk.test.test_views import ViewsLogonMommy
from dpnk.test.util import print_response  # noqa

from model_mommy import mommy

from .mommy_recipes import campaign_type


class TestPasswordForms(ViewsLogonMommy):
    def test_password_recovery(self):
        self.client = Client(HTTP_HOST="testing-campaign.example.com", HTTP_REFERER="test-referer")
        mommy.make("User", email='test@test.cz', password=make_password('test_password'))
        address = reverse('password_reset')
        post_data = {
            'email': 'test@test.cz',
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertRedirects(response, reverse('password_reset_done'))
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test@test.cz'])
        self.assertEqual(msg.subject, 'Zapomenuté heslo Do práce na kole')
        self.assertTrue('http://testing-campaign.example.com/zapomenute_heslo/zmena/' in msg.body)

    def test_password_recovery_no_password(self):
        """ Test, that sending password works also for users without password thorough Social auth """
        self.client = Client(HTTP_HOST="testing-campaign.example.com", HTTP_REFERER="test-referer")
        mommy.make("User", email='test@test.cz', password='')
        address = reverse('password_reset')
        post_data = {
            'email': 'test@test.cz',
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertRedirects(response, reverse('password_reset_done'))
        msg = mail.outbox[0]
        self.assertEqual(msg.recipients(), ['test@test.cz'])
        self.assertEqual(msg.subject, 'Zapomenuté heslo Do práce na kole')
        self.assertTrue('http://testing-campaign.example.com/zapomenute_heslo/zmena/' in msg.body)

    def test_password_recovery_unknown_email(self):
        address = reverse('password_reset')
        post_data = {
            'email': 'unknown@test.cz',
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(
            response,
            "<strong>Problém na trase! Tento e-mail neznáme, zkontrolujte jeho formát. <br/> "
            "<a href='/registrace/unknown@test.cz/'>Jsem tu poprvé a chci se registrovat.</a></strong>",
            html=True,
        )

    def test_password_reset_confirm(self):
        user = mommy.make("User", email='test@test.cz')
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uidb64 = base64.b64encode(bytes(str(user.id), "utf-8")).decode("utf-8")
        address = reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})
        response = self.client.get(address, follow=True)
        self.assertContains(
            response,
            '<label for="id_new_password2" class="col-form-label  requiredField">'
            'Potvrzení nového hesla<span class="asteriskField">*</span> </label>',
            html=True,
        )
        self.assertContains(
            response,
            '<input type="submit" name="submit" value="Odeslat" class="btn btn-primary" id="submit-id-submit">',
            html=True,
        )

    def test_password_reset_confirm_post(self):
        """ Test, that password must be at least 6 characters long """
        user = mommy.make("User", email='test@test.cz')
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uidb64 = base64.b64encode(bytes(str(user.id), "utf-8")).decode("utf-8")
        address = reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})
        response1 = self.client.get(address)
        response = self.client.post(response1.url, {"new_password1": "azxkr", "new_password2": "azxkr"})
        self.assertContains(
            response,
            '<strong>Heslo je příliš krátké. Musí mít délku aspoň 6 znaků.</strong>',
            html=True,
        )

    def test_password_reset_confirm_bad_token(self):
        address = reverse('password_reset_confirm', kwargs={'uidb64': 'bad', 'token': 'token'})
        response = self.client.get(address)
        self.assertContains(
            response,
            '<h4>Obnovení hesla nebylo úspěšné</h4>',
            html=True,
        )

    def test_password_change(self):
        response = self.client.get(reverse('password_change'))
        self.assertContains(
            response,
            '<input type="submit" name="submit" value="Odeslat" class="btn btn-primary" id="submit-id-submit">',
            html=True,
        )


class TestEmailBackend(TestCase):
    def setUp(self):
        mommy.make("dpnk.campaign", slug="testing-campaign", campaign_type=campaign_type)
        self.client = Client(HTTP_HOST="testing-campaign.example.com", HTTP_REFERER="test-referer")

    def test_login_by_email(self):
        mommy.make("User", email='test@test.cz', password=make_password('test_password'))
        response = self.client.post(
            reverse('login'),
            {
                'username': 'test@test.cz',
                'password': 'test_password',
            },
        )
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_login_by_email_nonexistent(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': 'test@test.cz',
                'password': 'test_password',
            },
        )
        self.assertContains(
            response,
            '<a href="/registrace/test@test.cz/">Jsem tu poprvé a chci se registrovat.</a>',
            html=True,
        )
