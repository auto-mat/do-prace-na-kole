# -*- coding: utf-8 -*-
# Author: Hynek Hanke <hynek.hanke@auto-mat.cz>
#
# Copyright (C) 2012 o.s. Auto*Mat
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

"""Administrátorské rozhraní pro Do práce na kole"""

import pprint
import types

from adminactions import actions as admin_actions, merge

from adminfilters.filters import AllValuesComboFilter, RelatedFieldCheckBoxFilter, RelatedFieldComboFilter

from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin

from daterange_filter.filter import DateRangeFilter

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.sessions.models import Session
from django.core.urlresolvers import reverse
from django.db.models import Count, Sum
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _

from djcelery.models import TaskMeta

from import_export import fields, resources
from import_export.admin import ExportMixin, ImportExportMixin, ImportMixin

from leaflet.admin import LeafletGeoAdmin

from nested_inline.admin import NestedModelAdmin, NestedStackedInline, NestedTabularInline

from polymorphic.admin import PolymorphicChildModelAdmin, PolymorphicParentModelAdmin

from price_level import models as price_level_models

from related_admin import RelatedFieldAdmin

from t_shirt_delivery.admin import PackageTransactionInline
from t_shirt_delivery.forms import PackageTransactionForm
from t_shirt_delivery.models import PackageTransaction, TShirtSize

from . import actions, models, transaction_forms
from .admin_mixins import CityAdminMixin, FormRequestMixin, city_admin_mixin_generator
from .filters import (
    CampaignFilter,
    CityCampaignFilter,
    EmailFilter,
    HasReactionFilter,
    HasRidesFilter,
    HasTeamFilter,
    HasUserAttendanceFilter,
    HasUserprofileFilter,
    HasVoucherFilter,
    InvoicePaidFilter,
    IsForCompanyFilter,
    TrackFilter,
    campaign_filter_generator,
)


def admin_links(args_generator):
    return format_html_join(
        mark_safe('<br/>'),
        '<a href="{}">{}</a>',
        args_generator,
    )


class PaymentInline(NestedTabularInline):
    model = models.Payment
    extra = 0
    form = transaction_forms.PaymentForm
    readonly_fields = ['user_attendance', 'order_id', 'session_id', 'trans_id', 'error', 'author', 'updated_by']
    raw_id_fields = ['invoice', ]


class CommonTransactionInline(NestedTabularInline):
    model = models.CommonTransaction
    extra = 0
    readonly_fields = ['user_attendance', 'author', 'updated_by']
    form = transaction_forms.CommonTransactionForm


class UserActionTransactionInline(NestedTabularInline):
    model = models.UserActionTransaction
    extra = 0
    readonly_fields = ['user_attendance', 'author', 'updated_by']
    form = transaction_forms.UserActionTransactionForm


class TeamInline(admin.TabularInline):
    model = models.Team
    extra = 0
    readonly_fields = ['invitation_token', ]


class SubsidiaryInline(admin.TabularInline):
    model = models.Subsidiary
    extra = 0


@admin.register(models.City)
class CityAdmin(LeafletGeoAdmin):
    list_display = ('name', 'slug', 'cyklistesobe_slug', 'id', )
    prepopulated_fields = {'slug': ('name',), 'cyklistesobe_slug': ('name',)}
    list_filter = ('cityincampaign__campaign',)


