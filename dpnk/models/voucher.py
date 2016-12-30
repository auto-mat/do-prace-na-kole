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

from .user_attendance import UserAttendance


class Voucher(models.Model):
    TYPES = [
        ('rekola', _(u"ReKola")),
        ('sportlife', _(u"SportLife")),
    ]
    voucher_type = models.CharField(
        verbose_name=_(u"typ voucheru"),
        choices=TYPES,
        max_length=10,
        null=False,
        blank=False,
        default='rekola',
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
    )

    class Meta:
        verbose_name = _(u"Voucher")
        verbose_name_plural = _(u"Vouchery")
