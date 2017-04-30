# -*- coding: utf-8 -*-
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
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

import re

from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import Case, CharField, Q, Value, When

from django_datatables_view.base_datatable_view import BaseDatatableView

from . import models


class CompetitionResultListJson(BaseDatatableView):
    model = models.CompetitionResult
    max_display_length = 100

    def get_columns(self):
        columns = self.competition.get_columns()
        return list(zip(*columns))[1]

    def render_column(self, row, column):
        if column == 'team__member_count':
            return str(row.team.member_count)
        if column == 'user_attendance':
            return str(row.user_attendance)
        if column == 'get_sequence_range':
            sequence_range = self.rank_dict[row.id]
            if sequence_range[0] == sequence_range[1]:
                return "%s." % sequence_range[0]
            else:
                return "%s.&nbsp;-&nbsp;%s." % sequence_range
        if column in ('get_company', 'get_city', 'get_street', 'get_subsidiary'):
            return str(getattr(row, column)())
        if column in ('get_result_percentage'):
            return intcomma(getattr(row, column)())
        if column == 'get_team':
            return row.get_team().name
        else:
            return super().render_column(row, column)

    def get_initial_queryset(self):
        if not hasattr(self, 'competition'):
            self.competition = models.Competition.objects.get(
                slug=self.kwargs['competition_slug'],
            )
        results = self.competition.get_results()
        return self.competition.select_related_results(results)

    def prepare_results(self, results):
        all_results = self.get_initial_queryset()
        if not self.queryset_filtered:
            all_results = self.paging(all_results)
        all_results = self.competition.annotate_results_rank(all_results)
        self.rank_dict = self.competition.get_result_id_rank_dict(all_results)
        return super().prepare_results(results)

    def filter_queryset(self, qs):
        self.queryset_filtered = False
        search = self.request.GET.get('search[value]', None)
        if search:
            self.queryset_filtered = True
            qs = qs.annotate(
                first_name=Case(
                    When(user_attendance__userprofile__nickname__isnull=False, then=Value(None)),
                    default="user_attendance__userprofile__user__first_name",
                    output_field=CharField(),
                ),
                last_name=Case(
                    When(user_attendance__userprofile__nickname__isnull=False, then=Value(None)),
                    default="user_attendance__userprofile__user__last_name",
                    output_field=CharField(),
                ),
            )
            for s in search.split():
                qs = qs.filter(
                    Q(user_attendance__userprofile__nickname__unaccent__icontains=s) |
                    Q(first_name__unaccent__icontains=s) |
                    Q(last_name__unaccent__icontains=s) |
                    Q(company__name__unaccent__icontains=s) |
                    Q(user_attendance__team__subsidiary__city__name__unaccent__icontains=s) |
                    Q(user_attendance__team__subsidiary__company__name__unaccent__icontains=s) |
                    Q(user_attendance__team__subsidiary__address_street__unaccent__icontains=s) |
                    Q(user_attendance__team__name__unaccent__icontains=s) |
                    Q(team__subsidiary__city__name__unaccent__icontains=s) |
                    Q(team__subsidiary__company__name__unaccent__icontains=s) |
                    Q(team__subsidiary__address_street__unaccent__icontains=s) |
                    Q(team__name__unaccent__icontains=s),
                )

        company_search = self.request.GET.get('columns[0][search][value]', None)  # the column 7 means always company column
        if company_search:
            self.queryset_filtered = True
            querystring = self.competition.get_company_querystring()

            m = re.match(r'^"(.*)"$', company_search)
            if m:
                search_operation = 'iexact'
                company_search = m.group(1)
            else:
                search_operation = 'icontains'
            qs = qs.filter(**{'%s__name__unaccent__%s' % (querystring, search_operation): company_search})

        return qs
