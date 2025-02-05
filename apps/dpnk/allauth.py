from django.conf import settings
from django.utils.http import urlencode

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.models import EmailAddress
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_pk_to_url_str
from dj_rest_auth.serializers import PasswordResetSerializer


class AccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        if hasattr(settings, "ACCOUNT_EMAIL_CONFIRMATION_URL"):
            key = emailconfirmation.key
            email = emailconfirmation.email_address.email
            return f"{settings.ACCOUNT_EMAIL_CONFIRMATION_URL}?{urlencode({'key': key, 'email': email})}"
        else:
            return super().get_email_confirmation_url(request, emailconfirmation)


class UserPasswordResetSerializer(PasswordResetSerializer):
    """
    User password reset serializer with overrided default reset password
    confirmation email URL
    """

    def _reset_pass_url_generator(self, request, user, temp_key):
        """Override reset password confirmation email URL"""
        uid = user_pk_to_url_str(user)
        return f"{settings.ACCOUNT_RESET_PASSWORD_CONFIRMATION_URL}?uid={uid}&token={temp_key}"

    def get_email_options(self):
        return {"url_generator": self._reset_pass_url_generator}


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Allow login existed user account (login with email/password) with
    social media login with same email address

    https://github.com/pennersr/django-allauth/issues/418#issuecomment-107880925
    """

    def pre_social_login(self, request, sociallogin):
        # Social account already exists, so this is just a login
        if sociallogin.is_existing:
            return

        # Some social logins don't have an email address
        if not sociallogin.email_addresses:
            return

        # Find the first verified email that we get from this sociallogin
        verified_email = None
        for email in sociallogin.email_addresses:
            if email.verified:
                verified_email = email
                break

        # No verified emails found, nothing more to do
        if not verified_email:
            return

        # Check if given email address already exists as a verified email on
        # an existing user's account
        try:
            existing_email = EmailAddress.objects.get(
                email__iexact=email.email,
                verified=True,
            )
        except EmailAddress.DoesNotExist:
            return

        # If it does, connect this new social login to the existing user
        sociallogin.connect(request, existing_email.user)
