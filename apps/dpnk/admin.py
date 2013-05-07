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
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.models import User
from django.db.models import F, Sum
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from admin_enhancer.admin import EnhancedModelAdminMixin, EnhancedAdminMixin
from dpnk.wp_urls import wp_reverse
from nested_inlines.admin import NestedModelAdmin, NestedStackedInline, NestedTabularInline
# Models
from models import *
import dpnk
from django.forms import ModelForm
# -- ADMIN FORMS --

class PaymentInline(EnhancedAdminMixin, NestedTabularInline):
    model = Payment
    extra = 0
    readonly_fields = [ 'order_id', 'session_id', 'trans_id', 'error', ]

class TeamInline(EnhancedAdminMixin, admin.TabularInline):
    model = Team
    extra = 0
    readonly_fields = ['invitation_token',]

class SubsidiaryInline(EnhancedAdminMixin, admin.TabularInline):
    model = Subsidiary
    extra = 0

class CityAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'admission_fee', 'id', )

class CompanyAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'subsidiaries_text', 'id', )
    inlines = [SubsidiaryInline,]
    readonly_fields = ['subsidiary_links']
    search_fields = ('name',)
    def subsidiaries_text(self, obj):
        return mark_safe(" | ".join(['%s' % (str(u))
                                  for u in Subsidiary.objects.filter(company=obj)]))
    subsidiaries_text.short_description = 'Pobočky'
    def subsidiary_links(self, obj):
        return mark_safe("<br/>".join(['<a href="' + wp_reverse('admin') + 'dpnk/subsidiary/%d">%s</a>' % (u.id, str(u))
                                  for u in Subsidiary.objects.filter(company=obj)]))
    subsidiary_links.short_description = 'Pobočky'

class SubsidiaryAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('__unicode__', 'company', 'city', 'teams_text', 'id', )
    inlines = [TeamInline,]
    list_filter = ['city']
    search_fields = ('company__name', 'address_street',)

    readonly_fields = ['team_links', ]
    def teams_text(self, obj):
        return mark_safe(" | ".join(['%s' % (str(u))
                                  for u in Team.objects.filter(subsidiary=obj)]))
    teams_text.short_description = 'Týmy'
    def team_links(self, obj):
        return mark_safe("<br/>".join(['<a href="' + wp_reverse('admin') + 'dpnk/team/%d">%s</a>' % (u.id, str(u))
                                  for u in Team.objects.filter(subsidiary=obj)]))
    team_links.short_description = u"Týmy"

class CompetitionAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'slug', 'type', 'competitor_type', 'without_admission', 'date_from', 'date_to', 'city', 'company')
    filter_horizontal = ('user_competitors', 'team_competitors', 'company_competitors')

