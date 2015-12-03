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
import sys
from django.core.urlresolvers import reverse_lazy
from django.contrib.messages import constants as message_constants
from django.utils.translation import ugettext_lazy as _


def normpath(*args):
    return os.path.normpath(os.path.abspath(os.path.join(*args)))

PROJECT_ROOT = normpath(__file__, "..", "..")

sys.path.append(normpath(PROJECT_ROOT, "project"))
sys.path.append(normpath(PROJECT_ROOT, "apps"))

DEBUG = False
ADMINS = (
    ('Hynek Hanke', 'hynek.hanke@auto-mat.cz'),
    ('Petr Dlouhý', 'petr.dlouhy@email.cz'),
)
DEFAULT_FROM_EMAIL = 'Do práce na kole <kontakt@dopracenakole.net>'
MANAGERS = ADMINS
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '',
        'OPTIONS': {'init_command': 'SET storage_engine=INNODB,character_set_connection=utf8,collation_connection=utf8_unicode_ci'}
    },
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
CACHE_BACKEND = 'memcached://127.0.0.1:11211/'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'KEY_PREFIX': 'dpnkch',
    },
}

LOCALE_PATHS = (normpath(PROJECT_ROOT, 'apps/dpnk/locale'),)
TIME_ZONE = 'Europe/Prague'
LANGUAGES = (
    ('cs', _('Czech')),
    ('en', _('English')),
)
LANGUAGE_CODE = 'cs'
PREFIX_DEFAULT_LOCALE = False
SITE_ID = 1
USE_I18N = True
USE_L10N = True
MEDIA_ROOT = normpath(PROJECT_ROOT, 'media/upload')
MEDIA_URL = '/media/upload/'
STATIC_ROOT = normpath(PROJECT_ROOT, "static")
STATIC_URL = '/static/'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)
SECRET_KEY = ''
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'subdomains.middleware.SubdomainMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'denorm.middleware.DenormMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'author.middlewares.AuthorDefaultBackendMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
)
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.messages.context_processors.messages',
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    'django.core.context_processors.debug',
    'dpnk.context_processors.site',
    'dpnk.context_processors.user_attendance',
    "dpnk.context_processors.settings_properties",
    'settings_context_processor.context_processors.settings',
)
AUTHENTICATION_BACKENDS = (
    'oauth2_provider.backends.OAuth2Backend',
    'dpnk.auth.EmailModelBackend',
    "django_su.backends.SuBackend",
)
ROOT_URLCONF = 'urls'
TEMPLATE_DIRS = (
    normpath(PROJECT_ROOT, 'templates'),
    normpath(PROJECT_ROOT, 'apps/dpnk/templates'),
)
INSTALLED_APPS = (
    'django_su',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'nested_inlines',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.gis',
    'django.contrib.sites',

    'registration',
    'dpnk',
    'smart_selects',
    'composite_field',
    'admin_enhancer',
    'softhyphen',
    'debug_toolbar',
    'django_extensions',
    'chart_tools',
    'massadmin',
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
    'compressor',
    'django_bleach',
    'analytical',
    'leaflet',
    'settings_context_processor',
    'oauth2_provider',
    'rest_framework',
    'bulk_update',
    'denorm',
    'subdomains',
    # 'cachalot',
)
TEMPLATE_VISIBLE_SETTINGS = (
    'PAYU_POS_AUTH_KEY',
    'PAYU_POS_ID',
    'PAYU_KEY_1',
)

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
}

BLEACH_ALLOWED_TAGS = ['p', 'b', 'i', 'u', 'em', 'strong', 'a', 'br']
COMPRESSOR_ENABLED = True
COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
)

CRISPY_TEMPLATE_PACK = 'bootstrap3'
SERVER_EMAIL = 'root@auto-mat.cz'
LOGIN_URL = reverse_lazy('login')
LOGIN_REDIRECT_URL = reverse_lazy("profil")
LOGOUT_NEXT_PAGE = reverse_lazy('profil')
SITE_URL = ''
DJANGO_URL = ''
SMART_SELECTS_URL_PREFIX = "http://localhost:8000"
AKLUB_URL = "http://klub.vnitrni.auto-mat.cz"

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
MAX_TEAM_MEMBERS = 5

MAILING_API_KEY = ''

PAYU_KEY_1 = ''
PAYU_KEY_2 = ''
PAYU_POS_AUTH_KEY = 'NxFcSXh'
PAYU_POS_ID = "131116"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'plain': {
            'format': '%(asctime)s %(message)s'},
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "/var/log/django/dpnk.log",
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
    'loggers': {
        'django': {
            'handlers': ['console', 'logfile'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['mail_admins', 'logfile'],
            'level': 'ERROR',
            'propagate': False,
        },
        'dpnk': {
            'handlers': ['console', 'mail_admins', 'logfile'],
            'level': 'INFO',
        },
    }
}

MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'danger',
}

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# import local settings
try:
    from settings_local import *  # noqa
except ImportError:
    pass
