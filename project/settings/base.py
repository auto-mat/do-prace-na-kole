# -*- coding: utf-8 -*-
# Django settings for DPNK project.

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2015 o.s. Auto*Mat
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import base64
import os
import re
import sys
import unicodedata

import django.conf.locale
from django.contrib.messages import constants as message_constants
from django.urls import reverse_lazy
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from model_utils import Choices


def normpath(*args):
    return os.path.normpath(os.path.abspath(os.path.join(*args)))


PROJECT_ROOT = normpath(__file__, "..", "..", "..")
BASE_DIR = PROJECT_ROOT

sys.path.append(normpath(PROJECT_ROOT, "project"))

DEBUG = os.environ.get('DPNK_DEBUG', False) in (True, "True")
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Petr Dlouhý', 'petr.dlouhy@auto-mat.cz'),
)
DEFAULT_FROM_EMAIL = 'Do práce na kole <kontakt@dopracenakole.cz>'
MANAGERS = ADMINS
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DPNK_DB_ENGINE', 'django.contrib.gis.db.backends.postgis'),
        'NAME': os.environ.get('DPNK_DB_NAME', ''),
        'USER': os.environ.get('DPNK_DB_USER', ''),
        'PASSWORD': os.environ.get('DPNK_DB_PASSWORD', ''),
        'HOST': os.environ.get('DPNK_DB_HOST', 'localhost'),
        'PORT': os.environ.get('DPNK_DB_PORT', ''),
    },
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

DPNK_CACHE_REDIS_LOCATION = os.environ.get('DPNK_CACHE_REDIS_LOCATION', None)
if DPNK_CACHE_REDIS_LOCATION is not None:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': DPNK_CACHE_REDIS_LOCATION,
        },
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
            'KEY_PREFIX': 'dpnkch',
        },
    }

LOCALE_PATHS = (
    normpath(PROJECT_ROOT, 'avatar_locale/locale'),
    normpath(PROJECT_ROOT, 'dpnk/locale'),
    normpath(PROJECT_ROOT, 'coupons/locale'),
    normpath(PROJECT_ROOT, 't_shirt_delivery/locale'),
    normpath(PROJECT_ROOT, 'stravasync/locale'),
)
TIME_ZONE = 'Europe/Prague'
LANGUAGES = (
    ('dsnkcs', _('Do školy na kole - czech')),
    ('cs', _('Czech')),
    ('en', _('English')),
)
LANGUAGE_CODE = 'cs'
MODELTRANSLATION_DEFAULT_LANGUAGE = 'cs'
MODELTRANSLATION_LANGUAGES = ('en', 'cs', 'dsnkcs')
MODELTRANSLATION_FALLBACK_LANGUAGES = ('cs', 'dsnkcs', 'en')
MODELTRANSLATION_ENABLE_FALLBACKS = True
SITE_ID = os.environ.get('DPNK_SITE_ID', 1)
USE_I18N = True
USE_L10N = True

IMPORT_EXPORT_TMP_STORAGE_CLASS = 'import_export.tmp_storages.MediaStorage'

MEDIA_ROOT = os.environ.get('DPNK_MEDIA_ROOT', normpath(PROJECT_ROOT, 'media/upload'))
MEDIA_URL = os.environ.get('DPNK_MEDIA_URL', '/media/upload/')
STATIC_ROOT = os.environ.get('DPNK_STATIC_ROOT', normpath(PROJECT_ROOT, "static"))
STATIC_URL = os.environ.get('DPNK_STATIC_URL', '/static/')

EMAIL_BACKEND = os.environ.get('DPNK_EMAIL_BACKEND', 'djcelery_email.backends.CeleryEmailBackend')

AWS_ACCESS_KEY_ID = os.environ.get('DPNK_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('DPNK_AWS_SECRET_ACCESS_KEY')
AWS_S3_HOST = os.environ.get('DPNK_AWS_S3_HOST', 's3-eu-west-1.amazonaws.com')
AWS_STORAGE_BUCKET_NAME = os.environ.get('DPNK_AWS_STORAGE_BUCKET_NAME', 'dpnk')
AWS_QUERYSTRING_AUTH = os.environ.get('AWS_QUERYSTRING_AUTH', True)
AWS_QUERYSTRING_EXPIRE = os.environ.get('AWS_QUERYSTRING_EXPIRE', 60 * 60 * 24 * 365 * 10)
AWS_DEFAULT_ACL = "private"

if AWS_ACCESS_KEY_ID:
    THUMBNAIL_DEFAULT_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    CELERY_EMAIL_BACKEND = os.environ.get('DPNK_CELERY_EMAIL_BACKEND', 'django_ses.SESBackend')
    AWS_SES_REGION_NAME = 'eu-west-1'
    AWS_SES_REGION_ENDPOINT = 'email.eu-west-1.amazonaws.com'

    DBBACKUP_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    DBBACKUP_STORAGE_OPTIONS = {
        'access_key': AWS_ACCESS_KEY_ID,
        'secret_key': AWS_SECRET_ACCESS_KEY,
        'bucket_name': 'dpnk-dbbackup',
    }

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)


