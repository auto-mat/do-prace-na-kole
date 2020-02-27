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

from admin_views.admin import AdminViews

try:
    from adminactions import actions as admin_actions, merge
except ImportError:
    pass

from adminfilters.filters import AllValuesComboFilter, RelatedFieldCheckBoxFilter, RelatedFieldComboFilter

from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin

from advanced_filters.admin import AdminAdvancedFiltersMixin

from avatar.templatetags.avatar_tags import avatar

from daterange_filter.filter import DateRangeFilter

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.sessions.models import Session
from django.db.models import Count, Sum, TextField
from django.forms import Textarea
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from import_export.admin import ExportMixin, ImportExportMixin, ImportMixin

from import_export_celery.admin_actions import create_export_job_action

from isnull_filter import isnull_filter

from leaflet.admin import LeafletGeoAdmin, LeafletGeoAdminMixin

try:
    from massadmin.massadmin import mass_change_selected
except ImportError:
    pass

from modeltranslation.admin import TranslationAdmin, TranslationTabularInline

from nested_admin import NestedModelAdmin, NestedStackedInline, NestedTabularInline

from polymorphic.admin import PolymorphicChildModelAdmin

from price_level import models as price_level_models

from related_admin import RelatedFieldAdmin

from rest_framework.authtoken.admin import TokenAdmin

from scribbler import models as scribbler_models

from smmapdfs.actions import make_pdfsandwich
from smmapdfs.admin_abcs import PdfSandwichAdmin, PdfSandwichFieldAdmin

from stale_notifications.admin_mixins import StaleSyncMixin

from t_shirt_delivery.admin import PackageTransactionInline
from t_shirt_delivery.forms import PackageTransactionForm
from t_shirt_delivery.models import TShirtSize

from . import actions, models, resources, transaction_forms
from .admin_mixins import CityAdminMixin, FormRequestMixin, city_admin_mixin_generator
from .filters import (
    ActiveCityFilter,
    CampaignFilter,
    EmailFilter,
    HasReactionFilter,
    ICOFilter,
    PSCFilter,
    campaign_filter_generator,
)


def admin_links(args_generator):
    return format_html_join(
        mark_safe('<br/>'),
        '<a href="{}">{}</a>',
        args_generator,
    )


class PaymentInline(admin.TabularInline):
    model = models.Payment
    extra = 0
    form = transaction_forms.PaymentForm
    readonly_fields = ['order_id', 'session_id', 'trans_id', 'error', 'author', 'updated_by']
    raw_id_fields = ['invoice', 'user_attendance']
    formfield_overrides = {
        TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }


class PaymentInlineUserAttendance(PaymentInline):
    fk_name = "user_attendance"


class UserActionTransactionInline(admin.TabularInline):
    model = models.UserActionTransaction
    extra = 0
    readonly_fields = ['user_attendance', 'author', 'updated_by']
    form = transaction_forms.UserActionTransactionForm
    formfield_overrides = {
        TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }


class TeamInline(admin.TabularInline):
    model = models.Team
    form = models.team.TeamAdminForm
    extra = 0
    readonly_fields = ['invitation_token', ]


class SubsidiaryInline(NestedTabularInline):
    model = models.Subsidiary
    extra = 0


@admin.register(models.City)
class CityAdmin(LeafletGeoAdmin):
    list_display = ('name', 'slug', 'cyklistesobe_slug', 'wp_slug', 'id', )
    prepopulated_fields = {'slug': ('name',), 'cyklistesobe_slug': ('name',)}
    list_filter = ('cityincampaign__campaign',)


@admin.register(models.CityInCampaign)
class CityInCampaignAdmin(RelatedFieldAdmin):
    list_display = (
        'name',
    )
    list_filter = (
        CampaignFilter,
    )
    actions = (
        make_pdfsandwich,
    )


@admin.register(models.CityInCampaignDiploma)
class CityInCampaignDiplomaAdmin(PdfSandwichAdmin):
    search_fields = (
        'obj__city__name',
    )


