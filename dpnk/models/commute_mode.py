# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2017 Auto*Mat z.s.
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


class CommuteMode(models.Model):
    class Meta:
        verbose_name = _("Mód dopravy")
        verbose_name_plural = _("Módy dopravy")
        ordering = ["order"]

    name = models.CharField(
        verbose_name=_("Název módu dopravy"),
        max_length=160,
        unique=False,
        null=False,
    )
    slug = models.SlugField(
        verbose_name=_("Identifikátor"),
        unique=True,
        null=False,
        max_length=20,
    )
    order = models.IntegerField(
        verbose_name=_("Pořadí"),
        null=True,
        blank=True,
    )
    tooltip = models.TextField(
        verbose_name=_("Vysvětlivka módu"),
        default=None,
        blank=False,
        null=False,
    )
    button_html = models.TextField(
        verbose_name=_("Html of selector buttons"),
        default="",
        null=False,
    )
    icon_html = models.TextField(
        verbose_name=_("Html of summary icon"),
        default="",
        null=False,
    )
    add_command = models.TextField(
        verbose_name=_("Tooltip command for adding trip."),
        help_text=_("Use {{distance}} to insert distance and {{direction}} for direction."),
        default="",
        null=False,
    )
    choice_description = models.TextField(
        verbose_name=_("Vysvětlivka výběru módu"),
        help_text=_("Use {{distance}} to insert distance."),
        default=None,
        blank=True,
        null=True,
    )
    does_count = models.BooleanField(
        verbose_name=_("Počítá se"),
        help_text=_("Počítá se jako jízda do práce/z práce."),
        default=True,
        null=False,
    )
    # The difference between eco and does_count is that
    # does_count is also set for car trips and other
    # non-ecological modes of transportation.
    # does_count is not set only for the commute mode
    # "No trip".
    eco = models.BooleanField(
        verbose_name=_("Ekologický"),
        default=True,
    )

    def __str__(self):
        return self.name