SECRET_KEY = os.environ.get('DPNK_SECRET_KEY')
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'subdomains.middleware.SubdomainMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'denorm.middleware.DenormMiddleware',
    'author.middlewares.AuthorDefaultBackendMiddleware',
    'dpnk.middleware.UserAttendanceMiddleware',
    'dpnk.votes.SecretBallotUserMiddleware',
    'raven.contrib.django.raven_compat.middleware.Sentry404CatchMiddleware',
]
AUTHENTICATION_BACKENDS = (
    'social_core.backends.open_id.OpenIdAuth',
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',

    'django.contrib.auth.backends.ModelBackend',
    'dpnk.auth.EmailModelBackend',
    "django_su.backends.SuBackend",
)
ROOT_URLCONF = 'urls'

SOCIAL_AUTH_URL_NAMESPACE = 'social'
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get('DPNK_SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('DPNK_SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')
SOCIAL_AUTH_FACEBOOK_KEY = os.environ.get('DPNK_SOCIAL_AUTH_FACEBOOK_KEY', '')
SOCIAL_AUTH_FACEBOOK_SECRET = os.environ.get('DPNK_SOCIAL_AUTH_FACEBOOK_SECRET', '')
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id,name,email,gender',
}

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'dpnk.social_pipeline.create_userprofile',
)


class InvalidStringShowWarning(str):
    def __mod__(self, other):
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Undefined variable or unknown value for: '%s'" % (other,))
        return ""


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            normpath(PROJECT_ROOT, 'templates'),
            normpath(PROJECT_ROOT, 'dpnk/templates'),
            normpath(PROJECT_ROOT, 't_shirt_delivery/templates'),
            normpath(PROJECT_ROOT, 'registration-templates/'),
        ],
        'OPTIONS': {
            'string_if_invalid': InvalidStringShowWarning("%s"),
            'context_processors': (
                'django.contrib.messages.context_processors.messages',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'dpnk.context_processors.user_attendance',
                'settings_context_processor.context_processors.settings',
                # This is causing lots of database hits on every request and probaly isn't needed:
                # 'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ),
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]
INSTALLED_APPS = (
    'modeltranslation',
    'admin_view_permission',
    'admin_views',

    'django_su',
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.sessions',
    'nested_admin',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.postgres',
    'django.contrib.gis',
    'django.contrib.sites',

    'registration',

    'price_level',
    'coupons',
    'dpnk',
    't_shirt_delivery',
    'stravasync',
    'psc',
    'stale_notifications',

    'smart_selects',
    'composite_field',
    'softhyphen',
    'django_extensions',
    'chart_tools',
    'import_export',
    'polymorphic',
    'author',
    'fieldsignals',
    'corsheaders',
    'adminsortable2',
    'reportlab',
    'dbbackup',
    'related_admin',
    'easy_thumbnails',
    'crispy_forms',
    'adminfilters',
    'django_bleach',
    'avatar',
    'gtm',
    'leaflet',
    'settings_context_processor',
    'oauth2_provider',
    'rest_framework',
    'rest_framework_gis',
    'rest_framework.authtoken',
    'bulk_update',
    'denorm',
    'subdomains',
    'redactor',
    'scribbler',
    'selectable',
    'raven.contrib.django.raven_compat',
    'bootstrap4',
    'daterange_filter',
    'storages',
    'favicon',
    'adminactions',
    'massadmin',
    'advanced_filters',
    'djcelery_email',
    'django_celery_beat',
    'smmapdfs',
    'secretballot',
    'sitetree',
    'sitetree_modeltranslation',
    'likes',
    'colorfield',
    'social_django',
    'fm',
    # 'cachalot',
    'photologue',
    'sortedm2m',
    # 'dj_anonymizer',
)

ECC_PROVIDER_CODE = "DK"
ECC_URL_BASE = "http://srv.cycling365.eu/services"

TEMPLATE_VISIBLE_SETTINGS = (
    'PAYU_POS_AUTH_KEY',
    'PAYU_POS_ID',
    'PAYU_KEY_1',
    'HEADER_COLOR',
    'AKLUB_URL',
)

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.AllowAny',),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.authentication.OAuth2Authentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
}

