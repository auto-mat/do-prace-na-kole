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
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _


class DiscountCouponType(models.Model):
    name = models.CharField(
        verbose_name=_(u"jméno typu voucheru"),
        max_length=20,
        blank=False,
        null=False,
    )
    prefix = models.CharField(
        validators=[
            RegexValidator(
                regex='^[A-Z]*$',
                message=_('Prefix musí sestávat pouze z velkých písmen'),
                code='invalid_prefix',
            ),
        ],
        verbose_name=_("prefix"),
        max_length=10,
        null=False,
        blank=False,
        unique=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Typ slevového kupónu")
        verbose_name_plural = _("Typy slevového kupónu")
        app_label = "coupons"