@admin.register(models.CityInCampaignDiplomaField)
class CityInCampaignDiplomaFieldAdmin(PdfSandwichFieldAdmin):
    list_filter = (
        'pdfsandwich_type__name',
    )


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
    allow_duplicate_ico = forms.BooleanField(
        label=_("Umožnit uložení duplicitního IČO"),
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        self.instance.allow_duplicate_ico = cleaned_data.get('allow_duplicate_ico', False)
        return cleaned_data

    class Meta:
        model = models.Company
        fields = "__all__"
        error_messages = {
            'ico': {'stdnum_format': models.company.ICO_ERROR_MESSAGE},
            'dic': {'stdnum_format': models.company.DIC_ERROR_MESSAGE},
        }


try:
    class CompanyMergeForm(DontValidateCompnayFieldsMixin, merge.MergeForm):
        def full_clean(self):
            super().full_clean()
            if 'address_psc' in self._errors:
                del self._errors['address_psc']
except NameError:
    pass


class CompanyAdminInline(NestedTabularInline):
    raw_id_fields = ('administrated_company', 'userprofile')
    extra = 0
    model = models.CompanyAdmin
    formfield_overrides = {
        TextField: {'widget': Textarea(attrs={'rows': 1, 'cols': 30})},
    }


@admin.register(models.Company)
class CompanyAdmin(city_admin_mixin_generator('subsidiaries__city__in'), ImportExportMixin, NestedModelAdmin):
    list_display = (
        'name',
        'subsidiaries_text',
        'ico',
        'dic',
        'address_street',
        'address_street_number',
        'address_recipient',
        'address_city',
        'address_psc',
        'id',
    )
    inlines = [SubsidiaryInline, CompanyAdminInline]
    list_filter = [
        "subsidiaries__teams__campaign",
        'subsidiaries__city',
        'active',
        ICOFilter,
    ]
    readonly_fields = [
        'subsidiary_links',
        'author',
        'updated_by',
    ]
    search_fields = (
        'name',
        'address_street',
        'address_street_number',
        'address_recipient',
        'address_city',
        'address_psc',
        'ico',
        'dic',
    )
    list_max_show_all = 10000
    form = CompanyForm
    try:
        merge_form = CompanyMergeForm
    except NameError:
        pass
    resource_class = resources.CompanyResource
    actions = (
        actions.create_invoices,
        create_export_job_action,
    )

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


@admin.register(models.Subsidiary)
class SubsidiaryAdmin(AdminAdvancedFiltersMixin, CityAdminMixin, ImportExportMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'company',
        'address_recipient',
        'address_street',
        'address_street_number',
        'address_city',
        'city',
        'address_psc',
        'user_count',
        'team_count',
    )
    list_editable = (
        'address_psc',
    )
    inlines = [TeamInline, ]
    list_filter = (
        campaign_filter_generator('teams__campaign'),
        PSCFilter,
        'city',
        'active',
        ActiveCityFilter,
    )
    search_fields = (
        'address_recipient',
        'company__name',
        'address_street',
        'address_street_number',
        'address_city',
        'address_psc',
    )
    advanced_filter_fields = (
        'company__name',
        'address_recipient',
        'address_street',
        'address_street_number',
        'address_city',
        'city',
        'address_psc',
    )
    raw_id_fields = ('company',)
    list_max_show_all = 10000
    save_as = True

    readonly_fields = ['team_links', ]

    @property
    def resource_class(self):
        return resources.create_subsidiary_resource(models.Campaign.objects.values_list("slug", flat=True))

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
        'priority',
        'competition_type',
        'competitor_type',
        'is_public',
        'public_answers',
        'show_results',
        'date_from',
        'date_to',
        'entry_after_beginning_days',
        'city_list',
        'sex',
        'commute_modes_list',
        'company__name',
        'competition_results_link',
        'questionnaire_results_link',
        'questionnaire_link',
        'draw_link',
        'get_competitors_count',
        'url',
        'id')
    filter_horizontal = (
        'city',
    )
    search_fields = ('name', 'company__name', 'slug')
    list_filter = (
        CampaignFilter,
        'city',
        'is_public',
        'public_answers',
        'show_results',
        'competitor_type',
        'competition_type',
        'commute_modes',
        isnull_filter('company', _("Není vnitrofiremní soutěž?")),
        'sex')
    save_as = True
    actions = [actions.recalculate_competitions_results]
    inlines = [QuestionInline, ]
    prepopulated_fields = {'slug': ('name',)}
    list_max_show_all = 10000
    form = models.CompetitionForm

    def get_readonly_fields(self, request, obj=None):
        if request.user.has_perm('dpnk.can_edit_all_cities'):
            return ['competition_results_link', 'questionnaire_results_link', 'draw_link']
        return [
            'competition_results_link',
            'questionnaire_results_link',
            'url',
            'draw_link',
            'date_to',
            'date_from',
            'company',
            'public_answers',
            'is_public',
            'entry_after_beginning_days',
            'campaign',
        ]

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


