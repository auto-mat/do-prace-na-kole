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

from .campaign import Campaign
from .user_attendance import UserAttendance


class Voucher(models.Model):
    voucher_type1 = models.ForeignKey(
        'VoucherType',
        verbose_name=_("Typ voucheru"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    token = models.TextField(
        verbose_name=_(u"token"),
        blank=False,
        null=True,
    )
    user_attendance = models.ForeignKey(
        UserAttendance,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    campaign = models.ForeignKey(
        Campaign,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("Voucher třetí strany")
        verbose_name_plural = _("Vouchery třetích stran")

    #DEPRECATED
    TYPES = [
        ('rekola', _("ReKola")),
        ('sportlife', _("SportLife")),
        ('am-eshop', _("Automat benefiční obchod")),
    ]
    voucher_type = models.CharField(
        verbose_name=_(u"DEPRECATED"),
        choices=TYPES,
        max_length=10,
        null=False,
        blank=False,
        default='rekola',
    )


class VoucherType(models.Model):
    class Meta:
        verbose_name = _("Druh voucheru třetí strany")
        verbose_name_plural = _("Druhy voucherů třetích stran")

    name = models.CharField(
        verbose_name=_("Jméno"),
        max_length=255,
        null=False,
        blank=False,
        default='Rekola',
    )

    eshop_url = models.CharField(
        verbose_name=_("E-Shop URL"),
        max_length=255,
        null=False,
        blank=False,
        default='https://obchod.auto-mat.cz',
    )
    teaser_img = models.ImageField(
        verbose_name=_("Teaser image"),
        upload_to='3rd_party_voucher_teaser_images/image',
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name
