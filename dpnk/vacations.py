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
    vid = 1
    for trip in trips:
        if this_day and trip.date <= (this_day + datetime.timedelta(days=1)):
            current_vacation["end"] = trip.date + datetime.timedelta(days=1)
        else:
            if current_vacation:
                vacations.append(current_vacation)
            current_vacation = {
                "date": trip.date,
                "end": trip.date + datetime.timedelta(days=1),
                "editable": trip.date in possible_vacation_days,
            }
            if current_vacation["editable"]:
                current_vacation["id"] = vid
                vid += 1
        this_day = trip.date
    if current_vacation:
        vacations.append(current_vacation)
    return vacations, vid


def get_events(request):
    events = []

    def add_event(title, date, end=None, commute_mode=None, order=0, url=None, eid=None):
        event = {
            "title": title,
            "start": str(date),
            "order": order,
            "editable": False,
            "allDay": True,
            "commute_mode": commute_mode,
        }
        if end:
            event["end"] = str(end)
        else:
            event["end"] = str(date + datetime.timedelta(days=1))
        if url:
            event['url'] = url
        if id:
            event['id'] = eid
        events.append(event)

    phase = request.campaign.phase("competition")
    add_event("Začatek soutěže", phase.date_from)
    add_event("Konec soutěže", phase.date_to)
    trips = request.user_attendance.user_trips.filter(
        commute_mode__slug__in=('by_foot', 'bicycle'),
    )
    for trip in trips:
        distance = str(trip.distance)
        if trip.direction == 'trip_to':
            title = " " + _("Do práce") + " " + distance + " km"
            order = 1
            commute_mode = trip.commute_mode.slug
        if trip.direction == 'trip_from':
            title = " " + _("Domů") + " " + distance + " km"
            order = 2
            commute_mode = trip.commute_mode.slug
        add_event(
            title,
            trip.date,
            order=order,
            commute_mode=commute_mode,
            url=reverse('trip', kwargs={'date': trip.date, 'direction': trip.direction}),
        )
    for vacation in get_vacations(request.user_attendance)[0]:
        add_event(
            _('Dovolená'),
            vacation["date"],
            end=vacation["end"],
            eid=vacation.get("id", None),
        )
    add_event(_('Dnes'), util.today())
    return events