class UserAttendanceForm(forms.ModelForm):
    class Meta:
        model = models.UserAttendance
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 't_shirt_size' in self.fields:
            if hasattr(self.instance, 'campaign'):
                self.fields['t_shirt_size'].queryset = TShirtSize.objects.filter(campaign=self.instance.campaign)

    def clean(self):
        if 'team' in self.cleaned_data:  # if not in merge form
            new_team = self.cleaned_data['team']

            if self.instance.payment_status == 'done' and new_team is None:
                self.add_error(
                    "team",
                    _("Není možné odstranit tým učastníkovi kampaně, který již zaplatil"),
                )
        return super().clean()


class UserAttendanceInline(LeafletGeoAdminMixin, NestedTabularInline):
    model = models.UserAttendance
    form = UserAttendanceForm
    extra = 0
    list_max_show_all = 10000
    raw_id_fields = ('team', 'discount_coupon')
    map_width = '200px'
    map_height = '200px'


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['telephone'].required = False
        self.fields['sex'].required = False


class UserProfileAdminInline(NestedStackedInline):
    model = models.UserProfile
    form = UserProfileForm
    inlines = [UserAttendanceInline, CompanyAdminInline]
    filter_horizontal = ('administrated_cities',)


@admin.register(models.UserProfile)
class UserProfileAdmin(ImportExportMixin, NestedModelAdmin):
    form = UserProfileForm
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
        'telephone_opt_in',
        'mailing_opt_in',
        'default_rides_view',
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
    raw_id_fields = (
        'user',
    )
    actions = (actions.remove_mailing_id,)

    @property
    def resource_class(self):
        return resources.create_userprofile_resource(models.Campaign.objects.values_list("slug", flat=True))

    def lookup_allowed(self, key, value):
        if key in ('userattendance_set__team__subsidiary__city__id__exact',):
            return True
        return super().lookup_allowed(key, value)

    def get_queryset(self, request):
        return models.UserProfile.objects.annotate(
            userattendance_count=Count('userattendance_set'),
        ).select_related(
            'occupation',
            'user',
        )

    def user_attendances_count(self, obj):
        return obj.userattendance_count
    user_attendances_count.admin_order_field = "userattendance_count"


admin.site.unregister(models.User)


class UserForm(UserChangeForm):
    class Meta:
        model = models.User
        exclude = []

    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if email and models.User.objects.filter(email__iexact=email).exclude(username=username).count():
            raise forms.ValidationError(_('Tento e-mail je již v systému použit.'))
        return email

    def __init__(self, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        return ret_val


@admin.register(models.User)
class UserAdmin(RelatedFieldAdmin, ImportExportMixin, NestedModelAdmin, UserAdmin):
    inlines = (UserProfileAdminInline,)
    form = UserForm
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
        isnull_filter('userprofile', _("Nemá uživatelský profil?")),
        'userprofile__sex',
        'userprofile__administrated_cities',
        EmailFilter,
    ]
    list_max_show_all = 10000

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('userprofile')

    def userprofile_administrated_cities(self, obj):
        return ", ".join([str(c) for c in obj.userprofile.administrated_cities.all()])


class TripAdminInline(admin.TabularInline):
    fields = (
        'date',
        'direction',
        'commute_mode',
        'source_application',
        'from_application',
        'source_id',
        'distance',
        'duration',
    )
    raw_id_fields = ('user_attendance',)
    extra = 0
    model = models.Trip


