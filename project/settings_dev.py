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

from settings import *  # noqa
from settings import LOGGING

ADMINS = (
    ('', ''),
)
DEBUG = True
DEFAULT_FROM_EMAIL = 'Do práce na kole <>'
SERVER_EMAIL = 'Do práce na kole <>'

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

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/dpnk-emails'

SMART_SELECTS_URL_PREFIX = "http://localhost:8000"  # XXX
SITE_URL = 'http://localhost/~petr/dpnk-wp/'
DJANGO_URL = 'http://localhost:8000'
TESTING_URLS = True

ACCESS_CONTROL_ALLOW_ORIGIN = ("http://localhost", )

LOGIN_URL = '/dpnk/login/'
LOGOUT_NEXT_PAGE = '/dpnk/profil_pristup/'

SECRET_KEY = 'bt@kl##och59s((u!88iny_c^4p#en@o28w3g57$ys-sgw$4$5'

LOGGING['handlers']['logfile']['filename'] = "dpnk.log"

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.profiling.ProfilingDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
)


def custom_show_toolbar(request):
    return True  # Always show toolbar, for example purposes only.


DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
    # 'EXTRA_SIGNALS': ['myproject.signals.MySignal'],
    'HIDE_DJANGO_SQL': False,
    'TAG': 'div',
}
