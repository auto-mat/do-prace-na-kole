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
from author.decorators import with_author

from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext_lazy as _


@with_author
class PSC(models.Model):
    class Meta:
        verbose_name = _("Poštovní směrovací číslo")
        verbose_name_plural = _("Poštovní směrovací čísla")

    municipality_name = models.CharField(
        verbose_name=_("Název obce"),
        max_length=255,
    )
    municipality_part_name = models.CharField(
        verbose_name=_("Název části obce"),
        max_length=255,
    )
    district_name = models.CharField(
        verbose_name=_("Název okresu"),
        max_length=255,
    )
    psc = models.IntegerField(
        verbose_name=_("PSČ"),
        help_text=_("Např.: „130 00“"),
        validators=[
            MaxValueValidator(99999),
            MinValueValidator(10000),
        ],
    )
    post_name = models.CharField(
        verbose_name=_("Název pošty"),
        max_length=255,
    )
    code = models.IntegerField(
        verbose_name=_("Kód"),
    )
