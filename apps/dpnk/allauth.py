from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.utils.http import urlencode


class AccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        if hasattr(settings, "ACCOUNT_EMAIL_CONFIRMATION_URL"):
            key = emailconfirmation.key
            email = emailconfirmation.email_address.email
            return f"{settings.ACCOUNT_EMAIL_CONFIRMATION_URL}?{urlencode({'key': key, 'email': email})}"
        else:
            return super().get_email_confirmation_url(request, emailconfirmation)
