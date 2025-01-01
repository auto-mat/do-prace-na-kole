from .base import *  # noqa


CORS_ALLOW_ALL_ORIGINS = True

ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = (
    "https://rtwbb-test.dopracenakole.net/#/"
)

ACCOUNT_EMAIL_CONFIRMATION_URL = "https://rtwbb-test.dopracenakole.net/#/confirm-email"
ACCOUNT_ADAPTER = "dpnk.allauth.AccountAdapter"
