# -*- coding: utf-8 -*-
from django import forms
from dpnk.widgets import WorkingScheduleWidget
import util
from models import Trip

class WorkingScheduleField(forms.Field):
    widget = WorkingScheduleWidget

    def clean(self, schedule):
        for trip in self.initial:
            trip.is_working_ride_from = schedule.get((trip.date, 'from')) == 'on'
            trip.is_working_ride_to = schedule.get((trip.date, 'to')) == 'on'
        return self.initial
