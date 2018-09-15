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
from .settings import CORS_ORIGIN_REGEX, INSTALLED_APPS, LOGGING, MIDDLEWARE, PROJECT_ROOT, STATIC_URL, TEMPLATES, normpath

ADMINS = (
    ('', ''),
)
DEBUG = True
DEFAULT_FROM_EMAIL = 'Do práce na kole <contact@example.com>'
SERVER_EMAIL = 'Do práce na kole <contact@example.com>'

db_name = os.environ.get('DPNK_DB_NAME', 'dpnk')
db_user = os.environ.get('DPNK_DB_USER', 'dpnk')
db_password = os.environ.get('DPNK_DB_PASSWORD', '')
db_host = os.environ.get('DPNK_DB_HOST', 'localhost')
db_port = os.environ.get('DPNK_DB_PORT', '')

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': db_name,
        'USER': db_user,
        'PASSWORD': db_password,
        'HOST': db_host,
        'PORT': db_port,
        'CONN_MAX_AGE': 0,
    },
}

CELERY_RESULT_BACKEND = "db+postgresql://{user}:{password}@{host}/{db_name}".format(
    user=db_user,
    password=db_password,
    host=db_host,
    db_name=db_name,
)

INSTALLED_APPS += (
    'rosetta',
    'debug_toolbar',
    'debug_toolbar_line_profiler',
    'template_timings_panel',
)

CELERY_EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_FILE_PATH = '/tmp/dpnk-emails'

SITE_URL = 'localhost:8000'
DJANGO_URL = 'http://localhost:8000'

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

ALLOWED_HOSTS = [
    'localhost',
    '.localhost',
    '127.0.0.1',
    '.testserver',
    'example.com',
    '.example.com',
    '.dopracenakole.cz',
    '.lvh.me',
]

CORS_ORIGIN_REGEX += [
    r'^(https?://)?(\w+\.)?localhost$',
    r'^(https?://)?(\w+\.)?lvh.me$',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'project.non_html_debug.NonHtmlDebugToolbarMiddleware',
]

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TEMPLATE_CONTEXT': True,
    'JQUERY_URL': STATIC_URL + "bow/jquery/dist/jquery.js",
    'SHOW_TOOLBAR_CALLBACK': 'project.settings_local.custom_show_toolbar',
}

DEBUG_TOOLBAR_PANELS = [
    'ddt_request_history.panels.request_history.RequestHistoryPanel',
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
    'debug_toolbar.panels.profiling.ProfilingPanel',
    'debug_toolbar_line_profiler.panel.ProfilingPanel',
    # 'cachalot.panels.CachalotPanel',
    'template_timings_panel.panels.TemplateTimings.TemplateTimings',
]


def custom_show_toolbar(request):
    return True  # Always show toolbar, for example purposes only.


DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
    # 'EXTRA_SIGNALS': ['myproject.signals.MySignal'],
    'HIDE_DJANGO_SQL': False,
    'TAG': 'div',
}

TEMPLATES[0]['OPTIONS']['debug'] = True
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.filesystem.Loader'),
    ('django.template.loaders.app_directories.Loader'),
]

MEDIA_ROOT = normpath(PROJECT_ROOT, 'media/upload')
MEDIA_URL = '/media/upload/'

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
