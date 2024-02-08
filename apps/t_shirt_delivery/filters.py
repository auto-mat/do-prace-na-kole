# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2017 o.s. Auto*Mat
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

from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _


class AllPackagesDispatched(SimpleListFilter):
    title = _("Všechny balíčky vyřízeny")
    parameter_name = "all_packages_dispatched"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Ano")),
            ("no", _("Ne")),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.exclude(teampackage__dispatched=False)
        if self.value() == "no":
            return queryset.filter(teampackage__dispatched=False)


class InputFilter(SimpleListFilter):
    template = "admin/input_filter.html"

    def lookups(self, request, model_admin):
        # Dummy, required to show the filter.
        return ((),)


class IdFilter(InputFilter):
    parameter_name = "id"
    title = _("Id")

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice["query_parts"] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )
        yield all_choice

    def queryset(self, request, queryset):
        if self.value() is not None:
            ids = self.value()
            return queryset.filter(id__in=[id.strip() for id in ids.split(",")])
