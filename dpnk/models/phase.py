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

from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _

from .. import util

TYPE = [
    ('registration', _(u"registrační")),
    ('payment', _(u"placení startovného")),
    ('competition', _(u"soutěžní")),
    ('results', _(u"výsledková")),
    ('admissions', _(u"přihlašovací do soutěží")),
    ('invoices', _(u"vytváření faktur")),
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

    def get_minimum_rides_base(self):
        return self.campaign.minimum_rides_base

    def has_started(self):
        if not self.date_from:
            return True
        return self.date_from <= util.today()

    def has_finished(self):
        if not self.date_to:
            return False
        return not self.date_to >= util.today()

    def is_actual(self):
        return self.has_started() and not self.has_finished()

    def __str__(self):
        return "%s" % self.phase_type
