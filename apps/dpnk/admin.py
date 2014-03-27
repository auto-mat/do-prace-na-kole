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

# Django imports
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import SimpleListFilter
from django.db.models import F, Sum, Count, Q
from django.utils.safestring import mark_safe
from admin_enhancer.admin import EnhancedModelAdminMixin, EnhancedAdminMixin
from dpnk.wp_urls import wp_reverse
from nested_inlines.admin import NestedModelAdmin, NestedStackedInline, NestedTabularInline
from adminsortable.admin import SortableInlineAdminMixin
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin
from import_export.admin import ImportExportModelAdmin
from django.utils.translation import ugettext_lazy as _
import datetime
# Models
from dpnk import models, mailing
from django import forms
import dpnk


class PaymentInline(EnhancedAdminMixin, NestedTabularInline):
    model = models.Payment
    extra = 0
    form = models.PaymentForm
    readonly_fields = ['user_attendance', 'order_id', 'session_id', 'trans_id', 'error', 'author', 'updated_by']


class PackageTransactionInline(EnhancedAdminMixin, NestedTabularInline):
    model = models.PackageTransaction
    extra = 0
    readonly_fields = ['author', 'updated_by', 'tracking_number', 't_shirt_size']
    raw_id_fields = ['user_attendance', ]
    form = models.PackageTransactionForm


class CommonTransactionInline(EnhancedAdminMixin, NestedTabularInline):
    model = models.CommonTransaction
    extra = 0
    readonly_fields = ['user_attendance', 'author', 'updated_by']
    form = models.CommonTransactionForm


class UserActionTransactionInline(EnhancedAdminMixin, NestedTabularInline):
    model = models.UserActionTransaction
    extra = 0
    readonly_fields = ['user_attendance']
    form = models.UserActionTransactionForm


class TeamInline(EnhancedAdminMixin, admin.TabularInline):
    model = models.Team
    form = models.TeamForm
    extra = 0
    readonly_fields = ['invitation_token', ]
    raw_id_fields = ('coordinator_campaign', )


class SubsidiaryInline(EnhancedAdminMixin, admin.TabularInline):
    model = models.Subsidiary
    extra = 0


class CityAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'id', )
    filter_horizontal = ('city_admins',)
    prepopulated_fields = {'slug': ('name',)}


class CompanyAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'subsidiaries_text', 'ico', 'user_count', 'address_street', 'address_street_number', 'address_recipient', 'address_psc', 'address_city', 'id', )
    inlines = [SubsidiaryInline, ]
    readonly_fields = ['subsidiary_links']
    search_fields = ('name',)
    list_max_show_all = 10000

    def queryset(self, request):
        return models.Company.objects.annotate(user_count=Sum('subsidiaries__teams__member_count'))

    def user_count(self, obj):
        return obj.user_count
    user_count.admin_order_field = 'user_count'

    #this is quick addition for 2013 invoices
    def invoice_count(self, obj):
        return len([
            user for user in models.UserAttendance.objects.filter(team__subsidiary__company=obj)
            if user.payment()['payment'] and user.payment()['payment'].pay_type == 'fc' and user.payment()['payment'].status in models.Payment.done_statuses])

    #def company_admin__user__email(self, obj):
    #   return obj.company_admin.get().user.email

    def subsidiaries_text(self, obj):
        return mark_safe(" | ".join(
            ['%s' % (str(u)) for u in models.Subsidiary.objects.filter(company=obj)]))
    subsidiaries_text.short_description = 'Pobočky'

    def subsidiary_links(self, obj):
        return mark_safe(
            "<br/>".join(
                ['<a href="' + wp_reverse('admin') + 'dpnk/subsidiary/%d">%s</a>' % (u.id, str(u))
                    for u in models.Subsidiary.objects.filter(company=obj)]))
    subsidiary_links.short_description = 'Pobočky'


class SubsidiaryAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('__unicode__', 'company', 'city', 'teams_text', 'id', )
    inlines = [TeamInline, ]
    list_filter = ['city']
    search_fields = ('address_recipient', 'company__name', 'address_street', )
    raw_id_fields = ('company',)

    readonly_fields = ['team_links', ]

    def teams_text(self, obj):
        return mark_safe(
            " | ".join([
                '%s' % (str(u)) for u in models.Team.objects.filter(subsidiary=obj)]))
    teams_text.short_description = 'Týmy'

    def team_links(self, obj):
        return mark_safe(
            "<br/>".join(
                ['<a href="' + wp_reverse('admin') + 'dpnk/team/%d">%s</a>' % (u.id, str(u))
                    for u in models.Team.objects.filter(subsidiary=obj)]))
    team_links.short_description = u"Týmy"


def recalculate_competitions_results(modeladmin, request, queryset):
    for competition in queryset.all():
        competition.recalculate_results()
recalculate_competitions_results.short_description = "Přepočítat výsledku vybraných soutěží"


class CompetitionAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'slug', 'type', 'competitor_type', 'without_admission', 'is_public', 'date_from', 'date_to', 'city', 'company', 'competition_results_link', 'questionnaire_results_link', 'draw_link', 'id')
    filter_horizontal = ('user_attendance_competitors', 'team_competitors', 'company_competitors')
    search_fields = ('name',)
    actions = [recalculate_competitions_results]

    readonly_fields = ['competition_results_link', 'questionnaire_results_link', 'draw_link']

    def competition_results_link(self, obj):
        return mark_safe(u'<a href="%s?soutez=%s">výsledky</a>' % (wp_reverse('vysledky_souteze'), obj.slug))
    competition_results_link.short_description = u"Výsledky soutěže"

    def questionnaire_results_link(self, obj):
        if obj.type == 'questionnaire':
            return mark_safe(u'<a href="%s%s">odpovědi</a>' % (wp_reverse('dotaznik'), obj.slug))
    questionnaire_results_link.short_description = u"Odpovědi"

    def draw_link(self, obj):
        if obj.type == 'frequency' and obj.competitor_type == 'team':
            return mark_safe(u'<a href="%slosovani/%s">losovani</a>' % (wp_reverse('admin'), obj.slug))
    draw_link.short_description = u"Losování"