@admin.register(models.UserAttendance)
class UserAttendanceAdmin(
    StaleSyncMixin,
    AdminAdvancedFiltersMixin,
    RelatedFieldAdmin,
    ImportExportMixin,
    city_admin_mixin_generator('team__subsidiary__city__in'),
    admin.ModelAdmin,
):
    list_display = (
        'avatar_small',
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
        't_shirt_size__name',
        'payment_status',
        'representative_payment__pay_type',
        'representative_payment__status',
        'representative_payment__amount',
        'representative_payment__realized',
        'team__member_count',
        'frequency',
        'trip_length_total',
        'get_rides_count_denorm',
        'created',
        'updated',
        'last_sync_time',
    )
    list_filter = (
        CampaignFilter,
        ('team__subsidiary__city', RelatedFieldCheckBoxFilter),
        ('approved_for_team', AllValuesComboFilter),
        't_shirt_size__name',
        'userprofile__user__is_active',
        'userprofile__mailing_opt_in',
        'userprofile__telephone_opt_in',
        'representative_payment__pay_type',
        'representative_payment__status',
        'representative_payment__amount',
        'payment_status',
        ('team__member_count', AllValuesComboFilter),
        ('transactions__packagetransaction__team_package__box__delivery_batch', RelatedFieldComboFilter),
        ('userprofile__sex', AllValuesComboFilter),
        'discount_coupon__coupon_type__name',
        'discount_coupon__discount',
        isnull_filter('voucher', _("Nemá přiřazené vouchery?")),
        isnull_filter('user_trips', _("Nemá žádné cesty?")),
        isnull_filter('team', _("Uživatel nemá zvolený tým?")),
    )
    advanced_filter_fields = (
        'campaign',
        'team__subsidiary__city',
        'approved_for_team',
        't_shirt_size',
        'userprofile__user__is_active',
        'userprofile__mailing_opt_in',
        'userprofile__telephone_opt_in',
        'representative_payment__pay_type',
        'representative_payment__status',
        'representative_payment__amount',
        ('representative_payment__realized', _('Datum realizace platby')),
        'payment_status',
        'team__member_count',
        ('t_shirt_size__ship', _('Posílá se triko?')),
        'transactions__packagetransaction__team_package__box__delivery_batch',
        'team',
        'userprofile__sex',
        'discount_coupon__coupon_type__name',
        'discount_coupon__discount',
        'team__subsidiary__company__name',
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
        'team__subsidiary__company__name',
    )
    readonly_fields = (
        'avatar_large',
        'user_link',
        'userprofile__user__email',
        'created',
        'updated',
        'payment_status',
    )
    exclude = (
        'track',
        'dont_want_insert_track',
    )
    actions = (
        actions.update_mailing,
        actions.approve_am_payment,
        actions.recalculate_results,
        actions.show_distance,
        actions.assign_vouchers,
        actions.touch_items,
        actions.send_notifications,
        make_pdfsandwich,
    )
    form = UserAttendanceForm
    inlines = [PaymentInlineUserAttendance, PackageTransactionInline, UserActionTransactionInline, TripAdminInline]
    list_max_show_all = 10000
    list_per_page = 100
    resource_class = resources.UserAttendanceResource

    def avatar_small(self, obj):
        return avatar(obj.userprofile.user, 30)

    def avatar_large(self, obj):
        return avatar(obj.userprofile.user, 150)

    def user_link(self, obj):
        return format_html('<a href="{}">{}</a>', reverse('admin:auth_user_change', args=(obj.userprofile.user.pk,)), obj.userprofile.user)
    user_link.short_description = _('Uživatel')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'team__subsidiary__city',
            'team__subsidiary__company',
            't_shirt_size__campaign',
        ).only(
            'approved_for_team',
            'campaign__name',
            'campaign_id',
            'created',
            'distance',
            'frequency',
            'get_rides_count_denorm',
            'id',
            'last_sync_time',
            'payment_status',
            'representative_payment__amount',
            'representative_payment__pay_type',
            'representative_payment__realized',
            'representative_payment__status',
            't_shirt_size',
            't_shirt_size__campaign__slug',
            't_shirt_size__name',
            't_shirt_size__name_cs',
            't_shirt_size__name_en',
            't_shirt_size__price',
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
            'trip_length_total',
            'updated',
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
class TeamAdmin(ImportExportMixin, RelatedFieldAdmin):
    list_display = (
        'name',
        'subsidiary',
        'subsidiary__city',
        'subsidiary__company',
        'member_count',
        'paid_member_count',
        'campaign',
        'get_length',
        'get_frequency',
        'id',
    )
    search_fields = ['name', 'subsidiary__address_street', 'subsidiary__company__name']
    list_filter = [CampaignFilter, 'subsidiary__city', 'member_count', 'paid_member_count']
    list_max_show_all = 10000
    raw_id_fields = ['subsidiary', ]
    actions = (
        actions.touch_items,
        make_pdfsandwich,
    )
    form = models.team.TeamAdminForm

    readonly_fields = [
        'members',
        'invitation_token',
        'member_count',
        'paid_member_count',
        'author',
        'updated_by',
    ]

    def members(self, obj):
        return admin_links(
            [
                (reverse('admin:dpnk_userattendance_change', args=(u.pk,)), "%s - %s" % (u, u.approved_for_team))
                for u in obj.users.all()
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


class UserActionTransactionChildAdmin(TransactionChildAdmin):
    form = transaction_forms.UserActionTransactionForm


@admin.register(models.Payment)
class PaymentAdmin(ImportExportMixin, RelatedFieldAdmin):
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
        'invoice',
        'user_attendance__team__subsidiary__company__name',
    )
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
    raw_id_fields = (
        'user_attendance',
        'invoice',
    )
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


class AnswerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'instance' in kwargs and kwargs['instance']:
            self.fields['choices'].queryset = models.Choice.objects.filter(choice_type__question=kwargs['instance'].question)
        else:
            self.fields['choices'].queryset = models.Choice.objects.filter(choice_type__question__competition__campaign__slug=self.request.subdomain)


@admin.register(models.Answer)
class AnswerAdmin(FormRequestMixin, ImportExportMixin, RelatedFieldAdmin):
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
        'user_attendance__userprofile__user__email',
        'question__text',
        'question__name',
        'question__competition__name',
        'user_attendance__team__subsidiary__company__name')
    list_filter = (
        campaign_filter_generator('question__competition__campaign'),
        HasReactionFilter,
        'question__competition__city',
        'question__competition',
    )
    filter_horizontal = ('choices',)
    list_max_show_all = 100000
    raw_id_fields = ('user_attendance', 'question')
    save_as = True
    resource_class = resources.AnswerResource
    form = AnswerForm

    def attachment_url(self, obj):
        if obj.attachment:
            return format_html(u"<a href='{}'>{}</a>", obj.attachment.url, obj.attachment)


@admin.register(models.Question)
class QuestionAdmin(FormRequestMixin, city_admin_mixin_generator('competition__city__in'), ImportExportMixin, AdminViews, admin.ModelAdmin):
    admin_views = (
        (_('Spravovat otázky'), '/admin/questions'),
    )

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
            return format_html('<a href="{}?question={}">{}</a>', reverse('admin_answers'), _('vyhodnocení odpovědí'), obj.pk)


class GpxFileInline(LeafletGeoAdminMixin, admin.TabularInline):
    model = models.GpxFile
    raw_id_fields = (
        'user_attendance',
        'trip',
    )
    readonly_fields = (
        'author',
        'created',
        'updated_by',
    )
    exclude = (
        'ecc_last_upload',
    )
    extra = 0


@admin.register(models.Trip)
class TripAdmin(CityAdminMixin, ExportMixin, RelatedFieldAdmin, LeafletGeoAdmin):
    queryset_city_param = 'user_attendance__team__subsidiary__city__in'
    list_display = (
        'user_attendance__name_for_trusted',
        'date',
        'direction',
        'commute_mode',
        'source_application',
        'from_application',
        'source_id',
        'distance',
        'duration',
        'id')
    search_fields = (
        'user_attendance__userprofile__nickname',
        'user_attendance__userprofile__user__first_name',
        'user_attendance__userprofile__user__last_name',
        'user_attendance__userprofile__user__username',
        'user_attendance__userprofile__user__email',
        'user_attendance__team__subsidiary__company__name',
    )
    raw_id_fields = ('user_attendance',)
    list_filter = (
        campaign_filter_generator('user_attendance__campaign'),
        'direction',
        'commute_mode',
        ('date', DateRangeFilter),
        'user_attendance__team__subsidiary__city',
        'from_application',
        'source_application',
        'user_attendance__payment_status',
    )
    readonly_fields = ('created', 'author', 'updated_by')
    actions = (actions.show_distance_trips,)
    list_max_show_all = 100000
    inlines = [GpxFileInline, ]
    resource_class = resources.TripResource
    save_as = True

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'commute_mode',
            'user_attendance__userprofile__user',
        ).only(
            'commute_mode',
            'date',
            'direction',
            'distance',
            'duration',
            'from_application',
            'source_application',
            'source_id',
            'user_attendance',
            'user_attendance__team',
            'user_attendance__userprofile__nickname',
            'user_attendance__userprofile__user__email',
            'user_attendance__userprofile__user__first_name',
            'user_attendance__userprofile__user__last_name',
            'user_attendance__userprofile__user__username',
        )


