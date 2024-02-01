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

from django.db.models import Q

from .models import Competition, CompetitionResult


def all_members_paid(team):
    """Has all members of team paid?"""
    paid = True
    if team.members.filter(
        Q(userprofile__user__is_active=True) & ~Q(payment_status="done")
    ):
        paid = False
    return paid


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
        results = [result for result in results if all_members_paid(result.team)]

    if (
        competition.competition_type == "frequency"
        and competition.competitor_type == "team"
    ):
        return draw_weighed(results)

    results = sorted(results[:limit], key=lambda x: random.random())

    return results


def draw_weighed(results):
    """Draw competitors weighed by count of team members"""

    result_members = []
    for result in results:
        result_members.extend(
            itertools.repeat(
                result,
                result.team.members.count(),
            )
        )
    result_members = sorted(result_members, key=lambda x: random.random())

    return result_members
