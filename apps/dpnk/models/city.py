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


class City(models.Model):
    """Město"""

    class Meta:
        verbose_name = _(u"Město")
        verbose_name_plural = _(u"Města")
        ordering = ('name',)

    name = models.CharField(
        verbose_name=_(u"Jméno"),
        unique=True,
        max_length=40,
        null=False,
    )
    slug = models.SlugField(
        unique=True,
        verbose_name=_("Subdoména v URL"),
        blank=False,
    )
    wp_slug = models.SlugField(
        unique=True,
        verbose_name=_("Subdoména na WordPressu"),
        help_text=_("Pokud není vyplněno, použije se slug"),
        blank=True,
        null=True,
    )
    cyklistesobe_slug = models.SlugField(
        verbose_name=_(u"Jméno skupiny na webu Cyklisté sobě"),
        max_length=40,
        null=True,
    )
    location = models.PointField(
        verbose_name=_(u"poloha města"),
        srid=4326,
        null=True,
        blank=False,
    )

    def __str__(self):
        return "%s" % self.name

    def get_wp_slug(self):
        if self.wp_slug:
            return self.wp_slug
        return self.slug
