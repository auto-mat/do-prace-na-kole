# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
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


from django import forms
from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from dpnk import transaction_forms
from dpnk.admin_mixins import FormRequestMixin
from dpnk.filters import CampaignFilter, campaign_filter_generator
from dpnk.models import Campaign

from import_export import fields, resources
from import_export.admin import ExportMixin

from nested_inline.admin import NestedTabularInline

from related_admin import RelatedFieldAdmin

from . import models
from .forms import PackageTransactionForm


class PackageTransactionResource(resources.ModelResource):
    class Meta:
        model = models.PackageTransaction
        fields = (
            'id',
            'delivery_batch',
            'payment_complete_date',
            'user_attendance',
            'user_attendance__name',
            'user_attendance__userprofile__telephone',
            'user_attendance__userprofile__user__email',
            'created',
            'realized',
            'status',
            'user_attendance__team__subsidiary__address_street',
            'user_attendance__team__subsidiary__address_psc',
            'user_attendance__team__subsidiary__address_city',
            'user_attendance__team__subsidiary__company__name',
            'company_admin_email',
            't_shirt_size__name',
            'delivery_batch',
            'author__username',
        )
        export_order = fields

    payment_complete_date = fields.Field()

    def dehydrate_payment_complete_date(self, obj):
        if obj.user_attendance.representative_payment:
            return obj.user_attendance.representative_payment.payment_complete_date()

    user_attendance__name = fields.Field()

    def dehydrate_user_attendance__name(self, obj):
        return "%s %s" % (obj.user_attendance.first_name(), obj.user_attendance.last_name())

    user_attendance__team__subsidiary__address_street = fields.Field()

    def dehydrate_user_attendance__team__subsidiary__address_street(self, obj):
        if obj.user_attendance.team:
            return "%s %s" % (obj.user_attendance.team.subsidiary.address_street, obj.user_attendance.team.subsidiary.address_street_number)

    user_attendance__team__subsidiary__address_psc = fields.Field()

    def dehydrate_user_attendance__team__subsidiary__address_psc(self, obj):
        if obj.user_attendance.team:
            return obj.user_attendance.team.subsidiary.address_psc

    user_attendance__team__subsidiary__address_city = fields.Field()

    def dehydrate_user_attendance__team__subsidiary__address_city(self, obj):
        if obj.user_attendance.team:
            return obj.user_attendance.team.subsidiary.address_city

    company_admin_email = fields.Field()

    def dehydrate_company_admin_email(self, obj):
        company_admin = obj.user_attendance.get_asociated_company_admin()
        if company_admin:
            return company_admin.first().userprofile.user.email
        else:
            return ""


@admin.register(models.SubsidiaryBox)
class SubsidiaryBoxAdmin(ExportMixin, RelatedFieldAdmin):
    list_display = (
        'delivery_batch',
        'subsidiary',
        'customer_sheets',
        'created',
    )
    raw_id_fields = (
        'delivery_batch',
        'subsidiary',
    )


@admin.register(models.TeamPackage)
class TeamPackageAdmin(ExportMixin, RelatedFieldAdmin):
    list_display = (
        'box',
        'box__delivery_batch',
        'team',
        'team__subsidiary',
    )
    list_filter = (
        'box__delivery_batch',
    )
    raw_id_fields = (
        'box',
        'team',
    )
    search_fields = (
        'team__name',
        'team__subsidiary__address_street',
        'team__subsidiary__company__name',
    )


@admin.register(models.PackageTransaction)
class PackageTransactionAdmin(ExportMixin, RelatedFieldAdmin):
    resource_class = PackageTransactionResource
    list_display = (
        'id',
        'user_attendance',
        'created',
        'realized',
        'status',
        'author',
        'user_attendance__team__subsidiary',
        'user_attendance__team__subsidiary__company__name',
        't_shirt_size',
        'delivery_batch',
    )
    search_fields = (
        'id',
        'user_attendance__userprofile__nickname',
        'user_attendance__userprofile__user__first_name',
        'user_attendance__userprofile__user__last_name',
        'user_attendance__userprofile__user__username',
        'user_attendance__team__subsidiary__company__name',
    )
    list_filter = [campaign_filter_generator('user_attendance__campaign'), 'status', 'delivery_batch']
    raw_id_fields = ('user_attendance',)
    readonly_fields = ('author', 'created')
    list_max_show_all = 10000
    form = transaction_forms.PaymentForm


class DeliveryBatchForm(forms.ModelForm):
    class Meta:
        model = models.DeliveryBatch
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        ret_val = super(DeliveryBatchForm, self).__init__(*args, **kwargs)
        if hasattr(self, 'request'):
            self.instance.campaign = Campaign.objects.get(slug=self.request.subdomain)
        return ret_val


class PackageTransactionInline(NestedTabularInline):
    model = models.PackageTransaction
    extra = 0
    readonly_fields = ['author', 'updated_by', 't_shirt_size']
    raw_id_fields = ['user_attendance', 'delivery_batch']
    form = PackageTransactionForm


class SubsidiaryBoxInline(NestedTabularInline):
    model = models.SubsidiaryBox
    extra = 0
    readonly_fields = [
        'created',
    ]
    raw_id_fields = (
        'delivery_batch',
        'subsidiary',
    )


@admin.register(models.DeliveryBatch)
class DeliveryBatchAdmin(FormRequestMixin, admin.ModelAdmin):
    list_display = ['id', 'campaign', 'created', 'dispatched', 'package_transaction_count', 'box_count', 'author', 'customer_sheets__url', 'tnt_order__url']
    readonly_fields = ('campaign', 'author', 'created', 'updated_by', 'package_transaction_count', 'box_count', 't_shirt_sizes')
    inlines = [SubsidiaryBoxInline, ]
    list_filter = (CampaignFilter,)
    form = DeliveryBatchForm

    def get_list_display(self, request):
        for t_size in models.TShirtSize.objects.filter(campaign__slug=request.subdomain):
            field_name = "t_shirt_size_" + str(t_size.pk)
            if field_name not in self.list_display:
                self.list_display.append(field_name)

            def t_shirt_size(obj, t_size_id=t_size.pk):
                return obj.packagetransaction_set.filter(t_shirt_size__pk=t_size_id).aggregate(Count('t_shirt_size'))['t_shirt_size__count']
            t_shirt_size.short_description = t_size.name
            setattr(self, field_name, t_shirt_size)
        return self.list_display

    def package_transaction_count(self, obj):
        if not obj.pk:
            return obj.campaign.user_attendances_for_delivery().count()
        return obj.packagetransaction_set.count()
    package_transaction_count.short_description = _("Trik k odeslání")

    def t_shirt_sizes(self, obj):
        if not obj.pk:
            package_transactions = obj.campaign.user_attendances_for_delivery()
        else:
            package_transactions = obj.packagetransaction_set.all()
        t_shirts = models.TShirtSize.objects.filter(packagetransaction__in=package_transactions)
        t_shirts = t_shirts.annotate(size_count=Count('packagetransaction'))
        t_shirts = t_shirts.values_list('name', 'size_count')
        return format_html_join(mark_safe("<br/>"), "{}: {}", t_shirts)
    t_shirt_sizes.short_description = _(u"Velikosti trik")

    def customer_sheets__url(self, obj):
        if obj.customer_sheets:
            return format_html("<a href='{}'>customer_sheets</a>", obj.customer_sheets.url)

    def tnt_order__url(self, obj):
        if obj.tnt_order:
            return format_html("<a href='{}'>tnt_order</a>", obj.tnt_order.url)