class DontValidateCompnayFieldsMixin(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'dic' in self.fields:
            self.fields['dic'].required = False
        if 'ico' in self.fields:
            self.fields['ico'].required = False
        if 'address_city' in self.fields:
            self.fields['address_city'].required = False
        if 'address_psc' in self.fields:
            self.fields['address_psc'].required = False
        if 'address_street_number' in self.fields:
            self.fields['address_street_number'].required = False
        if 'address_street' in self.fields:
            self.fields['address_street'].required = False


class CompanyForm(DontValidateCompnayFieldsMixin, forms.ModelForm):
    class Meta:
        model = models.Company
        fields = "__all__"


class CompanyMergeForm(DontValidateCompnayFieldsMixin, merge.MergeForm):
    def full_clean(self):
        super().full_clean()
        if 'address_psc' in self._errors:
            del self._errors['address_psc']


class CompanyResource(resources.ModelResource):
    class Meta:
        model = models.Company
        fields = (
            'id',
            'name',
            'ico',
            'dic',
        )
        export_order = fields


@admin.register(models.Company)
class CompanyAdmin(city_admin_mixin_generator('subsidiaries__city__in'), ExportMixin, admin.ModelAdmin):
    list_display = (
        'name',
        'subsidiaries_text',
        'ico',
        'dic',
        'address_street',
        'address_street_number',
        'address_recipient',
        'address_psc',
        'address_city',
        'id',
    )
    inlines = [SubsidiaryInline, ]
    list_filter = [CityCampaignFilter, 'subsidiaries__city', 'active']
    readonly_fields = ['subsidiary_links']
    search_fields = (
        'name',
        'address_street',
        'address_street_number',
        'address_recipient',
        'address_psc',
        'address_city',
        'address_district',
    )
    list_max_show_all = 10000
    form = CompanyForm
    merge_form = CompanyMergeForm
    resource_class = CompanyResource

    def subsidiaries_text(self, obj):
        return " | ".join(
            ['%s' % (str(u)) for u in models.Subsidiary.objects.filter(company=obj)])
    subsidiaries_text.short_description = _('Pobočky')

    def subsidiary_links(self, obj):
        return admin_links(
            [
                (reverse('admin:dpnk_subsidiary_change', args=(u.pk,)), str(u))
                for u in models.Subsidiary.objects.filter(company=obj)
            ]
        )
    subsidiary_links.short_description = _('Pobočky')


def create_subsidiary_resource(campaign_slugs):
    campaign_fields = ["user_count_%s" % sl for sl in campaign_slugs]

    class SubsidiaryResource(resources.ModelResource):
        class Meta:
            model = models.Subsidiary
            fields = [
                'id',
                'name',
                'address_street',
                'address_street_number',
                'address_recipient',
                'address_psc',
                'address_city',
                'address_district',
                'company__name',
                'city__name',
                'user_count',
                'team_count',
            ] + campaign_fields
            export_order = fields

        name = fields.Field()

        def dehydrate_name(self, obj):
            return obj.name()

        team_count = fields.Field()

        def dehydrate_team_count(self, obj):
            return obj.team_count

        user_count = fields.Field()

        def dehydrate_user_count(self, obj):
            return obj.teams.distinct().aggregate(Sum('member_count'))['member_count__sum']

        for slug in campaign_slugs:
            vars()['user_count_%s' % slug] = fields.Field()

    for slug in campaign_slugs:
        def func(slug, obj):
            return obj.teams.filter(campaign__slug=slug).distinct().aggregate(Sum('member_count'))['member_count__sum']
        setattr(SubsidiaryResource, "dehydrate_user_count_%s" % slug, types.MethodType(func, slug))

    return SubsidiaryResource


@admin.register(models.Subsidiary)
class SubsidiaryAdmin(CityAdminMixin, ExportMixin, admin.ModelAdmin):
    list_display = (
        'name',
        'company',
        'city',
        'user_count',
        'team_count',
        'id',
    )
    inlines = [TeamInline, ]
    list_filter = [campaign_filter_generator('teams__campaign'), 'city', 'active']
    search_fields = (
        'address_recipient',
        'company__name',
        'address_street',
        'address_street_number',
        'address_recipient',
        'address_psc',
        'address_city',
        'address_district')
    raw_id_fields = ('company',)
    list_max_show_all = 10000
    save_as = True

    readonly_fields = ['team_links', ]

    @property
    def resource_class(self):
        return create_subsidiary_resource(models.Campaign.objects.values_list("slug", flat=True))

    def get_queryset(self, request):
        self.campaign = request.subdomain
        self.filter_campaign = {}
        filter_campaign = request.GET.get('campaign', request.subdomain)
        if filter_campaign != 'all':
            self.filter_campaign['campaign__slug'] = filter_campaign
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(team_count=Count('teams', distinct=True))
        return queryset

    def team_count(self, obj):
        return obj.team_count
    team_count.short_description = _('Počet týmů ve všech kampaních')
    team_count.admin_order_field = 'team_count'

    def user_count(self, obj):
        # TODO: Nejde řadit podle tohoto pole. Bylo by potřeba počet získat pomocí anotací, což je ale značně problematické.
        return obj.teams.filter(**self.filter_campaign).distinct().aggregate(Sum('member_count'))['member_count__sum']
    user_count.short_description = _('Počet soutěžících ve vyfiltrované kampani')

    def team_links(self, obj):
        return admin_links(
            [
                (reverse('admin:dpnk_team_change', args=(u.pk,)), str(u))
                for u in models.Team.objects.filter(subsidiary=obj)
            ],
        )
    team_links.short_description = _(u"Týmy")


class QuestionInline(SortableInlineAdminMixin, admin.TabularInline):
    model = models.Question
    form = models.QuestionForm
    extra = 0


@admin.register(models.Competition)
class CompetitionAdmin(FormRequestMixin, CityAdminMixin, ImportExportMixin, RelatedFieldAdmin):
    list_display = (
        'name',
        'slug',
        'competition_type',
        'competitor_type',
        'without_admission',
        'is_public',
        'public_answers',
        'show_results',
        'date_from',
        'date_to',
        'entry_after_beginning_days',
        'city_list',
        'sex',
        'company__name',
        'competition_results_link',
        'questionnaire_results_link',
        'questionnaire_link',
        'draw_link',
        'get_competitors_count',
        'url',
        'id')
    filter_horizontal = (
        'team_competitors',
        'company_competitors',
        'user_attendance_competitors',
        'city')
    search_fields = ('name', 'company__name', 'slug')
    list_filter = (
        CampaignFilter,
        'city',
        'without_admission',
        'is_public',
        'public_answers',
        'show_results',
        'competitor_type',
        'competition_type',
        IsForCompanyFilter,
        'sex')
    save_as = True
    actions = [actions.recalculate_competitions_results, actions.normalize_questionnqire_admissions]
    inlines = [QuestionInline, ]
    prepopulated_fields = {'slug': ('name',)}
    list_max_show_all = 10000
    form = models.CompetitionForm

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ['competition_results_link', 'questionnaire_results_link', 'draw_link']
        return [
            'competition_results_link',
            'questionnaire_results_link',
            'url',
            'draw_link',
            'date_to',
            'date_from',
            'company',
            'without_admission',
            'public_answers',
            'is_public',
            'entry_after_beginning_days',
            'team_competitors',
            'company_competitors',
            'user_attendance_competitors',
            'campaign',
        ]

    def city_list(self, obj):
        return ", ".join([str(c) for c in obj.city.all()])

    def competition_results_link(self, obj):
        if obj.slug:
            return format_html(u'<a href="{}">výsledky</a>', (reverse('competition_results', kwargs={'competition_slug': obj.slug})))
    competition_results_link.short_description = _(u"Výsledky soutěže")

    def questionnaire_results_link(self, obj):
        if obj.competition_type == 'questionnaire' and obj.slug:
            return format_html(u'<a href="{}">odpovědi</a>', (reverse('admin_questionnaire_results', kwargs={'competition_slug': obj.slug})))
    questionnaire_results_link.short_description = _(u"Odpovědi")

    def questionnaire_link(self, obj):
        if obj.competition_type == 'questionnaire' and obj.slug:
            return format_html(u'<a href="{}">dotazník</a>', (reverse('questionnaire', kwargs={'questionnaire_slug': obj.slug})))
    questionnaire_link.short_description = _(u"Dotazník")

    def draw_link(self, obj):
        if obj.competition_type == 'frequency' and obj.competitor_type == 'team' and obj.slug:
            return format_html(u'<a href="{}">losovani</a>', (reverse('admin_draw_results', kwargs={'competition_slug': obj.slug})))
    draw_link.short_description = _(u"Losování")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "team_competitors":
            kwargs["queryset"] = models.Team.objects.none()

        if db_field.name == "user_attendance_competitors":
            kwargs["queryset"] = models.UserAttendance.objects.none()

        if db_field.name == "company_competitors":
            kwargs["queryset"] = models.Company.objects.none()
        return super(CompetitionAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)


class UserAttendanceForm(forms.ModelForm):
    class Meta:
        model = models.UserAttendance
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(UserAttendanceForm, self).__init__(*args, **kwargs)
        if 't_shirt_size' in self.fields:
            if hasattr(self.instance, 'campaign'):
                self.fields['t_shirt_size'].queryset = TShirtSize.objects.filter(campaign=self.instance.campaign)

    def clean(self):
        new_team = self.cleaned_data['team']
        new_approved_for_team = self.cleaned_data['approved_for_team']
        if new_team:
            new_member_count = new_team.members().exclude(pk=self.instance.pk).count()
            if new_approved_for_team == 'approved':
                new_member_count += 1
            if self.instance.campaign.too_much_members(new_member_count):
                message = _("Tento tým není možné zvolit, protože by měl příliš mnoho odsouhlasených členů.")
                self.add_error("team", message)
                self.add_error("approved_for_team", message)
        return super().clean()


class UserAttendanceInline(NestedTabularInline):
    model = models.UserAttendance
    form = UserAttendanceForm
    extra = 0
    list_max_show_all = 10000
    raw_id_fields = ('team',)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['telephone'].required = False


class CompanyAdminInline(NestedTabularInline):
    raw_id_fields = ('administrated_company',)
    extra = 0
    model = models.CompanyAdmin


class UserProfileAdminInline(NestedStackedInline):
    model = models.UserProfile
    form = UserProfileForm
    inlines = [UserAttendanceInline, CompanyAdminInline]
    filter_horizontal = ('administrated_cities',)


def create_userprofile_resource(campaign_slugs):
    campaign_fields = ["user_attended_%s" % sl for sl in campaign_slugs]

    class UserProileResource(resources.ModelResource):
        class Meta:
            model = models.UserProfile
            fields = [
                'name',
                'email',
                'sex',
                'telephone',
                'language',
                'mailing_id',
                'note',
                'ecc_password',
                'ecc_email',
            ] + campaign_fields
            export_order = fields

        name = fields.Field()

        def dehydrate_name(self, obj):
            return obj.name()

        email = fields.Field()

        def dehydrate_email(self, obj):
            return obj.user.email

        for slug in campaign_slugs:
            vars()['user_attended_%s' % slug] = fields.Field()

    for slug in campaign_slugs:
        def func(slug, obj):
            user_profile = obj.userattendance_set.filter(campaign__slug=slug)
            if user_profile.exists():
                return user_profile.get().payment_status
        setattr(UserProileResource, "dehydrate_user_attended_%s" % slug, types.MethodType(func, slug))

    return UserProileResource


@admin.register(models.UserProfile)
class UserProfileAdmin(ExportMixin, admin.ModelAdmin):
    list_display = (
        'user',
        '__str__',
        'sex',
        'telephone',
        'language',
        'mailing_id',
        'note',
        'ecc_password',
        'ecc_email',
        'user_attendances_count',
        'occupation',
        'age_group',
    )
    inlines = (CompanyAdminInline,)
    list_filter = (
        campaign_filter_generator('userattendance_set__campaign'),
        'language',
        'sex',
        'userattendance_set__team__subsidiary__city',
        'userattendance_set__approved_for_team',
        'occupation',
        'age_group',
    )
    filter_horizontal = ('administrated_cities',)
    search_fields = [
        'nickname',
        'user__first_name',
        'user__last_name',
        'user__username',
        'user__email',
        'ecc_password',
        'ecc_email',
    ]
    readonly_fields = (
        'ecc_password',
        'ecc_email',
    )
    actions = (actions.remove_mailing_id,)

    @property
    def resource_class(self):
        return create_userprofile_resource(models.Campaign.objects.values_list("slug", flat=True))

    def lookup_allowed(self, key, value):
        if key in ('userattendance_set__team__subsidiary__city__id__exact',):
            return True
        return super().lookup_allowed(key, value)

    def get_queryset(self, request):
        return models.UserProfile.objects.annotate(userattendance_count=Count('userattendance_set'))

    def user_attendances_count(self, obj):
        return obj.userattendance_set.count()
    user_attendances_count.admin_order_field = "userattendance_count"


admin.site.unregister(models.User)


@admin.register(models.User)
class UserAdmin(RelatedFieldAdmin, ExportMixin, NestedModelAdmin, UserAdmin):
    inlines = (UserProfileAdminInline,)
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'userprofile__telephone',
        'date_joined',
        'is_active',
        'last_login',
        'userprofile_administrated_cities',
        'id',
    )
    search_fields = ['first_name', 'last_name', 'username', 'email', 'userprofile__company_admin__administrated_company__name', ]
    list_filter = [
        'userprofile__userattendance_set__campaign',
        'is_staff',
        'is_superuser',
        'is_active',
        'groups',
        'userprofile__company_admin__company_admin_approved',
        HasUserprofileFilter,
        'userprofile__sex',
        'userprofile__administrated_cities',
        EmailFilter,
    ]
    readonly_fields = ['password']
    list_max_show_all = 10000

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('userprofile')

    def userprofile_administrated_cities(self, obj):
        return ", ".join([str(c) for c in obj.userprofile.administrated_cities.all()])