@admin.register(models.CompetitionResult)
class CompetitionResultAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'user_attendance',
        'team',
        'company',
        'result',
        'result_divident',
        'result_divisor',
        'competition',
        'created',
        'updated',
    )
    list_filter = (campaign_filter_generator('competition__campaign'), 'competition',)
    search_fields = (
        'user_attendance__userprofile__nickname',
        'user_attendance__userprofile__user__first_name',
        'user_attendance__userprofile__user__last_name',
        'user_attendance__userprofile__user__username',
        'user_attendance__userprofile__user__email',
        'team__name',
        'competition__name')
    raw_id_fields = ('user_attendance', 'team')
    resource_class = resources.AdminCompetitionResultResource


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


class TShirtSizeInline(SortableInlineAdminMixin, TranslationTabularInline):
    model = TShirtSize
    extra = 0


@admin.register(models.CampaignType)
class CampaignTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
    )


@admin.register(models.Campaign)
class CampaignAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = (
        'year',
        'campaign_type',
        'slug',
        'slug_identifier',
        'mailing_list_id',
        'previous_campaign',
        'minimum_rides_base',
        'minimum_percentage',
        'trip_plus_distance',
        'mailing_list_enabled',
    )
    fieldsets = (
        ('Basic settings', {
            'fields': (
                'campaign_type',
                'year',
                'slug',
                'slug_identifier',
                'main_color',
                'previous_campaign',
                'sitetree_postfix',
                'language_prefixes',
            ),
        }),
        ('Communications', {
            'fields': (
                'email_footer',
                'mailing_list_id',
                'mailing_list_type',
                'mailing_list_enabled',
            ),
        }),
        ('Sign up and payment', {
            'fields': (
                'extra_agreement_text',
                'benefitial_admission_fee',
                'benefitial_admission_fee_company',
                'free_entry_cases_html',
                'invoice_sequence_number_first',
                'invoice_sequence_number_last',
                'club_membership_integration',
            ),
        }),
        ('Trip entry', {
            'fields': (
                'days_active',
                'tracks',
                'recreational',
                'show_application_links',
                'minimum_rides_base',
                'minimum_percentage',
                'trip_plus_distance',
            ),
        }),
        ('Teams', {
            'fields': (
                'max_team_members',
            ),
        }),
        ('Diplomas', {
            'fields': (
                'sandwich_type',
                'team_diploma_sandwich_type',
                'city_in_campaign_diploma_sandwich_type',
            ),
        }),
        ('Packages and t-shirts', {
            'fields': (
                'tracking_number_first',
                'tracking_number_last',
                'package_height',
                'package_width',
                'package_depth',
                'package_max_count',
                'package_weight',
            ),
        }),
        ('External API', {
            'fields': (
                'wp_api_date_from',
            ),
        }),
    )
    inlines = [
        TShirtSizeInline,
        PhaseInline,
        CityInCampaignInline,
        PriceLevelInline,
    ]
    readonly_fields = (
        'name',
        'city_count',
    )
    save_as = True

    def city_count(self, obj):
        return obj.cityincampaign_set.count()


