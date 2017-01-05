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

from .address import Address, get_address_string
from .city import City
from .company import Company


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super(ActiveManager, self).get_queryset().filter(active=True)


class Subsidiary(models.Model):
    """Pobočka"""

    class Meta:
        verbose_name = _(u"Pobočka organizace")
        verbose_name_plural = _(u"Pobočky organizací")

    address = Address()
    company = models.ForeignKey(
        Company,
        related_name="subsidiaries",
        null=False,
        blank=False,
    )
    city = models.ForeignKey(
        City,
        verbose_name=_(u"Spádové město"),
        help_text=_(
            "Rozhoduje o tom, do soutěží jakého města budete zařazeni"
            "a kde budete dostávat ceny - vizte "
            "<a href='%s' target='_blank'>pravidla soutěže</a>"
        ) % "http://www.dopracenakole.cz/pravidla",
        null=False,
        blank=False,
    )
    active = models.BooleanField(
        verbose_name=_(u"Aktivní"),
        default=True,
        null=False,
    )

    active_objects = ActiveManager()
    objects = models.Manager()

    def __str__(self):
        return "%s - %s" % (get_address_string(self.address), self.city)

    def name(self):
        return get_address_string(self.address)