class TripAdminInline(admin.TabularInline):
    list_display = ('user_attendance', 'date', 'distance', 'direction', 'commute_mode', 'id')
    raw_id_fields = ('user_attendance',)
    extra = 0
    model = models.Trip


class UserAttendanceResource(resources.ModelResource):
    class Meta:
        model = models.UserAttendance
        fields = (
            'id',
            'campaign__slug',
            'distance',
            'team__id',
            'team__name',
            'approved_for_team',
            't_shirt_size__name',
            'team__subsidiary__city__name',
            'userprofile__language',
            'userprofile__telephone',
            'userprofile__user__id',
            'userprofile__user__first_name',
            'userprofile__user__last_name',
            'userprofile__user__username',
            'userprofile__user__email',
            'userprofile__occupation',
            'userprofile__age_group',
            'subsidiary_name',
            'team__subsidiary__company__name',
            'created')
        export_order = fields

    subsidiary_name = fields.Field()

    def dehydrate_subsidiary_name(self, obj):
        if obj.team and obj.team.subsidiary:
            return obj.team.subsidiary.name()

    payment_date = fields.Field()

    def dehydrate_payment_date(self, obj):
        payment = obj.representative_payment
        if payment:
            return payment.realized or payment.created

    payment_status = fields.Field()

    def dehydrate_payment_status(self, obj):
        return obj.payment_status

    payment_type = fields.Field()

    def dehydrate_payment_type(self, obj):
        payment = obj.representative_payment
        if payment:
            return payment.pay_type

    payment_amount = fields.Field()

    def dehydrate_payment_amount(self, obj):
        payment = obj.representative_payment
        if payment:
            return payment.amount