REDACTOR_OPTIONS = {
    "plugins": ["source"],
    'formatting': ['div', 'p', 'blockquote', 'pre', 'h4', 'h5'],
    'imageResizable': 'true',
    'imagePosition': 'true',
}
BLEACH_ALLOWED_TAGS = [
    'a',
    'b',
    'blockquote',
    'br',
    'div',
    'em',
    'figure',
    'h4',
    'h5',
    'i',
    'img',
    'li',
    'ol',
    'p',
    'pre',
    'span',
    'strong',
    'u',
    'ul',
]
BLEACH_ALLOWED_ATTRIBUTES = [
    'height',
    'href',
    'src',
    'style',
    'width',
]
BLEACH_ALLOWED_STYLES = ['height', 'width']

CRISPY_TEMPLATE_PACK = 'bootstrap4'
SERVER_EMAIL = 'kontakt@dopracenakole.cz'
LOGIN_URL = reverse_lazy('login')
LOGIN_REDIRECT_URL = reverse_lazy("profil")
LOGOUT_NEXT_PAGE = reverse_lazy('profil')
REGISTRATION_AUTO_LOGIN = True
DJANGO_URL = ''
USE_DJANGO_JQUERY = True
JQUERY_URL = None
AKLUB_URL = os.environ.get('DPNK_AKLUB_URL', "https://klub.auto-mat.cz")

LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (50.0866699218750000, 14.4387817382809995),
    'TILES': [
        (
            _(u'cyklomapa'),
            'https://tiles.prahounakole.cz/{z}/{x}/{y}.png',
            {'attribution': u'&copy; přispěvatelé <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}),
        (
            _(u'Všeobecná mapa'),
            'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            {'attribution': u'&copy; přispěvatelé <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}),
    ],
    'DEFAULT_ZOOM': 8,
    'MIN_ZOOM': 8,
    'MAX_ZOOM': 18,
    'SPATIAL_EXTENT': [11.953, 48.517, 19.028, 51.097],
}

CORS_ORIGIN_REGEX = [
    r'^(https?://)?(\w+\.)?dopracenakole\.cz$',
]

DBBACKUP_BACKUP_DIRECTORY = normpath(PROJECT_ROOT, 'db_backup')

MAX_COMPETITIONS_PER_COMPANY = 8

MAILING_API_KEY = os.environ.get('DPNK_MAILING_API_KEY', '')
ECOMAIL_MAILING_API_KEY = os.environ.get('DPNK_ECOMAIL_MAILING_API_KEY', '')

GLS_USERNAME = os.environ.get('GLS_USERNAME', '')
GLS_PASSWORD = os.environ.get('GLS_PASSWORD', '')
GLS_BASE_URL = os.environ.get('GLS_BASE_URL', 'http://test.online.gls-czech.com')

FIO_TOKEN = os.environ.get('DPNK_FIO_TOKEN', '')

PAYU_KEY_1 = os.environ.get('DPNK_PAYU_KEY_1', '')
PAYU_KEY_2 = os.environ.get('DPNK_PAYU_KEY_2', '')
PAYU_POS_AUTH_KEY = os.environ.get('DPNK_PAYU_POS_AUTH_KEY', '')
PAYU_POS_ID = os.environ.get('DPNK_PAYU_POS_ID', '')

ACCOUNT_ACTIVATION_DAYS = 5

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s',
        },
        'simple': {
            'format': '%(levelname)s %(message)s',
        },
        'plain': {
            'format': '%(asctime)s %(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'sentry': {
            'level': 'WARNING',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            'tags': {'custom-tag': 'x'},
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.environ.get('DPNK_LOG_FILE', "dpnk.log"),
            'backupCount': 50,
            'maxBytes': 10000000,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
    },
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry', 'logfile', 'console'],
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'logfile', 'mail_admins', 'sentry'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console', 'logfile', 'mail_admins', 'sentry'],
            'level': 'ERROR',
            'propagate': False,
        },
        'dpnk': {
            'handlers': ['console', 'logfile', 'mail_admins', 'sentry'],
            'level': 'INFO',
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console', 'logfile', 'mail_admins', 'sentry'],
            'propagate': False,
        },
        # Don't send HTTP_HEADER warnings since it is too verbose on Amazon AWS.
        # Better soulution would be to filter invalid requests before reaching Django.
        'django.security.DisallowedHost': {
            'handlers': ['mail_admins', 'sentry'],
            'level': 'CRITICAL',
            'propagate': False,
        },
    },
}

RAVEN_CONFIG = {
    'dsn': os.environ.get('DPNK_RAVEN_DNS', ''),
    'string_max_length': 10000,
}

try:
    with open('static/version.txt') as f:
        RAVEN_CONFIG['release'] = f.readline().strip()
except FileNotFoundError:
    pass

GOOGLE_TAG_ID = os.environ.get('DPNK_GOOGLE_TAG_ID', '')