@admin.register(models.CompanyAdmin)
class CompanyAdminAdmin(ImportExportMixin, city_admin_mixin_generator('administrated_company__subsidiaries__city__in'), RelatedFieldAdmin):
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
        'will_pay_opt_in',
        'note',
        'motivation_company_admin',
        'campaign',
    ]
    list_filter = [
        CampaignFilter,
        'company_admin_approved',
        isnull_filter('userattendance', _("Nemá účast v kampani?")),
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
    actions = (
        actions.update_mailing_coordinator,
    )
    resource_class = resources.CompanyAdminResource

    def lookup_allowed(self, key, value):
        if key in ('administrated_company__subsidiaries__city__id__exact',):
            return True
        return super().lookup_allowed(key, value)


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = models.Invoice
        fields = "__all__"
        widgets = {
            'note': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'sequence_number' in self.fields:
            self.fields['sequence_number'].required = False


@admin.register(models.Invoice)
class InvoiceAdmin(StaleSyncMixin, ExportMixin, RelatedFieldAdmin):
    list_display = [
        'company',
        'exposure_date',
        'payback_date',
        'paid_date',
        'variable_symbol',
        'total_amount',
        'payments_count',
        'invoice_pdf_url',
        'invoice_xml_url',
        'campaign',
        'sequence_number',
        'order_number',
        'company_ico',
        'company_dic',
        'company_pais_benefitial_fee',
        'company_address_street',
        'note',
        'company_admin_telephones',
        'company_admin_emails',
    ]
    list_editable = (
        'note',
    )
    readonly_fields = [
        'created',
        'author',
        'updated_by',
        'payments_count',
    ]
    raw_id_fields = [
        'company',
    ]
    list_filter = [
        CampaignFilter,
        isnull_filter('paid_date', _("Nezaplacené faktury")),
        'company_pais_benefitial_fee',
        isnull_filter('fio_payments'),
    ]
    search_fields = [
        'company__name',
        'variable_symbol',
        'company_ico',
        'company_dic',
        'sequence_number',
        'total_amount',
    ]
    inlines = [PaymentInline]
    actions = [
        actions.mark_invoices_paid,
        actions.invoice_pdf_batch_download,
        actions.invoice_xml_batch_download,
        actions.send_invoice_notifications,
    ]
    list_max_show_all = 10000
    form = InvoiceForm
    resource_class = resources.InvoiceResource

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            payments_count=Count('payment_set'),
        )

    def get_changelist_form(self, request, **kwargs):
        return InvoiceForm

    def invoice_pdf_url(self, obj):
        if obj.invoice_pdf:
            return format_html("<a href='{}'>invoice.pdf</a>", obj.invoice_pdf.url)

    def invoice_xml_url(self, obj):
        if obj.invoice_xml:
            return format_html("<a href='{}'>invoice.xml</a>", obj.invoice_xml.url)


@admin.register(scribbler_models.Scribble)
class ScribbleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug',
        'url',
        'content',
    )
    search_fields = (
        'name',
        'slug',
        'url',
    )
    save_as = True