@admin.register(models.UserAttendance)
class UserAttendanceAdmin(RelatedFieldAdmin, ExportMixin, city_admin_mixin_generator('team__subsidiary__city__in'), LeafletGeoAdmin):
    list_display = (
        'id',
        'name_for_trusted',
        'userprofile__user__email',
        'userprofile__telephone',
        'distance',
        'team__name',
        'team__subsidiary',
        'team__subsidiary__city',
        'team__subsidiary__company',
        'approved_for_team',
        'campaign__name',
        't_shirt_size',
        'payment_status',
        'representative_payment__pay_type',
        'representative_payment__status',
        'representative_payment__amount',
        'team__member_count',
        'get_distance',
        'frequency',
        'trip_length_total',
        'get_rides_count_denorm',
        'created')
    list_filter = (
        CampaignFilter,
        ('team__subsidiary__city', RelatedFieldCheckBoxFilter),
        ('approved_for_team', AllValuesComboFilter),
        ('t_shirt_size', RelatedFieldComboFilter),
        'userprofile__user__is_active',
        'userprofile__mailing_opt_in',
        'representative_payment__pay_type',
        'representative_payment__status',
        'representative_payment__amount',
        'payment_status',
        ('team__member_count', AllValuesComboFilter),
        ('transactions__packagetransaction__team_package__box__delivery_batch', RelatedFieldComboFilter),
        ('userprofile__sex', AllValuesComboFilter),
        TrackFilter,
        HasVoucherFilter,
        HasRidesFilter,
        HasTeamFilter,
    )
    raw_id_fields = ('userprofile', 'team', 'discount_coupon')
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
        'team__subsidiary__address_district',
        'team__subsidiary__company__name',
    )
    readonly_fields = (
        'user_link',
        'userprofile__user__email',
        'created',
        'updated',
    )
    actions = (
        actions.update_mailing,
        actions.approve_am_payment,
        actions.recalculate_results,
        actions.show_distance,
        actions.assign_vouchers,
        actions.touch_items,
    )
    form = UserAttendanceForm
    inlines = [PaymentInline, PackageTransactionInline, UserActionTransactionInline, TripAdminInline]
    list_max_show_all = 10000
    list_per_page = 10
    resource_class = UserAttendanceResource

    def user_link(self, obj):
        return format_html('<a href="{}">{}</a>', reverse('admin:auth_user_change', args=(obj.userprofile.user.pk,)), obj.userprofile.user)
    user_link.short_description = _('Uživatel')

    def get_queryset(self, request):
        queryset = super(UserAttendanceAdmin, self).get_queryset(request)
        return queryset.length().select_related('team__subsidiary__city', 'team__subsidiary__company', 't_shirt_size').only(
            'approved_for_team',
            'campaign_id',
            'campaign__name',
            'created',
            'distance',
            'frequency',
            'get_rides_count_denorm',
            'id',
            'payment_status',
            'representative_payment__amount',
            'representative_payment__pay_type',
            'representative_payment__status',
            'team',
            'team__member_count',
            'team__name',
            'team__subsidiary',
            'team__subsidiary__address_city',
            'team__subsidiary__address_psc',
            'team__subsidiary__address_recipient',
            'team__subsidiary__address_street',
            'team__subsidiary__address_street_number',
            'team__subsidiary__city',
            'team__subsidiary__company',
            'track',
            'trip_length_total',
            't_shirt_size',
            't_shirt_size',
            't_shirt_size__name',
            't_shirt_size__price',
            'userprofile',
            'userprofile__nickname',
            'userprofile__sex',
            'userprofile__telephone',
            'userprofile__user__email',
            'userprofile__user__first_name',
            'userprofile__user__last_name',
            'userprofile__user__username',
        )


