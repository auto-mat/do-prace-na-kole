# -*- coding: utf-8 -*-
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
