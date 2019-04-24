# -*- coding: utf-8 -*-

# Author: Hynek Hanke <hynek.hanke@auto-mat.cz>
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2016 o.s. Auto*Mat
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
from datetime import timedelta

from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _

from .. import util

TYPE = [
    ('registration', _("registrační")),
    ('payment', _("placení startovného")),
    ('competition', _("soutěžní")),
    ('entry_enabled', _("zápis jízd umožněn")),
    ('results', _("výsledková")),
    ('admissions', _("přihlašovací do soutěží")),
    ('invoices', _("vytváření faktur")),
]
PHASE_TYPE_DICT = dict(TYPE)


class Phase(models.Model):
    """fáze kampaně"""

    class Meta:
        verbose_name = _(u"fáze kampaně")
        verbose_name_plural = _(u"fáze kampaně")
        unique_together = (("phase_type", "campaign"),)

    campaign = models.ForeignKey(
        'Campaign',
        verbose_name=_(u"Kampaň"),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    phase_type = models.CharField(
        verbose_name=_(u"Typ fáze"),
        choices=TYPE,
        max_length=16,
        null=False,
        default='registration',
    )
    date_from = models.DateField(
        verbose_name=_(u"Datum začátku fáze"),
        default=None,
        null=True,
        blank=True,
    )
    date_to = models.DateField(
        verbose_name=_(u"Datum konce fáze"),
        default=None,
        null=True,
        blank=True,
    )

    @classmethod
    def get_active(cls, when=None):
        if when is None:
            when = util.today()
        return cls.objects.filter(date_from__lte=when, date_to__gte=when)

    @staticmethod
    def get_active_range(phase_type, when=None):
        """
        Returns the earliest active day of the earliest starting active phase of a given type,
        and last active day of the latest ending active phase of the given type.
        """
        if when is None:
            when = util.today()
        earliest_start_date = when  # Earliest date from all competions
        for phase in Phase.get_active(when=when).filter(phase_type=phase_type):
            if phase.get_earliest_active_day() < earliest_start_date:
                earliest_start_date = phase.get_earliest_active_day()
        return earliest_start_date, util.today()

    def get_earliest_active_day(self):
        if util.today() - self.date_from <= timedelta(self.campaign.days_active):
            return self.date_from
        else:
            return util.today() - timedelta(days=self.campaign.days_active)

    def get_minimum_rides_base(self):
        return self.campaign.minimum_rides_base

    def day_before_start(self, day):
        if not self.date_from:
            return False
        return self.date_from > day

    def day_after_end(self, day):
        if not self.date_to:
            return False
        return self.date_to < day

    def has_started(self):
        return not self.day_before_start(util.today())

    def has_finished(self):
        return self.day_after_end(util.today())

    def day_in_phase(self, day):
        return (not self.day_before_start(day)) and (not self.day_after_end(day))

    def is_actual(self):
        return self.day_in_phase(util.today())

    def __str__(self):
        return "%s" % self.phase_type
