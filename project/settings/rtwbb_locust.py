from .base import *  # noqa


ALLOWED_HOSTS = [
    ".lvh.me",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
}

RTWBB_FRONTEND_APP_BASE_URL = os.getenv(
    "RTWBB_FRONTEND_APP_BASE_URL",
    "https://rtwbb-test.dopracenakole.net/#/",
)

ACCOUNT_EMAIL_VERIFICATION = "none"

db_name = os.environ.get("DPNK_DB_NAME", "dpnk")
db_user = os.environ.get("DPNK_DB_USER", "dpnk")
db_password = os.environ.get("DPNK_DB_PASSWORD", "")
db_host = os.environ.get("DPNK_DB_HOST", "localhost")
db_port = os.environ.get("DPNK_DB_PORT", "")

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": db_name,
        "USER": db_user,
        "PASSWORD": db_password,
        "HOST": db_host,
        "PORT": db_port,
        "CONN_MAX_AGE": 0,
    },
}

CELERY_RESULT_BACKEND = "db+postgresql://{user}:{password}@{host}/{db_name}".format(
    user=db_user,
    password=db_password,
    host=db_host,
    db_name=db_name,
)

STRAVA_APP_REDIRECT_URL = f"{RTWBB_FRONTEND_APP_BASE_URL}connect-third-party-apps"
ACCOUNT_ADAPTER = "dpnk.allauth.AccountAdapter"
SOCIALACCOUNT_ADAPTER = "dpnk.allauth.SocialAccountAdapter"

REST_AUTH["PASSWORD_RESET_SERIALIZER"] = "dpnk.allauth.UserPasswordResetSerializer"