class PaymentFilter(SimpleListFilter):
    title = u"stav platby"
    parameter_name = u'payment_state'

    def lookups(self, request, model_admin):
        return (
            ('not_paid', u'nezaplaceno'),
            ('not_paid_older', u'nezaplaceno (platba starší než 5 dnů)'),
            ('no_admission', u'neplatí se'),
            ('done', u'vyřízeno'),
            ('paid', u'zaplaceno'),
            ('waiting', u'čeká se'),
            ('unknown', u'neznámý'),
            ('none', u'bez plateb'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'not_paid_older':
            paying_or_prospective_user_ids = [p.user_attendance_id for p in models.Payment.objects.filter(
                Q(status=models.Payment.Status.DONE) | Q(
                    # Bank transfer less than 5 days old
                    status=models.Payment.Status.NEW, pay_type='bt',
                    created__gt=datetime.datetime.now() - datetime.timedelta(days=5))
                ).distinct()]
            return queryset.filter(
                userprofile__user__is_active=True).exclude(id__in=paying_or_prospective_user_ids).exclude(team__subsidiary__city__cityincampaign__admission_fee=0).distinct()
        elif self.value() == 'not_paid':
            return queryset.filter(
                userprofile__user__is_active=True).exclude(transactions__status__in=models.Payment.done_statuses).exclude(team__subsidiary__city__cityincampaign__admission_fee=0).distinct()
        elif self.value() == 'no_admission':
            return queryset.filter(team__subsidiary__city__cityincampaign__admission_fee=0).distinct()
        elif self.value() == 'done':
            return queryset.filter(Q(transactions__status__in=models.Payment.done_statuses) | Q(team__subsidiary__city__cityincampaign__admission_fee=0)).distinct()
        elif self.value() == 'paid':
            return queryset.filter(transactions__status__in=models.Payment.done_statuses).distinct()
        elif self.value() == 'waiting':
            return queryset.exclude(transactions__status__in=models.Payment.done_statuses).filter(transactions__status__in=models.Payment.waiting_statuses).distinct()
        elif self.value() == 'unknown':
            return queryset.exclude(team__subsidiary__city__cityincampaign__admission_fee=0).exclude(transactions__status__in=set(models.Payment.done_statuses) | set(models.Payment.waiting_statuses)).distinct()
        elif self.value() == 'none':
            return queryset.filter(transactions=None).distinct()


class UserAttendanceForm(forms.ModelForm):
    class Meta:
        model = models.UserAttendance

    def __init__(self, *args, **kwargs):
        super(UserAttendanceForm, self).__init__(*args, **kwargs)
        self.fields['t_shirt_size'].required = False


class UserAttendanceInline(EnhancedAdminMixin, NestedTabularInline):
    model = models.UserAttendance
    form = UserAttendanceForm
    extra = 0
    inlines = [PaymentInline, PackageTransactionInline, UserActionTransactionInline]
    list_display = ('userprofile__payment_type', 'userprofile__payment_status', 'userprofile__team__name', 'userprofile__distance', 'team__subsidiary__city', 'userprofile__team__subsidiary__company', 'trips_count', 'id')
    search_fields = ['first_name', 'last_name', 'username', 'email', 'userprofile__team__name', 'userprofile__team__subsidiary__company__name', 'company_admin__administrated_company__name', ]
    list_max_show_all = 10000
    raw_id_fields = ('team',)

    def queryset(self, request):
        return models.UserAttendance.objects.annotate(trips_count=Count('user_trips'))

    def trips_count(self, obj):
        return obj.trips_count
    trips_count.admin_order_field = 'trips_count'

    def userprofile__payment_type(self, obj):
        pay_type = "(None)"
        payment = obj.payment()['payment']
        if payment:
            pay_type = payment.pay_type
        return pay_type

    def userprofile__payment_status(self, obj):
        return obj.payment()['status_description']

    def userprofile__team__name(self, obj):
        return obj.team.name

    def userprofile__distance(self, obj):
        return obj.distance

    def team__subsidiary__city(self, obj):
        return obj.team.subsidiary.city

    def userprofile__team__subsidiary__company(self, obj):
        return obj.team.subsidiary.company


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['telephone'].required = False


class UserProfileAdminInline(EnhancedAdminMixin, NestedStackedInline):
    model = models.UserProfile
    form = UserProfileForm
    list_display = ('user__first_name', 'user__last_name', 'user', 'team', 'distance', 'user__email', 'user__date_joined', 'team__subsidiary__city', 'id', )
    inlines = [UserAttendanceInline, ]
    search_fields = ['user__first_name', 'user__last_name', 'user__username']

    #readonly_fields = ['mailing_id' ]

    def user__first_name(self, obj):
        return obj.user.first_name

    def user__last_name(self, obj):
        return obj.user.last_name

    def user__email(self, obj):
        return obj.user.email

    def user__date_joined(self, obj):
        return obj.user.date_joined

    def team__subsidiary__city(self, obj):
        return obj.team.subsidiary.city


class CompanyAdminInline(EnhancedAdminMixin, NestedTabularInline):
    raw_id_fields = ('administrated_company',)
    extra = 0
    model = dpnk.models.CompanyAdmin


class HasUserprofileFilter(SimpleListFilter):
    title = u"Má userprofile"
    parameter_name = u'has_userprofile'

    def lookups(self, request, model_admin):
        return [
            ('yes', 'Yes'),
            ('no', 'No'),
            ]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(userprofile=None)
        if self.value() == 'no':
            return queryset.filter(userprofile=None)
        return queryset


class UserAdmin(ImportExportModelAdmin, EnhancedModelAdminMixin, NestedModelAdmin, UserAdmin):
    inlines = (CompanyAdminInline, UserProfileAdminInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'date_joined', 'is_active', 'id')
    search_fields = ['first_name', 'last_name', 'username', 'email', 'company_admin__administrated_company__name', ]
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'company_admin__company_admin_approved', HasUserprofileFilter]
    readonly_fields = ['password']
    list_max_show_all = 10000

    #def queryset(self, request):
    #    return User.objects.annotate(trips_count = Count('userprofile__user_trips'))

    def trips_count(self, obj):
        return obj.trips_count
    trips_count.admin_order_field = 'trips_count'

    def userprofile__payment_type(self, obj):
        pay_type = "(None)"
        payment = obj.userprofile.payment()['payment']
        if payment:
            pay_type = payment.pay_type
        return pay_type

    def userprofile__telephone(self, obj):
        return obj.userprofile.telephone

    def userprofile__payment_status(self, obj):
        return obj.userprofile.payment()['status_description']

    def userprofile__team__name(self, obj):
        return obj.userprofile.team.name

    def userprofile__distance(self, obj):
        return obj.userprofile.distance

    def userprofile__team__subsidiary__city(self, obj):
        return obj.userprofile.team.subsidiary.city

    def userprofile__team__subsidiary__company(self, obj):
        return obj.userprofile.team.subsidiary.company

    def company_admin__administrated_company(self, obj):
        return obj.company_admin.administrated_company


def update_mailing(modeladmin, request, queryset):
    for user_attendance in queryset:
        mailing.add_or_update_user(user_attendance)
update_mailing.short_description = _(u"Aktualizovat mailing list")


def approve_am_payment(modeladmin, request, queryset):
    for user_attendance in queryset:
        payment = user_attendance.payment()['payment']
        if payment.pay_type == "am" and payment.status == models.Payment.Status.NEW:
            payment.status = models.Payment.Status.DONE
            payment.save()
approve_am_payment.short_description = _(u"Potvrdit platbu člena klubu přátel AM")


#TODO: this filters any paymant that user has is of specified type, should be only the last payment
class PaymentTypeFilter(SimpleListFilter):
    title = u"typ platby"
    parameter_name = u'payment_type'

    def lookups(self, request, model_admin):
        return models.Payment.PAY_TYPES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(transactions__payment__pay_type=self.value()).distinct()


class NotInCityFilter(SimpleListFilter):
    title = u"Ne ve městě"
    parameter_name = u'not_in_city'

    def lookups(self, request, model_admin):
        return [(c.pk, c.name) for c in models.City.objects.all()]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        return queryset.exclude(team__subsidiary__city=self.value())


class UserAttendanceAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('__unicode__', 'id', 'distance', 'team', 'team__subsidiary', 'team__subsidiary__company', 'approved_for_team', 'campaign', 't_shirt_size', 'payment_type', 'payment_status')
    list_filter = ('campaign', 'team__subsidiary__city', NotInCityFilter, 'approved_for_team', 't_shirt_size', PaymentTypeFilter, PaymentFilter)
    raw_id_fields = ('userprofile', 'team')
    search_fields = ('userprofile__user__first_name', 'userprofile__user__last_name', 'userprofile__user__username', 'userprofile__user__email')
    actions = (update_mailing, approve_am_payment)
    form = UserAttendanceForm
    inlines = [PaymentInline, PackageTransactionInline, UserActionTransactionInline]

    def team__subsidiary(self, obj):
        if obj.team:
            return obj.team.subsidiary

    def team__subsidiary__company(self, obj):
        if obj.team:
            return obj.team.subsidiary.company


class CoordinatorFilter(SimpleListFilter):
    title = u"stav týmu"
    parameter_name = u'team_state'

    def lookups(self, request, model_admin):
        return (
            ('without_coordinator', u'bez koordinátora'),
            ('inactive_coordinator', u'neaktivní koordinátor'),
            ('empty', u'prázdný tým'),
            ('foreign_coordinator', u'cizí koordinátor (chyba)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'without_coordinator':
            return queryset.filter(coordinator_campaign=None)
        if self.value() == 'inactive_coordinator':
            return queryset.filter(coordinator_campaign__userprofile__user__is_active=False)
        if self.value() == 'empty':
            return queryset.filter(users=None)
        if self.value() == 'foreign_coordinator':
            return queryset.exclude(coordinator_campaign__team__id=F("id"))


class TeamAdmin(EnhancedModelAdminMixin, ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name', 'subsidiary', 'subsidiary__city', 'subsidiary__company', 'coordinator_campaign', 'member_count', 'campaign', 'id', )
    search_fields = ['name', 'subsidiary__address_street', 'subsidiary__company__name', 'coordinator_campaign__userprofile__user__first_name', 'coordinator_campaign__userprofile__user__last_name']
    list_filter = ['subsidiary__city', 'campaign', 'member_count', CoordinatorFilter]
    list_max_show_all = 10000
    raw_id_fields = ['subsidiary', ]

    readonly_fields = ['members', 'invitation_token', 'member_count']

    def members(self, obj):
        return mark_safe("<br/>".join(['<a href="' + wp_reverse('admin') + 'auth/user/%d">%s</a>' % (u.userprofile.user.id, str(u))
                         for u in models.UserAttendance.objects.filter(team=obj)]))
    members.short_description = 'Členové'
    form = models.TeamForm

    def subsidiary__city(self, obj):
        return obj.subsidiary.city

    def subsidiary__company(self, obj):
        return obj.subsidiary.company


class TransactionChildAdmin(EnhancedModelAdminMixin, PolymorphicChildModelAdmin):
    base_model = models.Transaction
    raw_id_fields = ('user_attendance',)
    readonly_fields = ('author', 'created', 'updated_by')


class PaymentChildAdmin(TransactionChildAdmin):
    form = models.PaymentForm


class PackageTransactionChildAdmin(TransactionChildAdmin):
    readonly_fields = ['created', 'author', 'updated_by', 'tracking_number', 't_shirt_size']
    form = models.PackageTransactionForm


class CommonTransactionChildAdmin(TransactionChildAdmin):
    form = models.CommonTransactionForm


class UserActionTransactionChildAdmin(TransactionChildAdmin):
    form = models.UserActionTransactionForm


class TransactionAdmin(PolymorphicParentModelAdmin):
    list_display = ('id', 'user_attendance', 'created', 'status', 'polymorphic_ctype', 'user_link', 'author')
    search_fields = ('user_attendance__userprofile__user__first_name', 'user_attendance__userprofile__user__last_name', 'user_attendance__userprofile__user__username')
    list_filter = ['status', 'polymorphic_ctype', 'user_attendance__campaign']

    readonly_fields = ['user_link', ]

    def user_link(self, obj):
        if obj.user_attendance:
            return mark_safe('<a href="' + wp_reverse('admin') + 'auth/user/%d">%s</a>' % (obj.user_attendance.userprofile.user.pk, obj.user_attendance.userprofile.user))
    user_link.short_description = 'Uživatel'

    base_model = models.Transaction
    child_models = (
        (models.Payment, PaymentChildAdmin),
        (models.PackageTransaction, PackageTransactionChildAdmin),
        (models.CommonTransaction, CommonTransactionChildAdmin),
        (models.UserActionTransaction, UserActionTransactionChildAdmin),
        )


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_attendance', 'created', 'status', 'session_id', 'trans_id', 'amount', 'pay_type', 'error', 'order_id', 'author')
    search_fields = ('session_id', 'trans_id', 'order_id')
    list_filter = ['status', 'error', 'pay_type']
    raw_id_fields = ('user_attendance',)
    readonly_fields = ('author', 'created')


class ChoiceInline(EnhancedAdminMixin, admin.TabularInline):
    model = models.Choice
    extra = 3


class ChoiceTypeAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'competition', 'universal')
    inlines = [ChoiceInline]
    list_filter = ('competition', )


class AnswerAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('user_attendance', 'points_given', 'choices__all', 'choices_ids__all', 'question__competition', 'comment', 'question')
    search_fields = ('user_attendance__userprofile__user__first_name', 'user_attendance__userprofile__user__last_name')
    list_filter = ('question__competition',)
    filter_horizontal = ('choices',)
    list_max_show_all = 100000
    raw_id_fields = ('user_attendance', )

    def choices__all(self, obj):
        return " | ".join([ch.text for ch in obj.choices.all()])

    def choices_ids__all(self, obj):
        return ", ".join([(str(ch.pk)) for ch in obj.choices.all()])

    def question__competition(self, obj):
        return obj.question.competition


class QuestionAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('text', 'type', 'order', 'date', 'competition', 'answers_link', 'id', )
    ordering = ('order', 'date',)
    list_filter = ('competition',)

    readonly_fields = ['choices', 'answers_link', ]

    def choices(self, obj):
        return mark_safe("<br/>".join([
            choice.text for choice in obj.choice_type.choices.all()]) + '<br/><a href="' + wp_reverse('admin') + 'dpnk/choicetype/%d">edit</a>' % obj.choice_type.id)

    def answers_link(self, obj):
        return mark_safe('<a href="' + wp_reverse('admin') + 'odpovedi/?question=%d">vyhodnocení odpovědí</a>' % (obj.pk))


class TripAdmin(EnhancedModelAdminMixin, ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('user_attendance', 'date', 'trip_from', 'trip_to', 'distance_from', 'distance_to', 'id')
    search_fields = ('user_attendance__userprofile__user__first_name', 'user_attendance__userprofile__user__last_name', 'user_attendance__userprofile__user__username')
    raw_id_fields = ('user_attendance',)


class CompetitionResultAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('user_attendance', 'team', 'result', 'competition')
    list_filter = ('competition',)
    search_fields = ('user_attendance__userprofile__user__first_name', 'user_attendance__userprofile__user__last_name', 'user_attendance__userprofile__user__username', 'team__name', 'user_attendance__userprofile__team__name', 'competition__name')
    raw_id_fields = ('user_attendance', 'team')


class PhaseInline(EnhancedModelAdminMixin, admin.TabularInline):
    model = models.Phase
    extra = 0


class CityInCampaignInline(EnhancedAdminMixin, admin.TabularInline):
    model = models.CityInCampaign
    extra = 0


class TShirtSizeInline(EnhancedAdminMixin, SortableInlineAdminMixin, admin.TabularInline):
    model = models.TShirtSize
    extra = 0


class DeliveryBatchAdmin(EnhancedAdminMixin, admin.ModelAdmin):
    list_display = ('campaign', 'created', 'package_transaction__count', 'customer_sheets__url', 'tnt_order__url')
    readonly_fields = ('campaign', 'author', 'created', 'updated_by', 'package_transaction__count')
    inlines = [PackageTransactionInline, ]

    def package_transaction__count(self, obj):
        if not obj.pk:
            return obj.campaign.user_attendances_for_delivery().count()
        return obj.packagetransaction_set.count()
    package_transaction__count.short_description = "Balíčků k odeslání"

    def customer_sheets__url(self, obj):
        return mark_safe(u"<a href='%s'>customer_sheets</a>" % obj.customer_sheets.url)

    def tnt_order__url(self, obj):
        return mark_safe(u"<a href='%s'>tnt_order</a>" % obj.tnt_order.url)


class CampaignAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'slug', 'mailing_list_enabled', )
    inlines = [TShirtSizeInline, PhaseInline, CityInCampaignInline]
    prepopulated_fields = {'slug': ('name',)}


class CompanyAdminAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ['user', 'user__email', 'user__name', 'user__telephone', 'company_admin_approved', 'administrated_company__name', 'can_confirm_payments', 'note', 'campaign']
    list_filter = ['campaign', 'company_admin_approved']
    search_fields = ['administrated_company__name', 'user__first_name', 'user__last_name', 'user__username']
    raw_id_fields = ['user', ]

    def user__email(self, obj):
        return obj.user.email

    def user__name(self, obj):
        return obj.user.get_profile()

    def user__telephone(self, obj):
        return obj.user.get_profile().telephone

    def administrated_company__name(self, obj):
        if obj.administrated_company:
            return obj.administrated_company.name

admin.site.register(models.Team, TeamAdmin)
admin.site.register(models.Transaction, TransactionAdmin)
admin.site.register(models.Payment, PaymentAdmin)
admin.site.register(models.Question, QuestionAdmin)
admin.site.register(models.ChoiceType, ChoiceTypeAdmin)
admin.site.register(models.City, CityAdmin)
admin.site.register(models.Subsidiary, SubsidiaryAdmin)
admin.site.register(models.Company, CompanyAdmin)
admin.site.register(models.Competition, CompetitionAdmin)
admin.site.register(models.CompetitionResult, CompetitionResultAdmin)
admin.site.register(models.Answer, AnswerAdmin)
admin.site.register(models.Trip, TripAdmin)
admin.site.register(models.Campaign, CampaignAdmin)
admin.site.register(models.UserAttendance, UserAttendanceAdmin)
admin.site.register(models.CompanyAdmin, CompanyAdminAdmin)
admin.site.register(models.DeliveryBatch, DeliveryBatchAdmin)

admin.site.unregister(models.User)
admin.site.register(models.User, UserAdmin)
