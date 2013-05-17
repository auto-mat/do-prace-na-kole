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
from dpnk import util
import random

def all_members_paid(team):
    for user in team.members():
        if user.payment()['status'] != 'done':
            return False
    return True

def draw(competition_slug, threshold=0.66):
    competition = Competition.objects.get(slug=competition_slug)
    condition = {}
    condition['competition']=competition
    if competition.type == 'frequency':
        condition['result__gt'] = threshold * util.days_count() * 2.0
    results = CompetitionResult.objects.filter(**condition)
    results = sorted(results[:10], key=lambda x: random.random())

    if competition.competitor_type == 'team':
        results = [result for result in results if all_members_paid(result.team)]

    return results
