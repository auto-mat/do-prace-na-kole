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

from dpnk.models import CompetitionResult, Competition
import random


def all_members_paid(team):
    """Has all members of team paid?"""

    for userattendance in team.members():
        if userattendance.userprofile.user.is_active \
                and userattendance.payment()['status'] != 'done':
            return False
    return True


def draw(competition_slug, limit=10):
    """Draw competitors above threshold in given competition"""

    competition = Competition.objects.get(slug=competition_slug)
    threshold = competition.campaign.minimum_percentage / 100.0
    condition = {}
    condition['competition'] = competition
    if competition.type == 'frequency':
        condition['result__gt'] = threshold
    results = CompetitionResult.objects.filter(**condition)

    if competition.competitor_type == 'team':
        results = \
            [result for result in results if all_members_paid(result.team)]

    if competition.type == 'frequency' and competition.competitor_type == 'team':
        return draw_weighed(results)

    results = sorted(results[:limit], key=lambda x: random.random())

    return results


def draw_weighed(results):
    """Draw competitors weighed by count of team members"""

    result_members = []
    for result in results:
        for team_member in result.team.members():
            result_members.append(result)
    result_members = sorted(result_members, key=lambda x: random.random())

    return result_members
