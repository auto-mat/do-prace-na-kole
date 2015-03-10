# -*- coding: utf-8 -*-
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.translation import ugettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from dpnk.forms import SubmitMixin


class EmailModelBackend(ModelBackend):
    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email__iexact=username)
            except User.DoesNotExist:
                return None

        if user.check_password(password):
            return user

class PasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _(u'Odeslat')))
        super(PasswordResetForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        """
        Validate that the email is not already in use.
        """
        if User.objects.filter(email__iexact=self.cleaned_data['email']).exists():
            return self.cleaned_data['email']
        else:
            raise forms.ValidationError(_(u"Tento email v systému není zanesen."))


class PasswordChangeForm(SubmitMixin, PasswordChangeForm):
   pass
