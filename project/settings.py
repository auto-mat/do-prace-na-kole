# -*- coding: utf-8 -*-
# Django settings for DPNK project.
import os
import sys

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
                'OPTIONS': { 'init_command': 'SET storage_engine=INNODB,character_set_connection=utf8,collation_connection=utf8_unicode_ci' }
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
LANGUAGE_CODE = 'cs-CZ'
SITE_ID = 5
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
)
SECRET_KEY = ''
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'author.middlewares.AuthorDefaultBackendMiddleware',
    'timelog.middleware.TimeLogMiddleware',
    'remote_ajax.middleware.XHRMiddleware',
	#'django.middleware.csrf.CsrfViewMiddleware',

#    "dpnk.middleware.XHRMiddleware",
)
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
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

    'registration',
    'dpnk',
    'smart_selects',
    'composite_field',
    'south',
    'bootstrapform',
    'admin_enhancer',
    'softhyphen',
    'debug_toolbar',
    'django_extensions',
    'chart_tools',
    'massadmin',
    'import_export',
    'polymorphic',
    'django.contrib.contenttypes',
    'author',
    'fieldsignals',
    'timelog',
    'remote_ajax',
    'adminsortable',
    'reportlab',
)
AUTH_PROFILE_MODULE = 'dpnk.UserProfile'
SERVER_EMAIL='root@auto-mat.cz'
LOGIN_URL = '/dpnk/login/'
LOGIN_REDIRECT_VIEW = 'profil'
LOGOUT_NEXT_PAGE = '/dpnk/logout_redirect'
LOGOUT_REDIRECT_URL = '/'
SITE_URL = ''
DJANGO_URL = ''
SMART_SELECTS_URL_PREFIX = "http://localhost:8000"  #XXX

ACCESS_CONTROL_ALLOW_ORIGIN = ("http://localhost", )

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
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'logfile': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': "/var/log/django/dpnk.log",
            'backupCount': 50,
            'maxBytes': 10000000,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
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


# import local settings
try:
        from settings_dev_local import *
except ImportError:
        pass
