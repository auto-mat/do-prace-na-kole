import base64
import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from rest_framework import authentication
from rest_framework import exceptions

logger = logging.getLogger(__name__)


class PayUNotifyOrderRequestAuthentification(authentication.BaseAuthentication):
    """Authentificate PayU order notify POST request

    See PayUPaymentNotifyPost() REST API URL class endpoint
    """

    def authenticate(self, request):
        authorization_header = request.META.get("HTTP_AUTHORIZATION")
        if not authorization_header:
            raise exceptions.AuthenticationFailed(
                _("Request has missing <Authorization: Basic> header.")
            )
        try:
            decoded_auth_header = base64.b64decode(
                authorization_header.replace("Basic ", "")
            ).decode()
        except base64.binascii.Error:
            raise exceptions.AuthenticationFailed(
                _("Decode Authorization Basic header <%(auth_header)s> failed.")
                % {"auth_header": authorization_header.replace("Basic ", "")}
            )
        if (":") not in decoded_auth_header:
            raise exceptions.AuthenticationFailed(
                _(
                    "Incorrect format of Authorization Basic header. Use <username:password> format."
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
        raise exceptions.AuthenticationFailed(_("Invalid username or password."))
