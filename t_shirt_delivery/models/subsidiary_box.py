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
from django.utils.translation import ugettext_lazy as _


class SubsidiaryBox(models.Model):
    """ Krabice pro firmu """

    class Meta:
        verbose_name = _("Krabice pro firmu")
        verbose_name_plural = _("Krabice pro firmu")

    delivery_batch = models.ForeignKey(
        'dpnk.DeliveryBatch',
        verbose_name=_("Dávka objednávek"),
        null=False,
        blank=False,
    )
    subsidiary = models.ForeignKey(
        'dpnk.Subsidiary',
        verbose_name=_("Pobočka"),
        null=False,
        blank=False,
    )
