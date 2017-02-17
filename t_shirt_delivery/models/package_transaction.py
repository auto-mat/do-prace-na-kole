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

from dpnk.models import Status, Transaction


class PackageTransaction(Transaction):
    """Transakce balíku"""

    t_shirt_size = models.ForeignKey(
        't_shirt_delivery.TShirtSize',
        verbose_name=_(u"Velikost trička"),
        null=True,
        blank=False,
    )
    tracking_number = models.PositiveIntegerField(
        verbose_name=_(u"Tracking number"),
        unique=True,
        null=True,
        default=None,
    )
    delivery_batch = models.ForeignKey(
        't_shirt_delivery.DeliveryBatch',
        verbose_name=_(u"Dávka objednávek"),
        null=True,
        blank=True,
    )
    team_package = models.ForeignKey(
        't_shirt_delivery.TeamPackage',
        verbose_name=_("Týmový balíček"),
        null=True,
        blank=False,
    )

    shipped_statuses = [
        Status.PACKAGE_ACCEPTED_FOR_ASSEMBLY,
        Status.PACKAGE_ASSEMBLED,
        Status.PACKAGE_SENT,
        Status.PACKAGE_DELIVERY_CONFIRMED,
        Status.PACKAGE_DELIVERY_DENIED,
    ]

    class Meta:
        verbose_name = _("Transakce trika")
        verbose_name_plural = _("Transakce trika")

    def save(self, *args, **kwargs):
        if not self.t_shirt_size:
            self.t_shirt_size = self.user_attendance.t_shirt_size
        super().save(*args, **kwargs)