@admin.register(models.Team)
class TeamAdmin(ExportMixin, RelatedFieldAdmin):
    list_display = (
        'name',
        'subsidiary',
        'subsidiary__city',
        'subsidiary__company',
        'member_count',
        'campaign',
        'get_length',
        'get_frequency',
        'id',
    )
    search_fields = ['name', 'subsidiary__address_street', 'subsidiary__company__name']
    list_filter = [CampaignFilter, 'subsidiary__city', 'member_count']
    list_max_show_all = 10000
    raw_id_fields = ['subsidiary', ]
    actions = (
        actions.touch_items,
    )

    readonly_fields = ['members', 'invitation_token', 'member_count']

    def members(self, obj):
        return admin_links(
            [
                (reverse('admin:dpnk_userattendance_change', args=(u.pk,)), u, u.approved_for_team)
                for u in models.UserAttendance.objects.filter(team=obj)
            ],
        )
    members.short_description = _('Členové')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('campaign', 'subsidiary__company')


class TransactionChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.Transaction
    raw_id_fields = ('user_attendance',)
    readonly_fields = ('author', 'created', 'updated_by')


class PaymentChildAdmin(TransactionChildAdmin):
    form = transaction_forms.PaymentForm


class PackageTransactionChildAdmin(TransactionChildAdmin):
    readonly_fields = ['created', 'author', 'updated_by', 't_shirt_size']
    form = PackageTransactionForm