class PaymentFilter(SimpleListFilter):
    title = u"stav platby"
    parameter_name = u'payment_state'

    def lookups(self, request, model_admin):
        return (
            ('not_paid', u'nezaplaceno'),
            ('not_paid_older', u'nezaplaceno (platba starší než 5 dnů)'),
            ('no_admission', u'neplatí se'),
            ('done', u'vyřízeno'),
            ('waiting', u'čeká se'),
            ('unknown', u'neznámý'),
            ('none', u'bez plateb'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'not_paid_older':
            paying_or_prospective_user_ids = [p.user_id for p in Payment.objects.filter(
                Q(status=Payment.Status.DONE) | Q (
                    # Bank transfer less than 5 days old
                    status=Payment.Status.NEW, pay_type='bt',
                    created__gt=datetime.datetime.now() - datetime.timedelta(days=5))
                )]
            return queryset.filter(
                userprofile__user__is_active=True).exclude(userprofile__id__in=paying_or_prospective_user_ids)
        elif self.value() == 'not_paid':
            return queryset.filter(
                userprofile__user__is_active=True).exclude(userprofile__payments__status__in = Payment.done_statuses)
        elif self.value() == 'no_admission':
            return queryset.filter(userprofile__team__subsidiary__city__admission_fee = 0)
        elif self.value() == 'done':
            return queryset.filter(userprofile__payments__status__in = Payment.done_statuses)
        elif self.value() == 'waiting':
            return queryset.exclude(userprofile__payments__status__in = Payment.done_statuses).filter(userprofile__payments__status__in = Payment.waiting_statuses)
        elif self.value() == 'unknown':
            return queryset.exclude(userprofile__team__subsidiary__city__admission_fee = 0, userprofile__payments__status__in = set(Payment.done_statuses) | set(Payment.waiting_statuses))
        elif self.value() == 'none':
            return queryset.filter(userprofile__payments = None)

class UserProfileAdminInline(EnhancedAdminMixin, NestedStackedInline):
    model = UserProfile
    list_display = ('user__first_name', 'user__last_name', 'user', 'team', 'distance', 'user__email', 'user__date_joined', 'team__subsidiary__city', 'id', )
    inlines = [PaymentInline, ]
    search_fields = ['user__first_name', 'user__last_name', 'user__username']
    list_filter = ['user__is_active', 'team__subsidiary__city', 'approved_for_team', 't_shirt_size', PaymentFilter]

    readonly_fields = ['mailing_id' ]

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

class CompanyAdminInline(EnhancedAdminMixin, NestedStackedInline):
    model = dpnk.models.CompanyAdmin

class UserAdmin(EnhancedModelAdminMixin, NestedModelAdmin, UserAdmin):
    inlines = (CompanyAdminInline, UserProfileAdminInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'userprofile__payment_type', 'userprofile__payment_status', 'date_joined', 'userprofile__team', 'userprofile__distance', 'userprofile__team__subsidiary__city', 'userprofile__team__subsidiary__company', 'company_admin__administrated_company', 'is_staff', 'is_superuser', 'is_active', 'id')
    search_fields = ['first_name', 'last_name', 'username', 'email', 'userprofile__team__subsidiary__company__name',]
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'userprofile__team__subsidiary__city', 'company_admin__company_admin_approved', 'userprofile__approved_for_team', 'userprofile__t_shirt_size', 'userprofile__team__subsidiary__city', PaymentFilter]
    readonly_fields = ['password']
    list_max_show_all = 10000

    def userprofile__payment_type(self, obj):
       pay_type = "(None)"
       payment = obj.userprofile.payment()['payment']
       if payment:
          pay_type = payment.pay_type
       return pay_type
    def userprofile__payment_status(self, obj):
       return obj.userprofile.payment()['status_description']
    def userprofile__team(self, obj):
       return obj.userprofile.team
    def userprofile__distance(self, obj):
       return obj.userprofile.distance
    def userprofile__team__subsidiary__city(self, obj):
        return obj.userprofile.team.subsidiary.city
    def userprofile__team__subsidiary__company(self, obj):
        return obj.userprofile.team.subsidiary.company
    def company_admin__administrated_company(self, obj):
        return obj.company_admin.administrated_company

class TeamForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(TeamForm, self).__init__(*args, **kwargs)
        self.fields['coordinator'].queryset = UserProfile.objects.filter(team=self.instance)

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
            return queryset.filter(coordinator = None)
        if self.value() == 'inactive_coordinator':
            return queryset.filter(coordinator__user__is_active = False)
        if self.value() == 'empty':
            return queryset.filter(users = None)
        if self.value() == 'foreign_coordinator':
            return queryset.exclude(coordinator__team__id = F("id"))

class LiberoFilter(SimpleListFilter):
    title = u"libero"
    parameter_name = u'libero'

    def lookups(self, request, model_admin):
        return (
            ('empty', u'prázdný'),
            ('libero', u'libero'),
            ('non libero', u'ne libero'),
        )

    def queryset(self, request, queryset):
        queryset = queryset.annotate(team_member_count=Sum('users__user__is_active'))
        if self.value() == 'empty':
            return queryset.filter(team_member_count__lte = 0)
        if self.value() == 'libero':
            return queryset.filter(team_member_count__lte = 1, team_member_count__gt = 0)
        elif self.value() == 'non_libero':
            return queryset.filter(team_member_count__gt = 1)

class TeamAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'subsidiary', 'subsidiary__city', 'subsidiary__company', 'coordinator', 'id', )
    search_fields = ['name', 'subsidiary__address_street', 'subsidiary__company__name', 'coordinator__user__first_name', 'coordinator__user__last_name']
    list_filter = ['subsidiary__city', CoordinatorFilter, LiberoFilter]
    list_max_show_all = 10000

    readonly_fields = ['members', 'invitation_token']
    def members(self, obj):
        return mark_safe("<br/>".join(['<a href="' + wp_reverse('admin') + 'auth/user/%d">%s</a>' % (u.user.id, str(u))
                                  for u in UserProfile.objects.filter(team=obj, user__is_active=True)]))
    members.short_description = 'Členové'
    form = TeamForm

    def subsidiary__city(self, obj):
       return obj.subsidiary.city
    def subsidiary__company(self, obj):
       return obj.subsidiary.company
    
class PaymentAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'trans_id', 'session_id', 'user', 'amount', 'pay_type', 'created', 'status', )
    search_fields = ('trans_id', 'session_id', 'user__user__first_name', 'user__user__last_name' )

    list_filter = ['status', 'pay_type']

    readonly_fields = ['user_link', ]
    def user_link(self, obj):
        return mark_safe('<a href="' + wp_reverse('admin') + 'auth/user/%d">%s</a>' % (obj.user.user.pk, obj.user.user))
    user_link.short_description = 'Uživatel'

class ChoiceInline(EnhancedAdminMixin, admin.TabularInline):
    model = Choice
    extra = 3

class ChoiceTypeAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'competition', 'universal')
    inlines = [ChoiceInline]
    list_filter = ('competition', )

class AnswerAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ( 'user', 'points_given', 'question__competition', 'comment', 'question')
    search_fields = ('user__user__first_name','user__user__last_name')

    def question__competition(self, obj):
       return obj.question.competition

class QuestionAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    list_display = ('text', 'type', 'order', 'date', 'competition', 'id', )
    ordering = ('order', 'date',)
    list_filter = ('competition',)

    readonly_fields = ['choices']
    def choices(self, obj):
        return mark_safe("<br/>".join([choice.text for choice in obj.choice_type.choices.all()]) + '<br/><a href="' + wp_reverse('admin') + 'dpnk/choicetype/%d">edit</a>' % obj.choice_type.id )

class TripAdmin(EnhancedModelAdminMixin, admin.ModelAdmin):
    model = Team

admin.site.register(Team, TeamAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(ChoiceType, ChoiceTypeAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Subsidiary, SubsidiaryAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Competition, CompetitionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(Trip, TripAdmin)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