ALLOWED_HOSTS = os.environ.get('DPNK_ALLOWED_HOSTS', '').split(',')

BROKER_URL = os.environ.get('DPNK_BROKER_URL', '')

MIGRATION_MODULES = {
    'price_level': 'price_level_migrations',
}

CSRF_COOKIE_SECURE = os.environ.get("DPNK_CSRF_COOKIE_SECURE", True)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 60
SECURE_SSL_REDIRECT = os.environ.get("DPNK_SECURE_SSL_REDIRECT", True)
SESSION_COOKIE_SECURE = os.environ.get("DPNK_SESSION_COOKIE_SECURE", True)
SECURE_REDIRECT_EXEMPT = [r"version\.txt"]
X_FRAME_OPTIONS = 'DENY'

MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'danger',
}

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

HEADER_COLOR = os.environ.get('DPNK_HEADER_COLOR', "red")

IGNORABLE_404_URLS = [
    re.compile(r'^/apple-touch-icon.*\.png$'),
    re.compile(r'^/favicon\.ico$'),
    re.compile(r'^/robots\.txt$'),
    re.compile(r'^/wordpress$'),
    re.compile(r'^/wp$'),
    re.compile(r'wp-login'),
    re.compile(r'wp-admin'),
    re.compile(r'^/blog$'),
    re.compile(r'^/sitenews$'),
    re.compile(r'^/site$'),
    re.compile(r'^/browserconfig.xml$'),
    re.compile(r'^/humans.txt$'),
    re.compile(r'^/.well-known/dnt-policy.txt$'),
    re.compile(r'^/blog/robots.txt$'),
    re.compile(r'^xmlrpc.php$'),
    re.compile(r'^/android-chrome-.*\.png$'),
]

FAVICON_PATH = STATIC_URL + 'img/favicon/favicon.ico'

PRICE_LEVEL_MODEL = 'dpnk.Campaign'
PRICE_LEVEL_CATEGORY_CHOICES = Choices(('basic', _('Základní')), ('company', _('Pro firmy')))
PRICE_LEVEL_CATEGORY_DEFAULT = 'basic'

SITETREE_MODEL_TREE_ITEM = 'sitetree_modeltranslation.ModeltranslationTreeItem'

# We have large inline fields, so it is necesarry to set this
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

# import local settings
try:
    from .settings_local import *  # noqa
except ImportError:
    pass

DATABASE_CONFIGURED = DATABASES['default']['NAME'] != ''


EXTRA_LANG_INFO = {
    'dsnkcs': {
        'bidi': False,
        'code': 'dsnkcs',
        'name': 'Do Školy na kole',
        'name_local': u'Do skoly na kole',
    },
}

LANG_INFO = {**django.conf.locale.LANG_INFO, **EXTRA_LANG_INFO}
django.conf.locale.LANG_INFO = LANG_INFO

STRAVA_FINE_POLYLINES = os.environ.get('STRAVA_FINE_POLYLINES', True)
STRAVA_CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID', None)
STRAVA_CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET', None)
STRAVA_MAX_USER_SYNC_COUNT = 16

SMMAPDFS_CELERY = True
SMMAPDFS_EMAIL_CONTEXT_HELP = """<br/>
{{name}} - Name of User<br/>
{{name_vocative}} - Vocative case of name of user<br/>
{{diplomas_page}} - Page where diplomas are shown<br/>
"""

DENORM_MAX_PROCESS_COUNT = os.environ.get('DENORM_MAX_PROCESS_COUNT', 100)


AVATAR_CACHE_ENABLED = False
AVATAR_AUTO_GENERATE_SIZES = (30, 80, 150)
AVATAR_FACEBOOK_GET_ID = 'dpnk.avatar.get_facebook_id'
AVATAR_DEFAULT_URL = 'img/default-avatar.png'
AVATAR_MAX_AVATARS_PER_USER = 1
AVATAR_GRAVATAR_DEFAULT = 'mp'
AVATAR_MAX_SIZE = 10 * 1024 * 1024
AVATAR_THUMB_FORMAT = 'PNG'
AVATAR_PROVIDERS = (
    'avatar.providers.PrimaryAvatarProvider',
    'avatar.providers.FacebookAvatarProvider',
    'avatar.providers.GravatarAvatarProvider',
    'avatar.providers.DefaultAvatarProvider',
)


def photologue_path(instance, filename):
    fn = unicodedata.normalize('NFKD', force_text(filename)).encode('ascii', 'ignore').decode('ascii')
    return os.path.join('photologue', 'photos', base64.b64encode(os.urandom(18)).decode('utf8') + fn)


PHOTOLOGUE_PATH = photologue_path
