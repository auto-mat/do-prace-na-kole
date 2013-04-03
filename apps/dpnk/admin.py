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
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from snippets.related_field_admin import RelatedFieldAdmin
from dpnk.wp_urls import wp_reverse
# Models
from models import *
from django.forms import ModelForm
# -- ADMIN FORMS --

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0

class TeamInline(admin.TabularInline):
    model = Team
    extra = 0

class VoucherInline(admin.TabularInline):
    model = Voucher
    extra = 0

class SubsidiaryInline(admin.TabularInline):
    model = Subsidiary
    extra = 0

class TeamInline(admin.TabularInline):
    model = Team
    extra = 0

class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'admission_fee', 'id', )

class CompanyAdmin(admin.ModelAdmin):
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

class SubsidiaryAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'company', 'city', 'teams_text', 'id', )
    inlines = [TeamInline,]
    list_filter = ['city']
    search_fields = ('company__name', 'address_street',)

    readonly_fields = ['team_links']
    def teams_text(self, obj):
        return mark_safe(" | ".join(['%s' % (str(u))
                                  for u in Team.objects.filter(subsidiary=obj)]))
    teams_text.short_description = 'Týmy'
    def team_links(self, obj):
        return mark_safe("<br/>".join(['<a href="' + wp_reverse('admin') + 'dpnk/team/%d">%s</a>' % (u.id, str(u))
                                  for u in Team.objects.filter(subsidiary=obj)]))

class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'type', 'competitor_type', 'without_admission')

class UserProfileAdmin(RelatedFieldAdmin):
    list_display = ('user__first_name', 'user__last_name', 'user', 'team', 'distance', 'user__email', 'user__date_joined', 'team__subsidiary__city', 'id', )
    inlines = [PaymentInline, VoucherInline]
    search_fields = ['user__first_name', 'user__last_name', 'user__username']
    list_filter = ['user__is_active', 'team__subsidiary__city']

    readonly_fields = ['team_link']
    def team_link(self, obj):
        return mark_safe('<a href="' + wp_reverse('admin') + 'dpnk/team/%s">%s</a>' % (obj.team.id, obj.team.name))
    team_link.short_description = 'Tým'

class UserProfileUnpaidAdmin(UserProfileAdmin, RelatedFieldAdmin):
    list_display = ('user__first_name', 'user__last_name', 'user', 'team', 'distance', 'user__email', 'user__date_joined', 'team__subsidiary__city', 'id', )

class UserProfileAdminInline(admin.StackedInline):
    model = UserProfile
    inlines = [PaymentInline, ]
    can_delete=False

    readonly_fields = ['team_link']
    def team_link(self, obj):
        return mark_safe('<a href="' + wp_reverse('admin') + 'dpnk/team/%s">%s</a>' % (obj.team.id, obj.team.name))
    team_link.short_description = 'Tým'

class UserAdmin(UserAdmin, RelatedFieldAdmin):
    inlines = (UserProfileAdminInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_active', 'date_joined', 'userprofile__team', 'userprofile__distance', 'userprofile__team__subsidiary__city', 'id')
    search_fields = ['first_name', 'last_name', 'username']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'userprofile__team__subsidiary__city']

class TeamForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(TeamForm, self).__init__(*args, **kwargs)
        self.fields['coordinator'].queryset = UserProfile.objects.filter(team=self.instance)

class TeamAdmin(RelatedFieldAdmin):
    list_display = ('name', 'subsidiary', 'subsidiary__city', 'subsidiary__company', 'coordinator', 'id', )
    search_fields = ['name', 'subsidiary__address_street', 'subsidiary__company__name', 'coordinator__user__first_name', 'coordinator__user__last_name']
    list_filter = ['subsidiary__city']

    readonly_fields = ['members']
    def members(self, obj):
        return mark_safe("<br/>".join(['<a href="' + wp_reverse('admin') + 'dpnk/userprofile/%d">%s</a>' % (u.id, str(u))
                                  for u in UserProfile.objects.filter(team=obj, user__is_active=True)]))
    members.short_description = 'Členové'
    form = TeamForm

    
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('trans_id', 'user', 'amount', 'pay_type', 'created', 'status', 'id', )
    fields = ('trans_id', 'user', 'amount', 'description', 'created', 'status', 'realized', 'pay_type', 'error', 'session_id')

    list_filter = ['status', 'pay_type']


class VoucherAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'id', )
    fields = ('code', 'user')

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0

class ChoiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'competition', 'universal')
    inlines = [ChoiceInline]
    list_filter = ('competition', )

class AnswerAdmin(RelatedFieldAdmin):
    list_display = ( 'user', 'points_given', 'question__competition', 'comment', 'question')
    search_fields = ('user__user__first_name','user__user__last_name')

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'type', 'order', 'date', 'competition', 'id', )
    ordering = ('order', 'date',)
    list_filter = ('competition',)
    #fields = ('text', 'type', 'with_comment', 'order', 'date')

    readonly_fields = ['choices']
    def choices(self, obj):
        return mark_safe("<br/>".join([choice.text for choice in obj.choice_type.choices.all()]) + '<br/><a href="' + wp_reverse('admin') + 'dpnk/choicetype/%d">edit</a>' % obj.choice_type.id )

class TripAdmin(admin.ModelAdmin):
    model = Team

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserProfileUnpaid, UserProfileUnpaidAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Voucher, VoucherAdmin)
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