@admin.register(models.Voucher)
class VoucherAdmin(ImportMixin, admin.ModelAdmin):
    list_display = ('id', 'voucher_type', 'token', 'user_attendance', 'campaign')
    raw_id_fields = ('user_attendance',)
    list_filter = [CampaignFilter, 'voucher_type', isnull_filter('user_attendance', _("Nemá účast v kampani"))]


@admin.register(models.LandingPageIcon)
class LandingPageIconAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('role', 'file', 'min_frequency', 'max_frequency')
    list_editable = ('min_frequency', 'max_frequency')


@admin.register(models.CommuteMode)
class CommuteModeAdmin(SortableAdminMixin, TranslationAdmin):  # ImportExportMixin was removed, because it prevented ordering
    list_display = (
        'name',
        'slug',
        'does_count',
        'eco',
    )


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    def _session_data(self, obj):
        return pprint.pformat(obj.get_decoded()).replace('\n', '<br>\n')
    _session_data.allow_tags = True
    list_display = ['session_key', '_session_data', 'expire_date']
    readonly_fields = ['_session_data']
    search_fields = ('session_key',)
    date_hierarchy = 'expire_date'


TokenAdmin.raw_id_fields = ('user',)
TokenAdmin.search_fields = (
    'user__email',
    'user__first_name',
    'user__last_name',
    'user__username',
    'key',
)


# register all adminactions
try:
    admin.site.add_action(admin_actions.merge)
    # This is fix for massadmin not adding itself automatically
    admin.site.add_action(mass_change_selected)
except NameError:
    pass


@admin.register(models.Diploma)
class DiplomaAdmin(PdfSandwichAdmin):
    search_fields = (
        'obj__userprofile__user__first_name',
        'obj__userprofile__user__last_name',
    )


@admin.register(models.DiplomaField)
class DiplomaFieldAdmin(PdfSandwichFieldAdmin):
    list_filter = (
        'pdfsandwich_type__name',
    )


@admin.register(models.TeamDiploma)
class TeamDiplomaAdmin(PdfSandwichAdmin):
    search_fields = (
        'obj__name',
    )


@admin.register(models.TeamDiplomaField)
class TeamDiplomaFieldAdmin(PdfSandwichFieldAdmin):
    pass
