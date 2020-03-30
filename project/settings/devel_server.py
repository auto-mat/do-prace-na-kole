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
from .base import INSTALLED_APPS, MIDDLEWARE

INSTALLED_APPS += (
    'rosetta',
    'livereload',
)

DEBUG_TOOLBAR = os.environ.get('DPNK_DEBUG_TOOLBAR', False)

if DEBUG_TOOLBAR:
    INSTALLED_APPS += (
        'debug_toolbar',
        # 'template_timings_panel',
        "template_profiler_panel",
    )
    MIDDLEWARE += [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
        'project.non_html_debug.NonHtmlDebugToolbarMiddleware',
    ]

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
    "template_profiler_panel.panels.template.TemplateProfilerPanel",
    # 'cachalot.panels.CachalotPanel',
    # 'template_timings_panel.panels.TemplateTimings.TemplateTimings',
]


def custom_show_toolbar(request):
    if request.user and request.user.is_superuser and 'debug_toolbar' in request.GET:
        return True
    return False


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
    # 'EXTRA_SIGNALS': ['myproject.signals.MySignal'],
    'HIDE_DJANGO_SQL': False,
    'TAG': 'div',
}
