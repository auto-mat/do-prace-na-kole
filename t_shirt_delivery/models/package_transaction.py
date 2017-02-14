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
from django.db import transaction
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from dpnk.models import Status, Transaction

from modulus11 import mod11


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
        null=False,
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
        verbose_name = _(u"Transakce balíku")
        verbose_name_plural = _(u"Transakce balíku")

    def tracking_number_cnc(self):
        str_tn = str(self.tracking_number)
        return str_tn + str(mod11.calc_check_digit(str_tn))

    def tnt_con_reference(self):
        batch_date = self.delivery_batch.created.strftime("%y%m%d")
        return "{:s}-{:s}-{:0>6.0f}".format(str(self.delivery_batch.pk), batch_date, self.pk)

    def tracking_link(self):
        return mark_safe(
            "<a href='http://www.tnt.com/webtracker/tracking.do?"
            "requestType=GEN&"
            "searchType=REF&"
            "respLang=cs&"
            "respCountry=cz&"
            "sourceID=1&"
            "sourceCountry=ww&"
            "cons=%(number)s&"
            "navigation=1&"
            "genericSiteIdent='>%(number)s</a>" %
            {'number': self.tnt_con_reference()},
        )

    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.t_shirt_size:
            self.t_shirt_size = self.user_attendance.t_shirt_size
        if not self.tracking_number:
            campaign = self.user_attendance.campaign
            first = campaign.tracking_number_first
            last = campaign.tracking_number_last
            last_transaction = PackageTransaction.objects.filter(tracking_number__gte=first, tracking_number__lte=last).order_by("tracking_number").last()
            if last_transaction:
                if last_transaction.tracking_number == last:
                    raise Exception(_(u"Došla číselná řada pro balíčkové transakce"))
                self.tracking_number = last_transaction.tracking_number + 1
            else:
                self.tracking_number = first
        super().save(*args, **kwargs)