class CommonTransactionChildAdmin(TransactionChildAdmin):
    form = transaction_forms.CommonTransactionForm


class UserActionTransactionChildAdmin(TransactionChildAdmin):
    form = transaction_forms.UserActionTransactionForm


@admin.register(models.Transaction)
class TransactionAdmin(PolymorphicParentModelAdmin):
    list_display = ('id', 'user_attendance', 'created', 'status', 'polymorphic_ctype', 'user_link', 'author')
    search_fields = (
        'user_attendance__userprofile__nickname',
        'user_attendance__userprofile__user__first_name',
        'user_attendance__userprofile__user__last_name',
        'user_attendance__userprofile__user__username')
    list_filter = [campaign_filter_generator('user_attendance__campaign'), 'status', 'polymorphic_ctype', ]

    readonly_fields = ['user_link', ]

    def user_link(self, obj):
        if obj.user_attendance:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:auth_user_change', args=(obj.user_attendance.userprofile.user.pk,)),
                obj.user_attendance.userprofile.user,
            )
    user_link.short_description = _('Uživatel')

    base_model = models.Transaction
    child_models = (
        (models.Payment, PaymentChildAdmin),
        (PackageTransaction, PackageTransactionChildAdmin),
        (models.CommonTransaction, CommonTransactionChildAdmin),
        (models.UserActionTransaction, UserActionTransactionChildAdmin),
    )


@admin.register(models.Payment)
class PaymentAdmin(RelatedFieldAdmin):
    list_display = (
        'id',
        'user_attendance',
        'created',
        'realized',
        'status',
        'session_id',
        'trans_id',
        'amount',
        'pay_type',
        'error',
        'order_id',
        'author',
        'user_attendance__team__subsidiary__company__name')
    search_fields = (
        'user_attendance__userprofile__nickname',
        'user_attendance__userprofile__user__first_name',
        'user_attendance__userprofile__user__last_name',
        'user_attendance__userprofile__user__username',
        'session_id',
        'trans_id',
        'order_id',
        'user_attendance__team__subsidiary__company__name',
    )
    list_filter = [campaign_filter_generator('user_attendance__campaign'), 'status', 'error', 'pay_type', ]
    raw_id_fields = ('user_attendance',)
    readonly_fields = ('author', 'created', 'updated_by')
    list_max_show_all = 10000
    form = transaction_forms.PaymentForm


class ChoiceInline(SortableInlineAdminMixin, admin.TabularInline):
    model = models.Choice
    extra = 3


@admin.register(models.ChoiceType)
class ChoiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'competition', 'universal')
    inlines = [ChoiceInline]
    list_filter = (campaign_filter_generator('competition__campaign'), 'competition', )
    save_as = True


class AnswerResource(resources.ModelResource):
    class Meta:
        model = models.Answer
        fields = (
            'id',
            'user_attendance__userprofile__user__first_name',
            'user_attendance__userprofile__user__last_name',
            'user_attendance__userprofile__user__id',
            'user_attendance__team__name',
            'user_attendance__team__subsidiary__address_street',
            'user_attendance__team__subsidiary__address_street_number',
            'user_attendance__team__subsidiary__address_recipient',
            'user_attendance__team__subsidiary__address_district',
            'user_attendance__team__subsidiary__address_psc',
            'user_attendance__team__subsidiary__address_city',
            'user_attendance__team__subsidiary__company__name',
            'user_attendance__team__subsidiary__city__name',
            'question',
            'question__name',
            'question__text',
            'choices',
            'str_choices',
            'comment',
        )
        export_order = fields

    str_choices = fields.Field()

    def dehydrate_str_choices(self, obj):
        return obj.str_choices()


@admin.register(models.Answer)
class AnswerAdmin(ExportMixin, RelatedFieldAdmin):
    list_display = (
        'user_attendance',
        'user_attendance__userprofile__user__email',
        'points_given',
        'question__competition',
        'comment',
        'str_choices_ids',
        'str_choices',
        'attachment_url',
        'comment',
        'question__text')
    search_fields = (
        'user_attendance__userprofile__nickname',
        'user_attendance__userprofile__user__first_name',
        'user_attendance__userprofile__user__last_name',
        'question__text',
        'question__name',
        'question__competition__name',
        'user_attendance__team__subsidiary__company__name')
    list_filter = (campaign_filter_generator('question__competition__campaign'), HasReactionFilter, 'question__competition__city', 'question__competition')
    filter_horizontal = ('choices',)
    list_max_show_all = 100000
    raw_id_fields = ('user_attendance', 'question')
    resource_class = AnswerResource

    def attachment_url(self, obj):
        if obj.attachment:
            return format_html(u"<a href='{}'>{}</a>", obj.attachment.url, obj.attachment)


