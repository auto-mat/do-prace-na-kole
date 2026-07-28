import base64
import logging

from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import authentication
from rest_framework import exceptions
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)


class PayUNotifyOrderRequestAuthentification(authentication.BaseAuthentication):
    """Authentificate PayU order notify POST request

    See PayUPaymentNotifyPost() REST API URL class endpoint
    """

    def authenticate(self, request):
        authorization_header = request.META.get("HTTP_AUTHORIZATION")
        if not authorization_header:
            raise exceptions.AuthenticationFailed(
                _("Request objekt má chybějící <Authorization: Basic> záhlaví.")
            )
        try:
            decoded_auth_header = base64.b64decode(
                authorization_header.replace("Basic ", "")
            ).decode()
        except base64.binascii.Error:
            raise exceptions.AuthenticationFailed(
                _(
                    "Dekódovanie Authorization Basic header <%(auth_header)s> záhlaví selhalo."
                )
                % {"auth_header": authorization_header.replace("Basic ", "")}
            )
        if (":") not in decoded_auth_header:
            raise exceptions.AuthenticationFailed(
                _(
                    "Nesprávný formát Authorization Basic záhlaví. Prosím použijte <username:password> formát."
                )
            )
        payu_client_id, payu_rest_api_second_key_md5 = decoded_auth_header.split(":")
        if (
            payu_client_id == settings.PAYU_CONF["PAYU_REST_API_CLIENT_ID"]
            and payu_rest_api_second_key_md5
            == settings.PAYU_CONF["PAYU_REST_API_SECOND_KEY_MD5"]
        ):
            logger.info("PayU order notify request was authentificate sucessfully.")
            return (True, None)
        logger.info(
            "PayU order notify request was authentificate unsucessfully."
            " Invalid username or password."
        )
        raise exceptions.AuthenticationFailed(
            _("Neplatné uživatelské jméno nebo heslo.")
        )


def get_tokens_for_user(user, lifetime=1, lifetime_unit="days"):
    """Manualy generate simple JWT tokens with defined lifetime

    :param User user: User model instance
    :param int lifetime: Access token lifetime value with default value
                         1 day
    :param str lifetime_unit: Access token lifetime unit with default
                              value days

    :return dict: With refresh/access (key) token string and expiration
                  date time string with timezone offset
                  {
                    "refresh" : {
                        "token": "<TOKEN>"
                        "expiration": "<EXPIRATION DATE TIME>"
                    },
                    "access" : {
                        "token": "<TOKEN>"
                        "expiration": "<EXPIRATION DATE TIME>"
                    },
                }
    """
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    lifetime = {lifetime_unit: lifetime}
    access_token.set_exp(lifetime=timezone.timedelta(**lifetime))

    return {
        "refresh": {
            "token": str(refresh),
            "expiration": timezone.datetime.fromtimestamp(refresh["exp"])
            .astimezone()
            .isoformat(),
        },
        "access": {
            "token": str(access_token),
            "expiration": timezone.datetime.fromtimestamp(access_token["exp"])
            .astimezone()
            .isoformat(),
        },
    }
