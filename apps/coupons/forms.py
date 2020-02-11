# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
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
import logging

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator
from django.utils.translation import ugettext_lazy as _

from dpnk.forms import PrevNextMixin
from dpnk.util import today

from . import models

logger = logging.getLogger(__name__)


class DiscountCouponForm(PrevNextMixin, forms.Form):
    code = forms.CharField(
        label=_("Kód voucheru"),
        max_length=10,
        required=True,
        validators=[
            RegexValidator(r'^[a-zA-Z]+-[abcdefghjklmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ]+$', _('Nesprávný formát voucheru')),
            MinLengthValidator(9),
        ],
    )

    def clean(self):
        cleaned_data = super().clean()
        if 'code' in cleaned_data:
            prefix, base_code = cleaned_data['code'].upper().split("-")
            try:
                discount_coupon = models.DiscountCoupon.objects.exclude(
                    coupon_type__valid_until__isnull=False,
                    coupon_type__valid_until__lt=today(),
                ).get(
                    coupon_type__prefix=prefix,
                    token=base_code,
                )
                if not discount_coupon.available():
                    raise ValidationError(_("Tento slevový kupón již byl použit"))
                cleaned_data['discount_coupon'] = discount_coupon
            except models.DiscountCoupon.DoesNotExist:
                raise ValidationError(_("Tento slevový kupón neexistuje, nebo již byl použit"))
        return cleaned_data
