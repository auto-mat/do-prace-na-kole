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
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout, Submit

from django import forms
from django.contrib.auth import views as django_views
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from .forms import SubmitMixin, social_html
from .string_lazy import format_html_lazy


class EmailModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            user = User.objects.get(is_active=True, username__iexact=username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(is_active=True, email__iexact=username)
            except User.DoesNotExist:
                return None

        if user.check_password(password):
            return user


class SetPasswordForm(SubmitMixin, SetPasswordForm):
    pass


def clean_email(email):
    user = User.objects.filter(Q(email__iexact=email) | Q(username=email)).first()
    if user:
        if not user.is_active:
            raise forms.ValidationError(
                format_html(
                    _("Problém na trase! Sesedněte z kola a nejprve svůj účet {}."),
                    format_html(
                        "<a href='{activate_url}'>{activate_text}</a>",
                        activate_url=reverse('registration_resend_activation'),
                        activate_text=_("aktivujte"),
                    ),
                ),
            )
        return email
    else:
        error_text = format_html(
            "{text}"
            "<br/>"
            "<a href='{register}'>{register_text}</a>",
            text=_("Problém na trase! Tento e-mail neznáme, zkontrolujte jeho formát. "),
            password=reverse('password_reset'),
            register=reverse('registrace', args=(email,)),
            register_text=_("Jsem tu poprvé a chci se registrovat."),
        )
        raise forms.ValidationError(error_text)


class AuthenticationFormDPNK(AuthenticationForm):
    error_messages = {
        'invalid_login': {
            'password': format_html_lazy(
                "{}"
                "<br/>"
                '<a href="{}">{}</a>',
                _(
                    "Problém na trase! Sesedněte z kola a zkontrolujte si heslo. "
                    "Dejte pozor na malá a velká písmena.",
                ),
                reverse_lazy("password_reset"),
                _("Nepamatujete si heslo?"),
            ),
        },
        'inactive': _("This account is inactive."),
    }

    def clean_username(self):
        """
        Validate that the email is not already in use.
        """
        username = self.cleaned_data['username']
        return clean_email(username)

    def __init__(self, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "noAsterisks"
        self.helper.form_id = "authentication-form"
        self.helper.layout = Layout(
            'username', 'password',
            Submit('submit', _('Přihlásit')),
            social_html(True),
            HTML('<a class="remindme" href="{%% url "password_reset" %%}">%s</a>' % _("Obnovit heslo")),
            HTML('<a class="registerme" href="{%% url "registration_access" %%}">%s</a>' % _("Registrovat")),
            HTML('<a class="register_coordinator" href="{%% url "register_admin" %%}">%s</a>' % _("Registrovat firemního koordinátora")),
        )
        self.fields['username'].label = _("E-mail")
        return ret_val


class PasswordResetForm(SubmitMixin, PasswordResetForm):
    submit_text = _('Obnovit heslo')

    def get_users(self, email):
        return User.objects.filter(email__iexact=email, is_active=True)

    def clean_email(self):
        """
        Validate that the email is not already in use.
        """
        email = self.cleaned_data['email']
        clean_email(email)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_class = "noAsterisks"
        self.fields['email'].label = _("Zadejte e-mail")

    def save(self, *args, **kwargs):
        kwargs['extra_email_context'] = {'subdomain': kwargs['request'].subdomain}
        super().save(*args, **kwargs)


class PasswordChangeForm(SubmitMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_class = "noAsterisks"
        self.fields['old_password'].required = False
        self.fields['old_password'].help_text = _("V případě registrace přes sociální sítě nechte pole prázdné.")
        self.fields['new_password1'].help_text = _("Heslo musí mít minimálně 6 znaků a obsahovat alespoň jedno písmeno.")

    def clean_old_password(self):
        # Allow to set password if not set yet
        if self.user.password == '':
            return self.cleaned_data["old_password"]
        super().clean_old_password()


class PasswordChangeView(django_views.PasswordChangeView):
    template_name = 'base_generic_registration_form.html'
    form_class = PasswordChangeForm
