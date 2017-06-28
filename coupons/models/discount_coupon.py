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

from coupons.models.discount_coupon_type import DiscountCouponType

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.core.validators import MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from ..generate_pdf import generate_coupon_pdf


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
    coupon_pdf = models.FileField(
        verbose_name=_(u"PDF kupón"),
        upload_to='coupons',
        blank=True,
        null=True,
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
        app_label = "coupons"

    def __str__(self):
        return "%s-%s" % (self.coupon_type.prefix, self.token)

    def discount_multiplier(self):
        return (100 - self.discount) / 100.0

    def name(self):
        return self.__str__()

    def attached_user_attendances_list(self):
        return ", ".join([str(u) for u in self.userattendance_set.all()])

    def attached_user_attendances_count(self):
        return self.userattendance_set.count()

    def save(self, *args, **kwargs):
        if self.token is None or self.token == "":
            self.token = User.objects.make_random_password(length=6, allowed_chars='ABCDEFGHJKLMNPQRSTUVWXYZ')
        super().save(*args, **kwargs)


@receiver(post_save, sender=DiscountCoupon)
def create_coupon_file(sender, instance, created, **kwargs):
    if not instance.coupon_pdf:
        temp = NamedTemporaryFile()
        generate_coupon_pdf(
            temp,
            instance.name(),
            instance.coupon_type.valid_until.strftime("%d. %m. %Y") if instance.coupon_type.valid_until else None,
        )
        filename = "%s/coupon_%s.pdf" % (
            instance.coupon_type.campaign.slug,
            hash(str(instance.pk) + settings.SECRET_KEY)
        )
        instance.coupon_pdf.save(filename, File(temp))
        instance.save()
