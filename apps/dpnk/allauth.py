from django.conf import settings
from django.utils.http import urlencode

from allauth.account.adapter import DefaultAccountAdapter
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
