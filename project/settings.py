# -*- coding: utf-8 -*-
# Django settings for DPNK project.
import os
import sys
from django.core.urlresolvers import reverse_lazy
from django.contrib.messages import constants as message_constants
from django.utils.translation import ugettext_lazy as _

normpath = lambda *args: os.path.normpath(os.path.abspath(os.path.join(*args)))
PROJECT_ROOT = normpath(__file__, "..", "..")

sys.path.append(normpath(PROJECT_ROOT, "project"))
sys.path.append(normpath(PROJECT_ROOT, "apps"))

DEBUG = True
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

CACHE_BACKEND = 'memcached://127.0.0.1:11211/'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'KEY_PREFIX': 'dpnkch',
    },
}

LOCALE_PATH = normpath(PROJECT_ROOT, 'dpnk/locale')
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
DECIMAL_SEPARATOR = ','
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
    'localeurl.middleware.LocaleURLMiddleware',
    'subdomains.middleware.SubdomainMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'author.middlewares.AuthorDefaultBackendMiddleware',
    'timelog.middleware.TimeLogMiddleware',
    'remote_ajax.middleware.XHRMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
)
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.messages.context_processors.messages',
    'django.contrib.auth.context_processors.auth',
    "dpnk.context_processors.settings_properties",
)
AUTHENTICATION_BACKENDS = (
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
    'timelog',
    'remote_ajax',
    'adminsortable',
    'reportlab',
    'dbbackup',
    'localeurl',
    'related_admin',
    'easy_thumbnails',
    'crispy_forms',
    'adminfilters',
    'compressor',
    'django_bleach',
    'google_analytics',
)

GOOGLE_ANALYTICS_MODEL = True
BLEACH_ALLOWED_TAGS = ['p', 'b', 'i', 'u', 'em', 'strong', 'a']
COMPRESSOR_ENABLED = True

CRISPY_TEMPLATE_PACK = 'bootstrap3'
SERVER_EMAIL = 'root@auto-mat.cz'
LOGIN_URL = reverse_lazy('login')
LOGIN_REDIRECT_URL = reverse_lazy("upravit_profil")
LOGOUT_NEXT_PAGE = reverse_lazy('profil')
SITE_URL = ''
DJANGO_URL = ''
SMART_SELECTS_URL_PREFIX = "http://localhost:8000"
AKLUB_URL = "http://klub.vnitrni.auto-mat.cz"

DEFAULT_MAPWIDGET_LOCATION = lambda: None
DEFAULT_MAPWIDGET_LOCATION.x = 14.4387817382809995
DEFAULT_MAPWIDGET_LOCATION.y = 50.0866699218750000
DEFAULT_MAPWIDGET_ZOOM = 8

ACCESS_CONTROL_ALLOW_ORIGIN = ("http://localhost", )

DBBACKUP_STORAGE = 'dbbackup.storage.filesystem_storage'
DBBACKUP_FILESYSTEM_DIRECTORY = 'db_backup'

MAX_COMPETITIONS_PER_COMPANY = 4
MAX_TEAM_MEMBERS = 5

MAILING_API_KEY = ''

PAYU_KEY_1 = ''
PAYU_KEY_2 = ''

TIMELOG_LOG = '/var/log/django/dpnk-timelog.log'

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
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
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
        'timelog': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': TIMELOG_LOG,
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'plain',
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
        'timelog.middleware': {
            'handlers': ['timelog'],
            'level': 'DEBUG',
            'propogate': False,
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

# import local settings
try:
        from settings_local import *
except ImportError:
        pass
