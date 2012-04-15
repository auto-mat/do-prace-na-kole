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
from models import UserProfile, Team, Payment
# -- ADMIN FORMS --

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0

class TeamInline(admin.TabularInline):
    model = Team
    extra = 0

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('firstname', 'surname', 'team', 'distance', 'email', 'date_joined')
    inlines = [PaymentInline]

    readonly_fields = ['team_link']
    def team_link(self, obj):
        return mark_safe('<a href="/admin/admin/dpnk/team/%s">%s</a>' % (obj.team.id, obj.team.name))
    team_link.short_description = 'Tým'

class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'city', 'password')
    fields = ('name', 'members', 'company', 'city', 'address', 'password')

    readonly_fields = ['members']
    def members(self, obj):
        return mark_safe("<br/>".join(['<a href="/admin/admin/dpnk/userprofile/%d">%s</a>' % (u.id, str(u))
                                  for u in UserProfile.objects.filter(team=obj)]))
    members.short_description = 'Členové'

    
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('trans_id', 'user', 'amount', 'pay_type', 'created', 'status')
    fields = ('trans_id', 'user', 'amount', 'description', 'created', 'status', 'realized', 'pay_type', 'error', 'session_id')

    list_filter = ['status', 'pay_type']
    
admin.site.unregister(User)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Payment, PaymentAdmin)

from django.contrib.auth.models import Group
admin.site.unregister(Group)
