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
import re

from admin_views.admin import AdminViews

from adminactions import actions as admin_actions

from adminfilters.filters import RelatedFieldCheckBoxFilter, RelatedFieldComboFilter

from advanced_filters.admin import AdminAdvancedFiltersMixin

from daterange_filter.filter import DateRangeFilter

from django import forms
from django.contrib import admin
from django.db.models import Case, CharField, Count, TextField, When
from django.forms import Textarea
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from dpnk.admin_mixins import FormRequestMixin
from dpnk.filters import CampaignFilter, campaign_filter_generator
from dpnk.models import Campaign, UserAttendance

from import_export import fields, resources
from import_export.admin import ExportMixin, ImportExportMixin

from nested_admin import NestedModelAdmin, NestedTabularInline

from related_admin import RelatedFieldAdmin, getter_for_related_field

from . import actions, filters, models
from .admin_forms import IDENTIFIER_REGEXP
from .admin_mixins import ReadOnlyModelAdminMixin
from .forms import PackageTransactionForm


class PackageTransactionResource(resources.ModelResource):
    class Meta:
        model = models.PackageTransaction
        fields = (
            'id',
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
            'author__username',
            'team_package__box__delivery_batch__id',
            'team_package__box__id',
            'team_package__box__carrier_identification',
            'team_package__id',
        )
        export_order = fields

    payment_complete_date = fields.Field()

    def dehydrate_payment_complete_date(self, obj):
        if obj.user_attendance.representative_payment:
            return obj.user_attendance.payment_complete_date()

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


class PackageTransactionInline(admin.TabularInline):
    model = models.PackageTransaction
    extra = 0
    readonly_fields = [
        'author',
        'updated_by',
        't_shirt_size',
        'box_tracking_link',
    ]
    exclude = [
        'tracking_number',
    ]
    raw_id_fields = [
        'user_attendance',
        'team_package',
    ]
    formfield_overrides = {
        TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }
    form = PackageTransactionForm


class NestedPackageTransactionInline(NestedTabularInline, PackageTransactionInline):
    pass  # Nested version can't be used for dpnk.UserAttendanceAdmin


class TeamPackageInline(NestedTabularInline):
    model = models.TeamPackage
    extra = 0
    raw_id_fields = ('team',)
    inlines = (
        NestedPackageTransactionInline,
    )


@admin.register(models.SubsidiaryBox)
class SubsidiaryBoxAdmin(AdminAdvancedFiltersMixin, ImportExportMixin, RelatedFieldAdmin, AdminViews, NestedModelAdmin):
    admin_views = (
        (_('Označit balíky/krabice jako vyřízené'), '/admin/dispatch'),
    )

    list_display = (
        'identifier',
        'dispatched',
        'all_packages_dispatched',
        'dispatched_packages_count',
        'packages_count',
        'tracking_link',
        'delivery_batch__id',
        'delivery_batch__created',
        'subsidiary__company__name',
        'subsidiary',
        'subsidiary__city',
        'customer_sheets',
        'created',
    )
    inlines = (
        TeamPackageInline,
    )
    raw_id_fields = (
        'delivery_batch',
        'subsidiary',
    )
    search_fields = (
        'id',
        'carrier_identification',
        'subsidiary__address_street',
        'subsidiary__address_psc',
        'subsidiary__address_recipient',
        'subsidiary__address_city',
        'subsidiary__company__name',
    )
    advanced_filter_fields = (
        'carrier_identification',
        'dispatched',
        'delivery_batch__id',
        'delivery_batch__created',
        'subsidiary',
        'customer_sheets',
        'created',
    )
    actions = [actions.delivery_box_batch_download]
    list_filter = [
        campaign_filter_generator('delivery_batch__campaign'),
        'dispatched',
        filters.AllPackagesDispatched,
        ('delivery_batch__created', DateRangeFilter),
        'delivery_batch__id',
    ]
    readonly_fields = (
        'tracking_link',
        'all_packages_dispatched',
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'subsidiary__city',
        ).prefetch_related(
            'teampackage_set',
        )

    def get_search_results(self, request, queryset, search_term):
        search_term = search_term.strip()
        if re.match(IDENTIFIER_REGEXP, search_term) and search_term[0] == 'S':
                queryset = queryset.filter(id=search_term[1:])
                use_distinct = True
        else:
            queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset, use_distinct