@admin.register(models.Question)
class QuestionAdmin(FormRequestMixin, city_admin_mixin_generator('competition__city__in'), ExportMixin, admin.ModelAdmin):
    form = models.QuestionForm
    list_display = ('__str__', 'text', 'question_type', 'order', 'date', 'competition', 'choice_type', 'answers_link', 'id', )
    ordering = ('order', 'date',)
    list_filter = (campaign_filter_generator('competition__campaign'), 'competition__city', 'competition',)
    search_fields = ('text', 'competition__name')
    save_as = True

    readonly_fields = ['choices', 'answers_link', ]

    def choices(self, obj):
        return mark_safe(
            "<br/>".join(
                [choice.text for choice in obj.choice_type.choices.all()]) +
            '<br/><a href="%s">edit</a>' % reverse('admin:dpnk_choicetype_change', args=(obj.choice_type.pk,)),
        )

    def answers_link(self, obj):
        if obj.pk:
            return format_html(string_concat('<a href="{}?question={}">', _('vyhodnocení odpovědí'), '</a>'), reverse('admin_answers'), obj.pk)


class GpxFileInline(admin.TabularInline):
    model = models.GpxFile
    raw_id_fields = ('user_attendance', 'trip')
    extra = 0


class TripResource(resources.ModelResource):
    class Meta:
        model = models.Trip
        fields = (
            'id',
            'user_attendance__userprofile__user__id',
            'user_attendance',
            'date',
            'direction',
            'commute_mode',
            'distance',
        )
        export_order = fields


@admin.register(models.Trip)
class TripAdmin(ExportMixin, RelatedFieldAdmin):
    list_display = (
        'user_attendance__name_for_trusted',
        'date',
        'direction',
        'commute_mode',
        'distance',
        'id')
    search_fields = (
        'user_attendance__userprofile__nickname',
        'user_attendance__userprofile__user__first_name',
        'user_attendance__userprofile__user__last_name',
        'user_attendance__userprofile__user__username',
        'user_attendance__team__subsidiary__company__name')
    raw_id_fields = ('user_attendance',)
    list_filter = (
        campaign_filter_generator('user_attendance__campaign'),
        'direction',
        'commute_mode',
        ('date', DateRangeFilter),
        'user_attendance__team__subsidiary__city',
    )
    actions = (actions.show_distance_trips,)
    list_max_show_all = 100000
    inlines = [GpxFileInline, ]
    resource_class = TripResource

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user_attendance__userprofile__user').only(
            'user_attendance',
            'date',
            'direction',
            'commute_mode',
            'distance',
            'user_attendance__userprofile__nickname',
            'user_attendance__userprofile__user__email',
            'user_attendance__userprofile__user__first_name',
            'user_attendance__userprofile__user__last_name',
            'user_attendance__userprofile__user__username',
        )


@admin.register(models.CompetitionResult)
class CompetitionResultAdmin(admin.ModelAdmin):
    list_display = ('user_attendance', 'team', 'company', 'result', 'result_divident', 'result_divisor', 'competition')
    list_filter = (campaign_filter_generator('competition__campaign'), 'competition',)
    search_fields = (
        'user_attendance__userprofile__nickname',
        'user_attendance__userprofile__user__first_name',
        'user_attendance__userprofile__user__last_name',
        'user_attendance__userprofile__user__username',
        'team__name',
        'competition__name')
    raw_id_fields = ('user_attendance', 'team')


