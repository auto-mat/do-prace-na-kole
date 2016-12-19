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

from composite_field import CompositeField

from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext_lazy as _

from .. import util


def get_address_string(address):
    return ", ".join(filter(lambda x: x != "", [address.recipient, "%s %s" % (address.street, address.street_number), "%s %s" % (util.format_psc(address.psc), address.city)]))


class Address(CompositeField):
    street = models.CharField(
        verbose_name=_(u"Ulice"),
        help_text=_(u"Např. „Šeříková“ nebo „Nám. W. Churchilla“"),
        default="",
        max_length=50,
        null=False,
    )
    street_number = models.CharField(
        verbose_name=_(u"Číslo domu"),
        help_text=_(u"Např. „2965/12“ nebo „156“"),
        default="",
        max_length=10,
        null=False,
        blank=False,
    )
    recipient = models.CharField(
        verbose_name=_(u"Název pobočky (celé organizace, závodu, kanceláře, fakulty) na adrese"),
        help_text=_(u"Např. „odštěpný závod Brno“, „oblastní pobočka Liberec“, „Přírodovědecká fakulta“ atp."),
        default="",
        max_length=50,
        null=True,
        blank=True,
    )
    district = models.CharField(
        verbose_name=_(u"Městská část"),
        default="",
        max_length=50,
        null=True,
        blank=True,
    )
    psc = models.IntegerField(
        verbose_name=_(u"PSČ"),
        help_text=_(u"Např.: „130 00“"),
        validators=[
            MaxValueValidator(99999),
            MinValueValidator(10000),
        ],
        default=None,
        null=True,
        blank=False,
    )
    city = models.CharField(
        verbose_name=_(u"Město"),
        help_text=_(u"Např. „Jablonec n. N.“ nebo „Praha 3, Žižkov“"),
        default="",
        max_length=50,
        null=False,
        blank=False,
    )

    def __str__(self):
        return get_address_string(self)