@admin.register(models.TeamPackage)
class TeamPackageAdmin(ExportMixin, RelatedFieldAdmin, NestedModelAdmin):
    list_display = (
        'identifier',
        'dispatched',
        'box__dispatched',
        'box__identifier',
        'box__tracking_link',
        'box__name',
        'box__delivery_batch__id',
        'box__delivery_batch__created',
        'team__name',
        'team__subsidiary',
        'team__subsidiary__company',
    )
    box__identifier = getter_for_related_field('box__identifier', short_description=_('ID krabice'))
    team__name = getter_for_related_field('team__name', short_description=_('Tým'))
    box__name = getter_for_related_field('box__name', short_description=_('Krabice'))
    list_filter = (
        campaign_filter_generator('box__delivery_batch__campaign'),
        'dispatched',
        'box__dispatched',
        ('box__delivery_batch__created', DateRangeFilter),
        'box__delivery_batch__id',
    )
    raw_id_fields = (
        'box',
        'team',
    )
    search_fields = (
        'id',
        'team__name',
        'team__subsidiary__address_street',
        'team__subsidiary__company__name',
        'box__id',
        'box__carrier_identification',
    )
    inlines = (
        NestedPackageTransactionInline,
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'team__subsidiary__city',
            'box__subsidiary__city',
            'box__delivery_batch',
        )

    def get_search_results(self, request, queryset, search_term):
        search_term = search_term.strip()
        if re.match(IDENTIFIER_REGEXP, search_term):
            if search_term[0] == 'T':
                queryset = queryset.filter(id=search_term[1:])
                use_distinct = True
            elif search_term[0] == 'S':
                queryset = queryset.filter(box__id=search_term[1:])
                use_distinct = True
        else:
            queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset, use_distinct


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
        't_shirt_size__name',
        'team_package__box__delivery_batch__id',
        'team_package__box__tracking_link',
    )
    team_package__box__delivery_batch__id = getter_for_related_field('team_package__box__delivery_batch__id', short_description=_('ID krabice'))
    search_fields = (
        'id',
        'user_attendance__userprofile__nickname',
        'user_attendance__userprofile__user__first_name',
        'user_attendance__userprofile__user__last_name',
        'user_attendance__userprofile__user__username',
        'user_attendance__team__subsidiary__company__name',
    )
    list_filter = [
        campaign_filter_generator('user_attendance__campaign'),
        'status',
        'team_package__box__delivery_batch__id',
        'team_package__box__dispatched',
    ]
    raw_id_fields = [
        'user_attendance',
        'team_package',
    ]
    readonly_fields = (
        'author',
        'created',
        'updated_by',
    )
    list_max_show_all = 10000
    form = PackageTransactionForm

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'user_attendance__userprofile__user',
            'user_attendance__team__subsidiary__city',
            't_shirt_size__campaign',
        )


class DeliveryBatchForm(forms.ModelForm):
    class Meta:
        model = models.DeliveryBatch
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        if hasattr(self, 'request') and hasattr(self.request, 'campaign'):
            self.instance.campaign = self.request.campaign
        return ret_val


class SubsidiaryBoxInline(NestedTabularInline):
    model = models.SubsidiaryBox
    extra = 0
    readonly_fields = [
        'created',
        'identifier',
        'all_packages_dispatched',
    ]
    raw_id_fields = (
        'delivery_batch',
        'subsidiary',
    )


