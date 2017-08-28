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


class CityAdminMixin(object):
    queryset_city_param = 'city__in'

    def get_queryset(self, request):
        queryset = super(admin.ModelAdmin, self).get_queryset(request)
        if request.user.has_perm('dpnk.can_edit_all_cities'):
            return queryset.distinct()
        kwargs = {self.queryset_city_param: request.user.userprofile.administrated_cities.all()}
        return queryset.filter(**kwargs).distinct()


def city_admin_mixin_generator(queryset_city):
    class CAMixin(CityAdminMixin):
        queryset_city_param = queryset_city
    return CAMixin


class FormRequestMixin(object):
    def get_form(self, request, *args, **kwargs):
        form = super().get_form(request, *args, **kwargs)
        form.request = request
        return form
