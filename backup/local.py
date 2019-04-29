# -*- coding: utf-8 -*-

from .dev import *  # noqa
from .dev import LOGGING, PROJECT_ROOT, TEMPLATES, normpath

ADMINS = (
          ('Petr Dlouhý', 'petr.dlouhy@email.cz'),
          )
DEBUG=True
DEFAULT_FROM_EMAIL = 'Test Do práce na kole <test-kontakt@dopracenakole.cz>'
SERVER_EMAIL = 'Test Do práce na kole <test-kontakt@dopracenakole.cz>'

DATABASES = {
        'default': {
                'ENGINE': 'django.contrib.gis.db.backends.postgis',
                'NAME': 'dpnk_test2016',
                'USER': 'dpnk',
                'PASSWORD': 'bezklobouku2014',
                'HOST': 'localhost',
                'PORT': '',
        },
}

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/dpnk-emails'

TESTING_URLS = False

ALLOWED_HOSTS = (".dopracenakole.cz", )

LOGOUT_NEXT_PAGE = '/django/dpnk/logout_redirect'

SECRET_KEY = 'bt@kl##och59s((u!88iny_c^4p#en@o28w3g57$ys-sgw$4$5'

SITE_URL = 'http://test2015.dopracenakole.cz'
DJANGO_URL = 'http://test2015.dopracenakole.cz/django'

ACCESS_CONTROL_ALLOW_ORIGIN = ("http://test2015.dopracenakole.cz", )
SMART_SELECTS_URL_PREFIX = "http://test2015.dopracenakole.cz:8124"

MAILING_API_KEY = 'd102fef1dd00b3c952d46550b70ab93d'

##def custom_show_toolbar(request):
#    return True # Always show toolbar, for example purposes only.
#
#DEBUG_TOOLBAR_CONFIG = {
#    'INTERCEPT_REDIRECTS': False,
#    'SHOW_TOOLBAR_CALLBACK': 'project.settings_local.custom_show_toolbar',
#    #'EXTRA_SIGNALS': ['myproject.signals.MySignal'],
#    'HIDE_DJANGO_SQL': False,
#    'TAG': 'div',
#}


PAYU_KEY_1 = 'eac82603809d388f6a2b8b11471f1805'
PAYU_KEY_2 = 'c2b52884c3816d209ea6c5e7cd917abb'

DEBUG_TOOLBAR_PATCH_SETTINGS = False

HEADER_COLOR = "gray"

# CACHES['default']['KEY_PREFIX'] = 'dpnkch-devel'

import datetime
# FAKE_DATE=datetime.date(year=2016, month=5, day=15)


SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