@admin.register(models.Occupation)
class OccupationAdmin(ImportExportMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = ('name', )


class PhaseInline(admin.TabularInline):
    model = models.Phase
    extra = 0


class PriceLevelInline(admin.TabularInline):
    readonly_fields = ('created', 'author', 'updated_by')
    model = price_level_models.PriceLevel
    extra = 0


class CityInCampaignInline(admin.TabularInline):
    model = models.CityInCampaign
    extra = 0


class TShirtSizeInline(SortableInlineAdminMixin, admin.TabularInline):
    model = TShirtSize
    extra = 0


@admin.register(models.Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
        'mailing_list_id',
        'previous_campaign',
        'minimum_rides_base',
        'minimum_percentage',
        'trip_plus_distance',
        'mailing_list_enabled',
    )
    inlines = [
        TShirtSizeInline,
        PhaseInline,
        CityInCampaignInline,
        PriceLevelInline,
    ]
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('city_count',)
    save_as = True

    def city_count(self, obj):
        return obj.cityincampaign_set.count()


@admin.register(models.CompanyAdmin)
class CompanyAdminAdmin(city_admin_mixin_generator('administrated_company__subsidiaries__city'), RelatedFieldAdmin):
    list_display = [
        'userprofile__user',
        'userprofile__user__email',
        'userprofile',
        'userprofile__user__first_name',
        'userprofile__user__last_name',
        'userprofile__telephone',
        'company_admin_approved',
        'administrated_company__name',
        'can_confirm_payments',
        'note',
        'campaign',
    ]
    list_filter = [
        CampaignFilter,
        'company_admin_approved',
        HasUserAttendanceFilter,
        'administrated_company__subsidiaries__city',
    ]
    search_fields = [
        'administrated_company__name',
        'userprofile__nickname',
        'userprofile__user__first_name',
        'userprofile__user__last_name',
        'userprofile__user__username',
        'userprofile__user__email',
    ]
    raw_id_fields = ['userprofile']
    list_max_show_all = 100000
    actions = (actions.update_mailing_coordinator,)

    def lookup_allowed(self, key, value):
        if key in ('administrated_company__subsidiaries__city__id__exact',):
            return True
        return super().lookup_allowed(key, value)


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = models.Invoice
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(InvoiceForm, self).__init__(*args, **kwargs)
        self.fields['sequence_number'].required = False


class InvoiceResource(resources.ModelResource):
    class Meta:
        model = models.Invoice
        fields = (
            'company__name',
            'created',
            'exposure_date',
            'paid_date',
            'total_amount',
            'invoice_count',
            'campaign__name',
            'sequence_number',
            'order_number',
            'company__ico',
            'company__dic',
            'company_pais_benefitial_fee',
            'company__address_street',
            'company__address_street_number',
            'company__address_recipient',
            'company__address_district',
            'company__address_psc',
            'company__address_city')
        export_order = fields

    invoice_count = fields.Field()

    def dehydrate_invoice_count(self, obj):
        return obj.payment_set.count()


@admin.register(models.Invoice)
class InvoiceAdmin(ExportMixin, RelatedFieldAdmin):
    list_display = [
        'company',
        'created',
        'exposure_date',
        'paid_date',
        'total_amount',
        'invoice_count',
        'invoice_pdf_url',
        'campaign',
        'sequence_number',
        'order_number',
        'company__ico',
        'company__dic',
        'company_pais_benefitial_fee',
        'company_address',
    ]
    readonly_fields = ['created', 'author', 'updated_by', 'invoice_count']
    list_filter = [CampaignFilter, InvoicePaidFilter, 'company_pais_benefitial_fee']
    search_fields = ['company__name', ]
    inlines = [PaymentInline]
    actions = [actions.mark_invoices_paid]
    list_max_show_all = 10000
    form = InvoiceForm
    resource_class = InvoiceResource

    def company_address(self, obj):
        return obj.company.company_address()
    company_address.short_description = _(u"Adresa organizace")

    def invoice_count(self, obj):
        return obj.payment_set.count()
    invoice_count.short_description = _(u"Počet plateb")

    def invoice_pdf_url(self, obj):
        return format_html("<a href='{}'>invoice.pdf</a>", obj.invoice_pdf.url)


@admin.register(models.GpxFile)
class GpxFileAdmin(LeafletGeoAdmin):
    model = models.GpxFile
    list_display = (
        'id',
        'trip_date',
        'file',
        'direction',
        'trip',
        'user_attendance',
        'from_application',
        'created',
        'author',
        'updated_by',
        'created',
        'updated',
        'ecc_last_upload'
    )
    search_fields = (
        'user_attendance__userprofile__nickname',
        'user_attendance__userprofile__user__first_name',
        'user_attendance__userprofile__user__last_name',
        'user_attendance__userprofile__user__username')
    raw_id_fields = ('user_attendance', 'trip')
    readonly_fields = ('author', 'updated_by', 'updated', 'ecc_last_upload')
    list_filter = (campaign_filter_generator('user_attendance__campaign'), 'from_application', 'user_attendance__team__subsidiary__city')


@admin.register(models.Voucher)
class VoucherAdmin(ImportMixin, admin.ModelAdmin):
    list_display = ('id', 'voucher_type', 'token', 'user_attendance')
    raw_id_fields = ('user_attendance',)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    def _session_data(self, obj):
        return pprint.pformat(obj.get_decoded()).replace('\n', '<br>\n')
    _session_data.allow_tags = True
    list_display = ['session_key', '_session_data', 'expire_date']
    readonly_fields = ['_session_data']
    search_fields = ('session_key',)
    date_hierarchy = 'expire_date'


@admin.register(TaskMeta)
class TaskMetaAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'status', 'date_done', 'result_str', 'hidden')
    readonly_fields = ('result_str', 'date_done',)
    date_hierarchy = 'date_done'

    def result_str(self, obj):
        return str(obj.result)


# register all adminactions
admin.site.add_action(admin_actions.mass_update)
admin.site.add_action(admin_actions.merge)
