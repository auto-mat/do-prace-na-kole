# -*- coding: utf-8 -*-

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

from .settings import *  # noqa
from .settings import INSTALLED_APPS, LOGGING, MIDDLEWARE_CLASSES, TEMPLATES

ADMINS = (
    ('', ''),
)
DEBUG = True
DEFAULT_FROM_EMAIL = 'Do práce na kole <kontakt@test.cz>'
SERVER_EMAIL = 'Do práce na kole <kontakt@tests.cz>'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('DPNK_DB_NAME', 'circle_test'),
        'USER': os.environ.get('DPNK_DB_USER', 'ubuntu'),
        'PASSWORD': os.environ.get('DPNK_DB_PASSWORD', ''),
        'HOST': os.environ.get('DPNK_DB_HOST', 'localhost'),
        'PORT': os.environ.get('DPNK_DB_PORT', ''),
    },
}

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

UNUSED_MIDDLEWARES = [
    'django.middleware.locale.LocaleMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

INSTALLED_APPS += (
    'django_nose',
)

for mid in UNUSED_MIDDLEWARES:
    try:
        MIDDLEWARE_CLASSES.remove(mid)
    except ValueError:
        pass

SMART_SELECTS_URL_PREFIX = "http://localhost:8000"  # XXX
SITE_URL = 'localhost:8000'
DJANGO_URL = 'http://localhost:8000'

ACCESS_CONTROL_ALLOW_ORIGIN = ("http://localhost", )

SECRET_KEY = 'bt@kl##och59s((u!88iny_c^4p#en@o28w3g57$ys-sgw$4$5'


class InvalidStringError(str):
    def __mod__(self, other):
        raise Exception("empty string %s" % other)
        return ""


ALLOWED_HOSTS = ['testing-campaign.testserver', 'testing-campaign-unknown.testserver']

TEMPLATES[0]['OPTIONS']['string_if_invalid'] = InvalidStringError("%s")
TEMPLATES[0]['OPTIONS']['debug'] = True

LOGGING['handlers']['logfile']['filename'] = "test-dpnk.log"

CRISPY_FAIL_SILENTLY = False

# import local test_settings
try:
    from test_settings_local import *  # noqa
except ImportError:
    pass
