# -*- coding: utf-8 -*-
# Author: Petr Dlouhy <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2015 o.s. Auto*Mat
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

from django.contrib import admin

class ReadOnlyModelAdminMixin(object):
    """ModelAdmin class that prevents modifications through the admin.

    The changelist and the detail view work, but a 403 is returned
    if one actually tries to edit an object.

    Source: https://gist.github.com/aaugustin/1388243
    """
 
    actions = None
 
    def get_readonly_fields(self, request, obj=None):
        return self.fields or [f.name for f in self.model._meta.fields]
 
    def has_add_permission(self, request):
        return False
 
    # Allow viewing objects but not actually changing them
    #def has_change_permission(self, request, obj=None):
    #    if request.method not in ('GET', 'HEAD'):
    #        return False
    #    return super(ReadOnlyModelAdminMixin, self).has_change_permission(request, obj)
 
    def has_delete_permission(self, request, obj=None):
        return False


class CityAdminMixin(object):
    queryset_city_param = 'city__in'
    def queryset(self, request):
        queryset = super(admin.ModelAdmin, self).queryset(request)
        if request.user.is_superuser:
            return queryset
        kwargs = { self.queryset_city_param: request.user.userprofile.administrated_cities.all()}
        return queryset.filter(**kwargs)


