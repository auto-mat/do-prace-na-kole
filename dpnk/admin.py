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
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
# Models
from models import *
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
    list_display = ('name', 'admission_fee')

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'subsidiaries_text')
    inlines = [SubsidiaryInline,]
    readonly_fields = ['subsidiaries']
    def subsidiaries_text(self, obj):
        return mark_safe(" | ".join(['%s' % (str(u))
                                  for u in Subsidiary.objects.filter(company=obj)]))
    subsidiaries_text.short_description = 'Pobočky'
    def subsidiaries(self, obj):
        return mark_safe("<br/>".join(['<a href="/admin/admin/dpnk/subsidiary/%d">%s</a>' % (u.id, str(u))
                                  for u in Subsidiary.objects.filter(company=obj)]))
    subsidiaries.short_description = 'Pobočky'

class SubsidiaryAdmin(admin.ModelAdmin):
    list_display = ('address', 'company', 'city')
    inlines = [TeamInline,]
    list_filter = ['city']

class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'competitor_type')

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('firstname', 'surname', 'team', 'distance', 'email', 'date_joined', 'city')
    inlines = [PaymentInline, VoucherInline]
    search_fields = ['firstname', 'surname']
    list_filter = ['active', 'team__subsidiary__city']

    readonly_fields = ['team_link']
    def team_link(self, obj):
        return mark_safe('<a href="/admin/admin/dpnk/team/%s">%s</a>' % (obj.team.id, obj.team.name))
    team_link.short_description = 'Tým'

class UserProfileUnpaidAdmin(UserProfileAdmin):
    list_display = ('firstname', 'surname', 'team', 'distance', 'email', 'date_joined', 'city')

class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'subsidiary', 'team_subsidiary_city', 'team_subsidiary_company',)
    search_fields = ['name', 'subsidiary__address', 'subsidiary__company__name']
    list_filter = ['subsidiary__city']

    readonly_fields = ['members']
    def members(self, obj):
        return mark_safe("<br/>".join(['<a href="/admin/admin/dpnk/userprofile/%d">%s</a>' % (u.id, str(u))
                                  for u in UserProfile.objects.filter(team=obj, active=True)]))
    members.short_description = 'Členové'

    
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('trans_id', 'user', 'amount', 'pay_type', 'created', 'status')
    fields = ('trans_id', 'user', 'amount', 'description', 'created', 'status', 'realized', 'pay_type', 'error', 'session_id')

    list_filter = ['status', 'pay_type']


class VoucherAdmin(admin.ModelAdmin):
    list_display = ('code', 'user')
    fields = ('code', 'user')

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0

class ChoiceTypeAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_filter = ('competition',)

class AnswerAdmin(admin.ModelAdmin):
    pass

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'type', 'order', 'date', 'competition')
    ordering = ('order', 'date',)
    list_filter = ('competition',)
    #fields = ('text', 'type', 'with_comment', 'order', 'date')

    readonly_fields = ['choices']
    def choices(self, obj):
        return mark_safe("<br/>".join([choice.text for choice in obj.choice_type.choices.all()]) + '<br/><a href="/admin/admin/dpnk/choicetype/%d">edit</a>' % obj.choice_type.id )

#admin.site.unregister(User)
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

from django.contrib.auth.models import Group
admin.site.unregister(Group)
