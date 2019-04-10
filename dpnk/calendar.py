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


def get_vacations(user_attendance):
    trips = user_attendance.user_trips.filter(
        commute_mode__slug='no_work',
    ).order_by('date')
    vacations = []
    this_day = None
    current_vacation = None
    possible_vacation_days = user_attendance.campaign.possible_vacation_days()
    for trip in trips:
        if (this_day and trip.date <= (this_day + datetime.timedelta(days=1)) and
                (current_vacation["editable"] or trip.date not in possible_vacation_days)):
            current_vacation["end"] = trip.date + datetime.timedelta(days=1)
        else:
            if current_vacation:
                vacations.append(current_vacation)
            current_vacation = {
                "title": str(trip.get_commute_mode_display()),
                "date": trip.date,
                "end": trip.date + datetime.timedelta(days=1),
                "editable": trip.date in possible_vacation_days,
            }
            if current_vacation["editable"]:
                current_vacation["vacation"] = True
        this_day = trip.date
    if current_vacation:
        vacations.append(current_vacation)
    return vacations


def get_order(direction):
    return 2 if direction == 'trip_from' else 1


def get_events(request):
    events = []

    def add_event(title, date, end=None, commute_mode=None, direction=None, order=0, url=None, css_class=None, extra_attrs=None):
        event = {
            "title": title,
            "start": str(date),
            "order": order,
            "editable": False,
            "allDay": True,
            "direction": direction,
            "className": css_class,
        }
        if commute_mode:
            event.update({
                "commute_mode": commute_mode.slug,
                "commute_mode__eco": commute_mode.eco,
            })
        if end:
            event["end"] = str(end)
        else:
            event["end"] = str(date + datetime.timedelta(days=1))
        if url:
            event['url'] = url
        if extra_attrs:
            event.update(extra_attrs)
        events.append(event)

    phase = request.campaign.phase("competition")
    add_event(_("Začatek soutěže"), phase.date_from, css_class="vc-competition-beginning")
    add_event(_("Konec soutěže"), phase.date_to, css_class="vc-competition-end")
    trips = request.user_attendance.user_trips.filter(
        commute_mode__eco=True,
        commute_mode__does_count=True,
    )
    placeholders = {}
    for day in util.days_active(phase):
        placeholders[day] = {
            "trip_to": True,
            "trip_from": True,
        }
    for trip in trips:
        if trip.distance:
            distance = intcomma(round(trip.distance, 1))
            title = distance + " km"
        else:
            title = ""
        commute_mode = trip.commute_mode
        try:
            placeholders[trip.date][trip.direction] = False
        except KeyError:
            pass
        order = get_order(trip.direction)
        add_event(
            title,
            trip.date,
            order=order,
            commute_mode=commute_mode,
            direction=trip.direction,
            css_class="vc-" + trip.direction.replace("_", "-"),
            extra_attrs={"modal_url": reverse('trip', kwargs={'date': trip.date, 'direction': trip.direction})}
        )
    for date, dirs in placeholders.items():
        for d, v in dirs.items():
            add_event(
                "+",
                date,
                order=get_order(d),
                direction=d,
                extra_attrs={"placeholder":True}
        )

    for vacation in get_vacations(request.user_attendance):
        add_event(
            vacation.pop("title"),
            vacation["date"],
            end=vacation.pop("end"),
            css_class='no-trip' if vacation.pop('date') <= util.today() else 'vc-vacation',
            extra_attrs=vacation,
        )
    return events
