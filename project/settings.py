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

import os
import re
import sys

from django.contrib.messages import constants as message_constants
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from model_utils import Choices


def normpath(*args):
    return os.path.normpath(os.path.abspath(os.path.join(*args)))


PROJECT_ROOT = normpath(__file__, "..", "..")

sys.path.append(normpath(PROJECT_ROOT, "project"))

DEBUG = False

PRODUCTION_ENVIRONMENT = os.environ.get('DPNK_PRODUCTION_ENVIRONMENT', False)

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
    normpath(PROJECT_ROOT, 'dpnk/locale'),
    normpath(PROJECT_ROOT, 'coupons/locale'),
    normpath(PROJECT_ROOT, 't_shirt_delivery/locale'),
)
TIME_ZONE = 'Europe/Prague'
LANGUAGES = (
    ('dsnkcs', _('Do školy na kole - czech')),
    ('cs', _('Czech')),
    ('en', _('English')),
)
LANGUAGE_CODE = 'cs'
MODELTRANSLATION_DEFAULT_LANGUAGE = 'cs'
MODELTRANSLATION_LANGUAGES = ('en', 'cs')
SITE_ID = os.environ.get('DPNK_SITE_ID', 1)
USE_I18N = True
USE_L10N = True

IMPORT_EXPORT_TMP_STORAGE_CLASS = 'import_export.tmp_storages.MediaStorage'

MEDIA_ROOT = os.environ.get('DPNK_MEDIA_ROOT', normpath(PROJECT_ROOT, 'media/upload'))
MEDIA_URL = os.environ.get('DPNK_MEDIA_URL', '/media/upload/')
STATIC_ROOT = os.environ.get('DPNK_STATIC_ROOT', normpath(PROJECT_ROOT, "static"))
STATIC_URL = os.environ.get('DPNK_STATIC_URL', '/static/')

AWS_ACCESS_KEY_ID = os.environ.get('DPNK_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('DPNK_AWS_SECRET_ACCESS_KEY')
AWS_S3_HOST = os.environ.get('DPNK_AWS_S3_HOST', 's3-eu-west-1.amazonaws.com')
AWS_STORAGE_BUCKET_NAME = os.environ.get('DPNK_AWS_STORAGE_BUCKET_NAME', 'dpnk')
if AWS_ACCESS_KEY_ID:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    EMAIL_BACKEND = 'django_ses.SESBackend'
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
MIDDLEWARE_CLASSES = [
    # 'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'sslifyadmin.middleware.SSLifyAdminMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'subdomains.middleware.SubdomainMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'denorm.middleware.DenormMiddleware',
    'author.middlewares.AuthorDefaultBackendMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'dpnk.middleware.UserAttendanceMiddleware',
    'raven.contrib.django.raven_compat.middleware.Sentry404CatchMiddleware',
]
AUTHENTICATION_BACKENDS = (
    'dpnk.auth.EmailModelBackend',
    "django_su.backends.SuBackend",
)
ROOT_URLCONF = 'urls'

# CSRF_COOKIE_HTTPONLY = True
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# X_FRAME_OPTIONS = 'DENY'


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
        ],
        'OPTIONS': {
            'string_if_invalid': InvalidStringShowWarning("%s"),
            'context_processors': (
                'django.contrib.messages.context_processors.messages',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'dpnk.context_processors.site',
                'dpnk.context_processors.user_attendance',
                'settings_context_processor.context_processors.settings',
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

    'django_su',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'nested_inline',
    'django.contrib.admin',
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
    'sorl.thumbnail',
    'crispy_forms',
    'adminfilters',
    'django_bleach',
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
    'bootstrap3',
    'daterange_filter',
    'storages',
    'favicon',
    'adminactions',
    'massadmin',
    'advanced_filters',
    'django_celery_beat',
    'psc',
    # 'cachalot',
)

BASE_WP_URL = "http://www.dopracenakole.cz"

ECC_PROVIDER_CODE = "DK"
ECC_URL_BASE = "http://srv.cycling365.eu/services"

TEMPLATE_VISIBLE_SETTINGS = (
    'PAYU_POS_AUTH_KEY',
    'PAYU_POS_ID',
    'PAYU_KEY_1',
    'BASE_WP_URL',
    'HEADER_COLOR',
    'AKLUB_URL',
    'SITE_URL',
)

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.AllowAny',),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
}

