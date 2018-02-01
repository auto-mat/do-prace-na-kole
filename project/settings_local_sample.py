# -*- coding: utf-8 -*-
# import datetime

from settings import *  # noqa
from settings import INSTALLED_APPS, LOGGING, MIDDLEWARE, TEMPLATES

ADMINS = (
    ('Your name', 'your.name@email.com'),
)
DEBUG = True
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
DEFAULT_FROM_EMAIL = 'Do práce na kole <your.name@email.com>'
SERVER_EMAIL = 'Do práce na kole <your.name@email.com>'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'dpnk',
        'USER': 'dpnk',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '',
    },
}

INSTALLED_APPS += (
    'rosetta',
    'debug_toolbar',
    'template_timings_panel',
)


MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'project.non_html_debug.NonHtmlDebugToolbarMiddleware',
]

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/dpnk-emails'

TEMPLATES[0]["OPTIONS"]["loaders"] = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
TEMPLATES[0]["OPTIONS"]["debug"] = True

AKLUB_URL = "http://localhost:8001"

ALLOWED_HOSTS = [
    '127.0.0.1',
    '.localhost',
    '.dopracenakole.cz',
]


SECRET_KEY = 'CHANGE_ME'

LOGGING['handlers']['logfile']['filename'] = "dpnk.log"

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]


def custom_show_toolbar(request):
    if request.META['SERVER_NAME'] != 'testserver':
        return True  # Always show toolbar, for example purposes only.


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TEMPLATE_CONTEXT': True,
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TOOLBAR_CALLBACK': 'project.settings_local.custom_show_toolbar',
    'HIDE_DJANGO_SQL': False,
    'TAG': 'div',
}

MAILING_API_KEY = ''

PAYU_KEY_1 = ''
PAYU_KEY_2 = ''
PAYU_POS_AUTH_KEY = ''
PAYU_POS_ID = ''
HEADER_COLOR = "#000000"
# FAKE_DATE = datetime.date(year=2017, month=5, day=5)

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = False

GOOGLE_TAG_ID = ""

FIO_TOKEN = ''
