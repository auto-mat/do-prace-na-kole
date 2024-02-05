# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2013 o.s. Auto*Mat
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

import itertools
import random

from django.db.models import F, Q

from .models import Competition, CompetitionResult, Team


def draw(competition_slug, limit=10):
    """Draw competitors above threshold in given competition"""

    competition = Competition.objects.get(slug=competition_slug)
    threshold = competition.campaign.minimum_percentage / 100.0
    condition = {}
    condition["competition"] = competition
    if competition.competition_type == "frequency":
        condition["result__gt"] = threshold

    results = CompetitionResult.objects.filter(**condition).order_by("result")

    if competition.competitor_type == "team":
        teams_all_members_paid = Team.objects.filter(
            Q(
                id__in=results.distinct().values_list("team_id", flat=True),
                users__userprofile__user__is_active=True,
                paid_member_count=F("member_count"),
                campaign=competition.campaign,
            )
        )
        results = results.filter(
            team_id__in=teams_all_members_paid.values_list("id", flat=True)
        )

    if (
        competition.competition_type == "frequency"
        and competition.competitor_type == "team"
    ):
        qs = []
        for i in (
            results.order_by("id")
            .distinct("id")
            .values("team__id", "team__member_count")
        ):
            qs.extend(
                itertools.repeat(
                    results.filter(team_id=i["team__id"]),
                    i["team__member_count"],
                )
            )
        first_qs = qs.pop(0)
        # Union querysets with allowing duplicates
        results = list(first_qs.union(*qs, all=True).order_by("result"))
        return sorted(results, key=lambda x: random.random())

    results = sorted(results[:limit], key=lambda x: random.random())

    return results
