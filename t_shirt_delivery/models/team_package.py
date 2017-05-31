# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2017 o.s. Auto*Mat
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
from django.utils.translation import ugettext as _

from model_utils.models import TimeStampedModel


class TeamPackage(TimeStampedModel, models.Model):
    """ Balíček pro tým """

    class Meta:
        verbose_name = _("týmový balíček")
        verbose_name_plural = _("týmové balíčky")

    box = models.ForeignKey(
        'SubsidiaryBox',
        verbose_name=_("Krabice"),
        null=False,
        blank=False,
    )
    team = models.ForeignKey(
        'dpnk.Team',
        verbose_name=_("Tým"),
        null=True,
        blank=True,
    )
    dispatched = models.BooleanField(
        verbose_name=_("Balíek vyřízen"),
        blank=False,
        null=False,
        default=False,
    )

    def identifier(self):
        if self.id:
            return "T%s" % self.id
    identifier.admin_order_field = 'id'

    def __str__(self):
        if self.team:
            return _("Balíček pro tým %s") % self.team.name
        else:
            return _("Balíček bez týmu")
