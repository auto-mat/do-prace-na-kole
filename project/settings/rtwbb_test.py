from .base import *  # noqa


RTWBB_FRONTEND_APP_BASE_URL = os.getenv(
    "RTWBB_FRONTEND_APP_BASE_URL",
    "https://rtwbb-test.dopracenakole.net/#/",
)

rtwbb_frontend_app_base_url_split_char = ","
rtwbb_frontend_app_base_url_fragment_identifier = "/#/"
if rtwbb_frontend_app_base_url_split_char in RTWBB_FRONTEND_APP_BASE_URL:
    urls = RTWBB_FRONTEND_APP_BASE_URL.split(rtwbb_frontend_app_base_url_split_char)
    for url in urls:
        CORS_ORIGIN_REGEX.append(
            url.rstrip(rtwbb_frontend_app_base_url_fragment_identifier)
        )
    RTWBB_FRONTEND_APP_BASE_URL = urls[0]
else:
    CORS_ORIGIN_REGEX.append(
        RTWBB_FRONTEND_APP_BASE_URL.rstrip(
            rtwbb_frontend_app_base_url_fragment_identifier
        )
    )

ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = RTWBB_FRONTEND_APP_BASE_URL

ACCOUNT_EMAIL_CONFIRMATION_URL = f"{RTWBB_FRONTEND_APP_BASE_URL}confirm-email"
ACCOUNT_RESET_PASSWORD_CONFIRMATION_URL = f"{RTWBB_FRONTEND_APP_BASE_URL}reset-password"
STRAVA_APP_REDIRECT_URL = (
    f"{RTWBB_FRONTEND_APP_BASE_URL}routes/connect-third-party-apps"
)
ACCOUNT_ADAPTER = "dpnk.allauth.AccountAdapter"
SOCIALACCOUNT_ADAPTER = "dpnk.allauth.SocialAccountAdapter"

REST_AUTH["PASSWORD_RESET_SERIALIZER"] = "dpnk.allauth.UserPasswordResetSerializer"
