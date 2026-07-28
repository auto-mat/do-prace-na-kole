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

from django.conf import settings
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _

from dpnk.filters import CampaignFilter, campaign_filter_generator

from import_export import resources
from import_export.admin import ImportExportMixin

from related_admin import RelatedFieldAdmin

import smmapdfs.actions
from smmapdfs.admin_abcs import PdfSandwichAdmin, PdfSandwichFieldAdmin, fieldForm

from . import models


@admin.register(models.DiscountCouponType)
class DiscountCouponTypeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "campaign",
        "valid_until",
        "prefix",
    )
    list_filter = (CampaignFilter,)


class NullUserAttendanceListFilter(SimpleListFilter):
    title = _("Účastník kampaně")
    parameter_name = "userattendance"

    def lookups(self, request, model_admin):
        return (
            (
                "False",
                _("Přiřazen"),
            ),
            (
                "True",
                _("Nepřiřazen"),
            ),
        )

    def queryset(self, request, queryset):
        if self.value() in ("False", "True"):
            kwargs = {
                "{0}__isnull".format(self.parameter_name): self.value() == "True",
            }
            return queryset.filter(**kwargs).distinct()
        return queryset


class DiscountCouponResource(resources.ModelResource):
    class Meta:
        model = models.DiscountCoupon
        fields = (
            "discount",
            "note",
            "coupon_type",
            "receiver",
            "recipient_name",
            "user_attendance_number",
        )

    def import_field(self, field, obj, data, **kwargs):
        if field.column_name == "coupon_type":
            obj.coupon_type = models.DiscountCouponType.objects.get(
                prefix=data["coupon_type"]
            )
        else:
            super().import_field(field, obj, data, **kwargs)

    def get_instance(self, instance_loader, row):
        return False


@admin.register(models.DiscountCoupon)
class DiscountCouponAdmin(ImportExportMixin, RelatedFieldAdmin):
    list_display = (
        "name",
        "coupon_type__prefix",
        "token",
        "get_pdf",
        "coupon_type",
        "discount",
        "user_attendance_number",
        "note",
        "receiver",
        "recipient_name",
        "attached_user_attendances_list",
        "attached_user_attendances_count",
    )
    exclude = (
        "sent",
        "coupon_pdf",
    )
    readonly_fields = (
        "token",
        "created",
        "updated",
        "author",
        "updated_by",
    )
    list_editable = (
        "note",
        "receiver",
        "recipient_name",
        "discount",
        "user_attendance_number",
    )
    list_filter = (
        campaign_filter_generator("coupon_type__campaign"),
        "coupon_type__name",
        "user_attendance_number",
        NullUserAttendanceListFilter,
    )
    search_fields = (
        f"token__{settings.ADMIN_SEARCH_FIELD_LOOKUP}",
        f"note__{settings.ADMIN_SEARCH_FIELD_LOOKUP}",
        f"receiver__{settings.ADMIN_SEARCH_FIELD_LOOKUP}",
    )

    resource_class = DiscountCouponResource
    actions = (smmapdfs.actions.make_pdfsandwich,)


@admin.register(models.CouponSandwich)
class DiscountCouponSandwichAdmin(PdfSandwichAdmin):
    pass


@admin.register(models.CouponField)
class CouponFieldAdmin(PdfSandwichFieldAdmin):
    form = fieldForm(models.CouponField)
