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

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _

from dpnk.filters import CampaignFilter, campaign_filter_generator

from import_export.admin import ImportExportMixin

from related_admin import RelatedFieldAdmin

from . import models


@admin.register(models.DiscountCouponType)
class DiscountCouponTypeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('name', 'campaign', 'valid_until', 'prefix')
    list_filter = (CampaignFilter,)


class NullUserAttendanceListFilter(SimpleListFilter):
    title = _('Účastník kampaně')
    parameter_name = 'userattendance'

    def lookups(self, request, model_admin):
        return (
            ('False', _('Přiřazen'), ),
            ('True', _('Nepřiřazen'), ),
        )

    def queryset(self, request, queryset):
        if self.value() in ('False', 'True'):
            kwargs = {
                '{0}__isnull'.format(self.parameter_name): self.value() == 'True',
            }
            return queryset.filter(**kwargs).distinct()
        return queryset


@admin.register(models.DiscountCoupon)
class DiscountCouponAdmin(ImportExportMixin, RelatedFieldAdmin):
    list_display = (
        'name',
        'coupon_type__prefix',
        'token',
        'coupon_type',
        'coupon_pdf',
        'discount',
        'user_attendance_number',
        'note',
        'receiver',
        'attached_user_attendances_list',
        'attached_user_attendances_count',
        'sent',
    )
    readonly_fields = ('token', 'created', 'updated', 'author', 'updated_by')
    list_editable = ('note', 'receiver', 'discount', 'user_attendance_number', 'sent')
    list_filter = (
        campaign_filter_generator('coupon_type__campaign'),
        'coupon_type__name',
        'sent',
        'user_attendance_number',
        NullUserAttendanceListFilter,
    )
    search_fields = ('token', 'note', 'receiver')