REDACTOR_OPTIONS = {'formatting': ['p', 'blockquote', 'pre', 'h4', 'h5']}
BLEACH_ALLOWED_TAGS = ['p', 'b', 'i', 'u', 'em', 'strong', 'a', 'br', 'span', 'div', 'h4', 'h5', 'pre', 'blockquote', 'ol', 'li', 'ul']
BLEACH_ALLOWED_ATTRIBUTES = ['href', ]

CRISPY_TEMPLATE_PACK = 'bootstrap3'
SERVER_EMAIL = 'kontakt@dopracenakole.cz'
LOGIN_URL = reverse_lazy('login')
LOGIN_REDIRECT_URL = reverse_lazy("profil")
LOGOUT_NEXT_PAGE = reverse_lazy('profil')
DJANGO_URL = ''
SMART_SELECTS_URL_PREFIX = ""
if PRODUCTION_ENVIRONMENT:
    AKLUB_URL = "https://klub.auto-mat.cz"
else:
    AKLUB_URL = "https://devel-klub.auto-mat.cz"

LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (50.0866699218750000, 14.4387817382809995),
    'TILES': [
        (
            _(u'cyklomapa'),
            'http://tiles.prahounakole.cz/{z}/{x}/{y}.png',
            {'attribution': u'&copy; přispěvatelé <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'}),
        (
            _(u'Všeobecná mapa'),
            'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            {'attribution': u'&copy; přispěvatelé <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'}),
    ],
    'DEFAULT_ZOOM': 8,
    'MIN_ZOOM': 8,
    'MAX_ZOOM': 18,
    'SPATIAL_EXTENT': [11.953, 48.517, 19.028, 51.097],
}

ACCESS_CONTROL_ALLOW_ORIGIN = ("http://localhost", )

DBBACKUP_BACKUP_DIRECTORY = normpath(PROJECT_ROOT, 'db_backup')

MAX_COMPETITIONS_PER_COMPANY = 4

MAILING_API_KEY = os.environ.get('DPNK_MAILING_API_KEY', '')

FIO_TOKEN = os.environ.get('DPNK_FIO_TOKEN', '')

PAYU_KEY_1 = os.environ.get('DPNK_PAYU_KEY_1', '')
PAYU_KEY_2 = os.environ.get('DPNK_PAYU_KEY_2', '')
PAYU_POS_AUTH_KEY = os.environ.get('DPNK_PAYU_POS_AUTH_KEY', '')
PAYU_POS_ID = os.environ.get('DPNK_PAYU_POS_ID', '')

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
}

GOOGLE_TAG_ID = os.environ.get('DPNK_GOOGLE_TAG_ID', '')

ALLOWED_HOSTS = os.environ.get('DPNK_ALLOWED_HOSTS', '').split(',')

BROKER_URL = os.environ.get('DPNK_BROKER_URL', '')

MIGRATION_MODULES = {
    'price_level': 'price_level_migrations',
    'thumbnail': 'thumbnail_migrations',
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'danger',
}

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

if PRODUCTION_ENVIRONMENT:
    HEADER_COLOR = "red"
else:
    HEADER_COLOR = "blue"

IGNORABLE_404_URLS = [
    re.compile(r'^/apple-touch-icon.*\.png$'),
    re.compile(r'^/favicon\.ico$'),
    re.compile(r'^/robots\.txt$'),
    re.compile(r'^/wordpress$'),
    re.compile(r'^/wp$'),
    re.compile(r'^/blog$'),
    re.compile(r'^/sitenews$'),
    re.compile(r'^/site$'),
    re.compile(r'^/blog/robots.txt$'),
    re.compile(r'^xmlrpc.php$'),
]

FAVICON_PATH = STATIC_URL + 'img/favicon/favicon.ico'

PRICE_LEVEL_MODEL = 'dpnk.Campaign'
PRICE_LEVEL_CATEGORY_CHOICES = Choices(('basic', _('Základní')), ('company', _('Pro firmy')))
PRICE_LEVEL_CATEGORY_DEFAULT = 'basic'

THUMBNAIL_FORCE_OVERWRITE = True

SITE_URL = 'dopracenakole.cz'
# import local settings
try:
    from settings_local import *  # noqa
except ImportError:
    pass

DATABASE_CONFIGURED = DATABASES['default']['NAME'] != ''
