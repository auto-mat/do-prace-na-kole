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

from django import forms
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from .forms import SubmitMixin


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


class PasswordResetForm(SubmitMixin, PasswordResetForm):
    def get_users(self, email):
        return User.objects.filter(email__iexact=email, is_active=True)

    def clean_email(self):
        """
        Validate that the email is not already in use.
        """
        if User.objects.filter(email__iexact=self.cleaned_data['email']).exists():
            return self.cleaned_data['email']
        else:
            raise forms.ValidationError(_(u"Tento e-mail v systému není zanesen."))

    def save(self, *args, **kwargs):
        kwargs['extra_email_context'] = {'subdomain': kwargs['request'].subdomain}
        super().save(*args, **kwargs)


class PasswordChangeForm(SubmitMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].required = False
        self.fields['old_password'].help_text = _("V případě, že se dosud přihlašujete pouze přes sociální sítě, nechte prázdné")

    def clean_old_password(self):
        # Allow to set password if not set yet
        if self.user.password == '':
            return self.cleaned_data["old_password"]
        super().clean_old_password()
