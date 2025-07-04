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

from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.html import format_html
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import smmapdfs
import smmapdfs.model_abcs


class CouponField(smmapdfs.model_abcs.PdfSandwichFieldABC):
    fields = {
        "token": (lambda obj: str(obj)),
        "good_till": (
            lambda obj: obj.coupon_type.valid_until.strftime("%d. %m. %Y")
            if obj.coupon_type.valid_until
            else None
        ),
        "campaign_year": (lambda obj: "%s." % obj.coupon_type.campaign.year),
        "discount": (lambda obj: "%s%%" % obj.discount),
        "name": (lambda obj: obj.recipient_name),
        "num_uses": (
            lambda obj: ("%s×" % str(obj.user_attendance_number))
            if obj.user_attendance_number and obj.user_attendance_number > 1
            else ""
        ),
    }


class CouponSandwich(smmapdfs.model_abcs.PdfSandwichABC):
    field_model = CouponField
    obj = models.ForeignKey(
        # black
        "DiscountCoupon",
        null=False,
        blank=False,
        default="",
        on_delete=models.CASCADE,
    )

    def get_email(self):
        return [self.obj.receiver]

    def get_language(self):
        return "cs"


@with_author
class DiscountCoupon(models.Model):
    sandwich_model = CouponSandwich
    coupon_type = models.ForeignKey(
        DiscountCouponType,
        verbose_name=_("typ voucheru"),
        null=False,
        blank=False,
        default="",
        on_delete=models.CASCADE,
    )
    token = models.TextField(
        # black
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
        # black
        verbose_name=_("poznámka"),
        max_length=50,
        blank=True,
        null=True,
    )
    receiver = models.CharField(
        # black
        verbose_name=_("příjemce"),
        max_length=50,
        blank=True,
        null=True,
    )
    recipient_name = models.CharField(
        # black
        verbose_name=_("jméno příjemce"),
        max_length=100,
        blank=True,
        null=True,
    )
    created = models.DateTimeField(
        # black
        verbose_name=_("Datum vytvoření"),
        auto_now_add=True,
        null=True,
    )
    updated = models.DateTimeField(
        # black
        verbose_name=_("Datum poslední změny"),
        auto_now=True,
        null=True,
    )
    sent = models.BooleanField(
        # black
        verbose_name=_("DEPRECATED"),
        default=False,
        null=False,
    )
    coupon_pdf = models.FileField(
        # black
        verbose_name=_("DEPRECATED"),
        upload_to="coupons",
        blank=True,
        null=True,
    )

    def get_pdf(self):
        try:
            url = self.couponsandwich_set.first().pdf.url
        except (ValueError, AttributeError):
            try:
                url = self.coupon_pdf.url
            except ValueError:
                url = None
        if url:
            return format_html("<a href='{}'>{}</a>", url, _("PDF file"))
        else:
            return "-"

    get_pdf.short_description = _("PDF")

    def available(self):
        # Checking lifetime
        if self.coupon_type.valid_until:
            return self.coupon_type.valid_until > timezone.now().date()
        # Checking number of usage
        if self.user_attendance_number is None:
            return True
        user_count = self.userattendance_set.count()
        return self.user_attendance_number > user_count

    def get_sandwich_type(self):
        return self.coupon_type.sandwich_type

    class Meta:
        verbose_name = _("Slevový kupón")
        verbose_name_plural = _("Slevové kupóny")
        unique_together = (
            # black
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
        return ", ".join(
            [u.userprofile.user.get_full_name() for u in self.userattendance_set.all()]
        )

    def attached_user_attendances_count(self):
        return self.userattendance_set.count()

    def save(self, *args, **kwargs):
        if self.token is None or self.token == "":
            self.token = User.objects.make_random_password(
                # black
                length=6,
                allowed_chars="ABCDEFGHJKLMNPQRSTUVWXYZ",
            )
        super().save(*args, **kwargs)


@receiver(post_save, sender=DiscountCoupon)
def create_coupon_file(sender, instance, created, **kwargs):
    smmapdfs.tasks.make_pdfsandwich.delay(
        # black
        instance._meta.app_label,
        instance._meta.object_name,
        instance.pk,
    )
