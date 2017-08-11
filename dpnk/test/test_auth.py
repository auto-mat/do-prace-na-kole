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
from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from dpnk.test.test_views import ViewsLogonMommy
from dpnk.test.util import print_response  # noqa

from model_mommy import mommy


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

    def test_password_recovery_unknown_email(self):
        address = reverse('password_reset')
        post_data = {
            'email': 'unknown@test.cz',
        }
        response = self.client.post(address, post_data, follow=True)
        self.assertContains(response, "<strong>Tento e-mail v systému není zanesen.</strong>", html=True)

    def test_password_reset_confirm(self):
        user = mommy.make("User", email='test@test.cz')
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uidb64 = base64.b64encode(bytes(str(user.id), "utf-8")).decode("utf-8")
        address = reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})
        response = self.client.get(address)
        self.assertContains(
            response,
            '<label for="id_new_password2" class="control-label  requiredField">'
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
        response = self.client.post(address, {"new_password1": "a", "new_password2": "a"})
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
            '<h3>Obnovení hesla nebylo úspěšné</h3>',
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
        mommy.make("Campaign", slug='testing-campaign')
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
            '<li>Zadejte správnou hodnotu pole uživatelské jméno a heslo. Pozor, obě pole mohou rozlišovat malá a velká písmena.</li>',
            html=True,
        )
