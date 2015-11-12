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
from django import forms
from dpnk.widgets import WorkingScheduleWidget


class WorkingScheduleField(forms.Field):
    widget = WorkingScheduleWidget

    def clean(self, schedule):
        for trip in self.initial:
            trip.is_working_ride_from = schedule.get((trip.date, 'from')) == 'on'
            trip.is_working_ride_to = schedule.get((trip.date, 'to')) == 'on'
        return self.initial


class ShowPointsMultipleModelChoiceField(forms.ModelMultipleChoiceField):
    show_points = False

    def label_from_instance(self, obj):
        if self.show_points:
            return u"%s (%s b)" % (obj.text, obj.points)
        else:
            return u"%s" % (obj.text)
