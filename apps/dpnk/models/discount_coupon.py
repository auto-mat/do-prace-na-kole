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

from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, RegexValidator
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


@with_author
class DiscountCoupon(models.Model):
    coupon_type = models.ForeignKey(
        DiscountCouponType,
        verbose_name=_("typ voucheru"),
        null=False,
        blank=False,
        default='',
    )
    token = models.TextField(
        verbose_name=_("token"),
        blank=False,
        null=False,
        unique=True,
    )
    discount = models.PositiveIntegerField(
        verbose_name=_("sleva (v procentech)"),
        null=False,
        blank=False,
        default=100,
        validators=[MaxValueValidator(100)],
    )
    user_attendance_number = models.PositiveIntegerField(
        verbose_name=_("Počet možných využití"),
        help_text=_("Pokud se nevyplní, bude počet využití neomezený"),
        null=True,
        blank=True,
        default=1,
    )
    note = models.CharField(
        verbose_name=_("poznámka"),
        max_length=50,
        blank=True,
        null=True,
    )
    receiver = models.CharField(
        verbose_name=_("příjemce"),
        max_length=50,
        blank=True,
        null=True,
    )
    sent = models.BooleanField(
        verbose_name=_("Odeslaný"),
        default=False,
        null=False,
    )
    created = models.DateTimeField(
        verbose_name=_(u"Datum vytvoření"),
        auto_now_add=True,
        null=True,
    )
    updated = models.DateTimeField(
        verbose_name=_(u"Datum poslední změny"),
        auto_now=True,
        null=True,
    )

    def available(self):
        if self.user_attendance_number is None:
            return True
        user_count = self.userattendance_set.count()
        return self.user_attendance_number > user_count

    class Meta:
        verbose_name = _("Slevový kupón")
        verbose_name_plural = _("Slevové kupóny")
        unique_together = (
            ("token", "coupon_type"),
        )

    def __str__(self):
        return "%s-%s" % (self.coupon_type.prefix, self.token)

    def discount_multiplier(self):
        return (100 - self.discount) / 100.0

    def name(self):
        return self.__str__()

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.token = User.objects.make_random_password(length=6, allowed_chars='ABCDEFGHJKLMNPQRSTUVWXYZ')
        super().save(*args, **kwargs)
