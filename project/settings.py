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
LOCALE_PATH = normpath(PROJECT_ROOT, 'dpnk/locale')
TIME_ZONE = 'Europe/Prague'
LANGUAGE_CODE = 'cs-CZ'
SITE_ID = 5
USE_I18N = True
USE_L10N = True
DECIMAL_SEPARATOR = ','
MEDIA_ROOT = normpath(PROJECT_ROOT, 'static/upload')
MEDIA_URL = '/upload/'
STATIC_ROOT = normpath(PROJECT_ROOT, "static/static")
STATIC_URL = '/media/'  # XXX: possible depences, rename static
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
	#'django.middleware.csrf.CsrfViewMiddleware',

#    "dpnk.middleware.XHRMiddleware",
)
ROOT_URLCONF = 'urls'
TEMPLATE_DIRS = (
    normpath(PROJECT_ROOT, 'templates'),
    normpath(PROJECT_ROOT, 'apps/dpnk/templates'),
)
INSTALLED_APPS = (
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
)
AUTH_PROFILE_MODULE = 'dpnk.UserProfile'
SERVER_EMAIL='root@auto-mat.cz'
LOGIN_URL = '/django/dpnk/login/'
LOGIN_REDIRECT_URL = ''
LOGOUT_NEXT_PAGE = '/django/dpnk/profil/'
SITE_URL = ''
DJANGO_URL = ''
SMART_SELECTS_URL_PREFIX = "http://localhost:8000"  #XXX
COMPETITION_STATE='not_started_yet'
#COMPETITION_STATE='started'

INSTALLED_APPS += ("remote_ajax", )
MIDDLEWARE_CLASSES += ("remote_ajax.middleware.XHRMiddleware", )
ACCESS_CONTROL_ALLOW_ORIGIN = ("http://localhost", )

MAILING_API_KEY = ''
MAILING_LIST_ID = ''

PAYU_KEY_1 = ''
PAYU_KEY_2 = ''

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
            'maxBytes': 50000,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'dpnk': {
            'handlers': ['console', 'mail_admins', 'logfile'],
            'level': 'INFO',
        }
    }
}
