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
#    ('Vaclav Rehak', 'vrehak@baf.cz'),
#    ('Petr Studený', 'petr.studeny@auto-mat.cz'),
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
    'django.contrib.admin',
    'django.contrib.staticfiles',

    'registration',
    'dpnk',
    'smart_selects',
    'composite_field',
    'south',
    'bootstrapform',
)
AUTH_PROFILE_MODULE = 'dpnk.UserProfile'
SERVER_EMAIL='root@auto-mat.cz'
LOGIN_URL = '/dpnk/login'
LOGIN_REDIRECT_URL = '/dpnk/profil/'
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
