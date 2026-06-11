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
from django.shortcuts import get_object_or_404
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView, View

from django_datatables_view.base_datatable_view import BaseDatatableView

from donation_chooser.models import get_charitative_results_column

from . import models
from . import resources
from .views_mixins import (
    ExportViewMixin,
    TitleViewMixin,
    UserAttendanceParameterMixin,
)


class WithCompetitionMixin(UserAttendanceParameterMixin):
    def get_object(self):
        competition_slug = self.kwargs.get("competition_slug")
        return get_object_or_404(
            models.Competition,
            slug=competition_slug,
        )


class CompetitionResultsView(WithCompetitionMixin, TitleViewMixin, TemplateView):
    template_name = "dpnk/competition_results.html"
    title = _("Výsledky soutěže")

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data["competition"] = self.get_object()
        return context_data

    # This is here for NewRelic to distinguish from TemplateView.get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


def should_include_personal_info(user, campaign, organization):
    if user.is_superuser:
        return True
    userprofile = models.UserProfile.objects.get(user=user)
    try:
        company_admin = models.CompanyAdmin.objects.get(
            userprofile=userprofile, campaign=campaign
        )
        return company_admin.administrated_company == organization
    except models.CompanyAdmin.DoesNotExist:
        return False
    return False


class ExportCompetitionResults(WithCompetitionMixin, ExportViewMixin, View):
    def dispatch(self, request, *args, extension="csv", organization=None, **kwargs):
        super().dispatch(request, *args, **kwargs)
        competition = self.get_object()
        queryset = models.CompetitionResult.objects.filter(
            competition=competition,
        )
        if organization:
            organization = models.Company.objects.get(pk=organization)
            queryset = queryset.filter(
                Q(user_attendance__team__subsidiary__company=organization)
                | Q(team__subsidiary__company=organization),
            )
        campaign = competition.campaign
        export_data = resources.CompetitionResultResource(
            should_include_personal_info(request.user, campaign, organization)
        ).export(queryset)
        return self.generate_export(export_data, extension)


class CompetitionResultListJson(BaseDatatableView):
    model = models.CompetitionResult
    max_display_length = 100

    def get_columns(self):
        columns = self.competition.get_columns()
        return list(zip(*columns))[1]

    def render_column(self, row, column):
        if column == "team__member_count":
            return str(row.team.member_count)
        if column == "user_attendance":
            return escape(row.user_attendance)
        if column == "donation_icon":
            return get_charitative_results_column(row.user_attendance)
        if column == "get_sequence_range":
            sequence_range = self.rank_dict[row.id]
            if sequence_range[0] == sequence_range[1]:
                return "%s." % sequence_range[0]
            else:
                return "%s.&nbsp;-&nbsp;%s." % sequence_range
        if column in (
            "get_company",
            "get_city",
            "get_street",
            "get_subsidiary",
            "get_occupation",
            "get_sex",
            "get_team_name",
        ):
            return escape(getattr(row, column)() or "")
        if column in (
            "get_result",
            "get_result_percentage",
            "get_result_divident",
            "get_result_divisor",
        ):
            return intcomma(getattr(row, column)())
        else:
            return super().render_column(row, column)

    @property
    def competition(self):
        if not hasattr(self, "_competition"):
            self._competition = models.Competition.objects.get(
                slug=self.kwargs["competition_slug"],
            )
        return self._competition

    def get_initial_queryset(self):
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
        search = self.request.GET.get("search[value]", None)
        if search:
            self.queryset_filtered = True
            qs = qs.annotate(
                first_name=Case(
                    When(
                        user_attendance__userprofile__nickname__isnull=False,
                        then=Value(None),
                    ),
                    default="user_attendance__userprofile__user__first_name",
                    output_field=CharField(),
                ),
                last_name=Case(
                    When(
                        user_attendance__userprofile__nickname__isnull=False,
                        then=Value(None),
                    ),
                    default="user_attendance__userprofile__user__last_name",
                    output_field=CharField(),
                ),
            )
            if search.lower() == "muž":
                search = "male"
            elif search.lower() == "žena":
                search = "female"
            for s in search.split():
                qs = qs.filter(
                    Q(user_attendance__userprofile__nickname__unaccent__icontains=s)
                    | Q(
                        user_attendance__userprofile__occupation__name__unaccent__icontains=s
                    )
                    | Q(user_attendance__userprofile__sex=s)
                    | Q(first_name__unaccent__icontains=s)
                    | Q(last_name__unaccent__icontains=s)
                    | Q(company__name__unaccent__icontains=s)
                    | Q(
                        user_attendance__team__subsidiary__city__name__unaccent__icontains=s
                    )
                    | Q(
                        user_attendance__team__subsidiary__company__name__unaccent__icontains=s
                    )
                    | Q(
                        user_attendance__team__subsidiary__address_street__unaccent__icontains=s
                    )
                    | Q(user_attendance__team__name__unaccent__icontains=s)
                    | Q(team__subsidiary__city__name__unaccent__icontains=s)
                    | Q(team__subsidiary__company__name__unaccent__icontains=s)
                    | Q(team__subsidiary__address_street__unaccent__icontains=s)
                    | Q(team__name__unaccent__icontains=s),
                )

        company_search = self.request.GET.get(
            "columns[0][search][value]", None
        )  # the column 7 means always company column
        if company_search:
            self.queryset_filtered = True
            querystring = self.competition.get_company_querystring()

            m = re.match(r'^"(.*)"$', company_search)
            if m:
                search_operation = "iexact"
                company_search = m.group(1)
            else:
                search_operation = "icontains"
            qs = qs.filter(
                **{
                    "%s__name__unaccent__%s"
                    % (querystring, search_operation): company_search
                }
            )

        return qs
