# -*- coding: utf-8 -*-
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.translation import ugettext_lazy as _
from crispy_forms.helper import FormHelper
from django.template import RequestContext
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate, get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template import loader
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

    #TODO: This is copy of original save method only adding RequestContext. This is quicfix, it should be done some more elegant way.
    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        from django.core.mail import send_mail
        UserModel = get_user_model()
        email = self.cleaned_data["email"]
        active_users = UserModel._default_manager.filter(
            email__iexact=email, is_active=True)
        for user in active_users:
            # Make sure that no email is sent to a user that actually has
            # a password marked as unusable
            if not user.has_usable_password():
                continue
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            c = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
            }
            subject = loader.render_to_string(subject_template_name, c, context_instance=RequestContext(request))
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            email = loader.render_to_string(email_template_name, c, context_instance=RequestContext(request))

            if html_email_template_name:
                html_email = loader.render_to_string(html_email_template_name, c, context_instance=RequestContext(request))
            else:
                html_email = None
            send_mail(subject, email, from_email, [user.email], html_message=html_email)



class PasswordChangeForm(SubmitMixin, PasswordChangeForm):
   pass
