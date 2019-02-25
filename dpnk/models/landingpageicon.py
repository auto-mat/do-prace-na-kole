# -*- coding: utf-8 -*-
# Copyright (C) 2019 o.s. Auto*Mat
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


class LandingPageIcon(models.Model):
    file = models.FileField(
        verbose_name=_(u"Landing page image"),
        max_length=512,
    )
    ROLES = [
        ('main', _(u"Hlavní obráz"))
    ]
    role = models.CharField(
        verbose_name=_(u"Role pro obráz"),
        max_length=64,
        choices=ROLES,
        blank=False,
    )
    min_frequency = models.FloatField(
        verbose_name=_("Min pravidelnost"),
        blank=True,
        null=True,
    )
    max_frequency = models.FloatField(
        verbose_name=_("Max pravidelnost"),
        blank=True,
        null=True,
    )