@admin.register(models.DeliveryBatch)
class DeliveryBatchAdmin(FormRequestMixin, NestedModelAdmin):
    list_display = [
        'id',
        'campaign',
        'created',
        'dispatched',
        'note',
        'package_transaction_count',
        'dispatched_count',
        'box_count',
        'author',
        'customer_sheets__url',
        'csv_data_url',
    ]
    readonly_fields = (
        'campaign',
        'author',
        'created',
        'updated_by',
        'package_transaction_count',
        'box_count',
        'dispatched_count',
        't_shirt_sizes',
    )
    inlines = [SubsidiaryBoxInline, ]
    list_filter = (CampaignFilter,)
    form = DeliveryBatchForm

    def get_list_display(self, request):
        for t_size in models.TShirtSize.objects.filter(campaign__slug=request.subdomain):
            field_name = "t_shirt_size_" + str(t_size.pk)
            if field_name not in self.list_display:
                self.list_display.append(field_name)

            def t_shirt_size(obj, t_size_id=t_size.pk):
                package_transactions = models.PackageTransaction.objects.filter(team_package__box__delivery_batch=obj)
                return package_transactions.filter(t_shirt_size__pk=t_size_id).aggregate(Count('t_shirt_size'))['t_shirt_size__count']
            t_shirt_size.short_description = t_size.name
            setattr(self, field_name, t_shirt_size)
        return self.list_display

    def package_transaction_count(self, obj):
        if not obj.pk:
            return obj.campaign.user_attendances_for_delivery().count()
        return models.PackageTransaction.objects.filter(team_package__box__delivery_batch=obj).count()
    package_transaction_count.short_description = _("Trik k odeslání")

    def t_shirt_sizes(self, obj):
        if not obj.pk:
            package_transactions = obj.campaign.user_attendances_for_delivery()
            t_shirts = models.TShirtSize.objects.filter(userattendance__in=package_transactions)
            t_shirts = t_shirts.annotate(size_count=Count('userattendance'))
        else:
            package_transactions = models.PackageTransaction.objects.filter(team_package__box__delivery_batch=obj)
            t_shirts = models.TShirtSize.objects.filter(packagetransaction__in=package_transactions)
            t_shirts = t_shirts.annotate(size_count=Count('packagetransaction'))
        t_shirts = t_shirts.values_list('name', 'size_count')
        return format_html_join(mark_safe("<br/>"), "{}: {}", t_shirts)
    t_shirt_sizes.short_description = _(u"Velikosti trik")

    def customer_sheets__url(self, obj):
        if obj.customer_sheets:
            return format_html("<a href='{}'>customer_sheets</a>", obj.customer_sheets.url)

    def csv_data_url(self, obj):
        if obj.tnt_order:
            return format_html("<a href='{}'>csv_data</a>", obj.tnt_order.url)

    def dispatched_count(self, obj):
        return obj.dispatched_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'author',
            'campaign',
        ).annotate(
            dispatched_count=Count(
                Case(
                    When(subsidiarybox__dispatched=True, then=1),
                    output_field=CharField(),
                ),
            ),
        )


class UserAttendanceToBatch(UserAttendance):
    class Meta:
        verbose_name = _(u"Uživatel na dávku objednávek")
        verbose_name_plural = _(u"Uživatelé na dávku objednávek")
        proxy = True


@admin.register(UserAttendanceToBatch)
class UserAttendanceToBatchAdmin(ReadOnlyModelAdminMixin, RelatedFieldAdmin, NestedModelAdmin):
    list_display = ('name', 't_shirt_size', 'team__subsidiary', 'team__subsidiary__city', 'payment_created', 'representative_payment__realized')
    list_filter = (('team__subsidiary__city', RelatedFieldCheckBoxFilter), ('t_shirt_size', RelatedFieldComboFilter), 'transactions__status')
    search_fields = (
        'userprofile__nickname',
        'userprofile__user__first_name',
        'userprofile__user__last_name',
        'userprofile__user__username',
        'userprofile__user__email',
        'team__name',
        'team__subsidiary__address_street',
        'team__subsidiary__address_psc',
        'team__subsidiary__address_recipient',
        'team__subsidiary__address_city',
        'team__subsidiary__company__name',
    )
    actions = (actions.create_batch, )

    def get_actions(self, request):
        return {'create_batch': (actions.create_batch, 'create_batch', actions.create_batch.short_description)}
    list_max_show_all = 10000

    def payment_created(self, obj):
        return obj.payment_created
    payment_created.admin_order_field = 'payment_created'
    payment_created.short_description = 'Datum vytvoření platby'

    def get_queryset(self, request):
        campaign = Campaign.objects.get(slug=request.subdomain)
        queryset = campaign.user_attendances_for_delivery()
        return queryset


# register all adminactions
admin.site.add_action(admin_actions.merge)
