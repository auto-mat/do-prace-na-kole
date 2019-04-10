# -*- coding: utf-8 -*-
# Author: Timothy Hobbs <timothy.hobbs@auto-mat.cz>
#
# Copyright (C) 2012 o.s. Auto*Mat
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

# Standard library imports

import datetime

from django.contrib.humanize.templatetags.humanize import intcomma
from django.urls import reverse
from django.utils.translation import ugettext as _

# Local imports
from . import util

def get_events(request):
    events = []

    def add_event(title, date, end=None, css_class=None, extra_attrs=None):
        event = {
            "title": title,
            "start": str(date),
            "allDay": True,
            "className": css_class,
        }
        if end:
            event["end"] = str(end)
        else:
            event["end"] = str(date + datetime.timedelta(days=1))
        if extra_attrs:
            event.update(extra_attrs)
        events.append(event)

    phase = request.campaign.phase("competition")
    add_event(_("Začatek soutěže"), phase.date_from, css_class="cal-competition-beginning")
    add_event(_("Konec soutěže"), phase.date_to, css_class="cal-competition-end")
    return events
