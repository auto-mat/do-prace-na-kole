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
from django.http import HttpResponseRedirect
# Models
from models import UserProfile, Team
# -- ADMIN FORMS --

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('firstname', 'surname', 'sex', 'language', 'competition_city', 'team',
                    'email', 'date_joined')

class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'password')
    fields = ('name', 'company', 'password')

admin.site.unregister(User)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Team, TeamAdmin)

from django.contrib.auth.models import Group
admin.site.unregister(Group)
