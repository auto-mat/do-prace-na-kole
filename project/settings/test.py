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

from .base import *  # noqa
from .base import INSTALLED_APPS, LOGGING, MIDDLEWARE, TEMPLATES

ADMINS = (("", ""),)
DEBUG = True
DEFAULT_FROM_EMAIL = "Do práce na kole <kontakt@test.cz>"
SERVER_EMAIL = "Do práce na kole <kontakt@tests.cz>"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
}

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("DPNK_DB_NAME", "circle_test"),
        "USER": os.environ.get("DPNK_DB_USER", "ubuntu"),
        "PASSWORD": os.environ.get("DPNK_DB_PASSWORD", ""),
        "HOST": os.environ.get("DPNK_DB_HOST", "localhost"),
        "PORT": os.environ.get("DPNK_DB_PORT", ""),
        "TEST": {
            "NAME": os.environ.get("DB", "circle_test"),
        },
    },
}

DATABASE_ROUTERS = []

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

UNUSED_MIDDLEWARES = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

INSTALLED_APPS += ("django_nose",)

INSTALLED_APPS.remove("adminactions")

for mid in UNUSED_MIDDLEWARES:
    try:
        MIDDLEWARE.remove(mid)
    except ValueError:
        pass

DJANGO_URL = "http://localhost:8000"

ACCESS_CONTROL_ALLOW_ORIGIN = ("http://localhost",)

SECRET_KEY = "bt@kl##och59s((u!88iny_c^4p#en@o28w3g57$ys-sgw$4$5"


class InvalidStringError(str):
    def __mod__(self, other):
        raise Exception("empty string %s" % other)
        return ""


ALLOWED_HOSTS = [
    ".testserver",
    "example.com",
    ".example.com",
]

TEMPLATES[0]["OPTIONS"]["string_if_invalid"] = InvalidStringError("%s")
TEMPLATES[0]["OPTIONS"]["debug"] = True

LOGGING["handlers"]["logfile"]["filename"] = "test-dpnk.log"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

CRISPY_FAIL_SILENTLY = False

SECURE_SSL_REDIRECT = False


MEDIA_ROOT = normpath(PROJECT_ROOT, "apps/dpnk/test_files/media")

# import local test_settings
try:
    from test_settings_local import *  # noqa
except ImportError:
    pass
