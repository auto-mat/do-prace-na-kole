# -*- coding: utf-8 -*-
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
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

import models
try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    from ordereddict import OrderedDict
from django.db.models import Sum, F, Q, Count
import util

def get_competitors(self):
    if self.without_admission:
        filter_query = {}
        if self.competitor_type == 'single_user' or self.competitor_type == 'liberos':
            filter_query['user__is_active'] = True
            filter_query['approved_for_team'] = 'approved'
            if self.city:
                filter_query['team__subsidiary__city'] = self.city
            if self.company:
                filter_query['team__subsidiary__company'] = self.company
            query = models.UserProfile.objects.filter(**filter_query)
        elif self.competitor_type == 'team':
            filter_query = {}
            if self.city:
                filter_query['subsidiary__city'] = self.city
            if self.company:
                filter_query['subsidiary__company'] = self.company
            query = models.Team.objects.filter(**filter_query)
        elif self.competitor_type == 'company':
            if self.company:
                filter_query['company'] = self.company
            query = models.Company.objects.filter(**filter_query)
    else:
        if self.competitor_type == 'single_user' or self.competitor_type == 'liberos':
            query = self.user_competitors.all()
        elif self.competitor_type == 'team':
            query = self.team_competitors.all()
        elif self.competitor_type == 'company':
            query = self.company_competitors.all()

    if self.competitor_type == 'single_user':
        query = query.filter(team__member_count__gt = 1)
    elif self.competitor_type == 'liberos':
        query = query.filter(team__member_count__lte = 1)
    elif self.competitor_type == 'team':
        query = query.filter(member_count__gt = 1)
    elif self.competitor_type == 'company':
        pass

    return query

def get_results(self):
    competitors = self.results.order_by('-result')
    return competitors

def get_competitions(userprofile):
    competitions = models.Competition.objects

    if userprofile.is_libero():
        competitions = competitions.filter(competitor_type = 'liberos')
    else:
        competitions = competitions.exclude(competitor_type = 'liberos')

    competitions = competitions.filter(
            (
                  (Q(company = None) | Q(company = userprofile.team.subsidiary.company))
                & (Q(city = None)    | Q(city = userprofile.team.subsidiary.city))
            )
        ).distinct()
    return competitions

def get_competitions_with_admission(userprofile):
    competitions = get_competitions(userprofile).filter(
            (
                Q(without_admission = True)
            ) | (
                Q(without_admission = False)
                & (
                    Q(user_competitors = userprofile)
                    | Q(team_competitors = userprofile.team)
                    | Q(company_competitors = userprofile.team.subsidiary.company)
                )
            )
        ).distinct()
    return competitions

def has_distance_competition(userprofile):
    competitions = get_competitions_with_admission(userprofile)
    competitions = competitions.filter(type = 'length', without_admission=False)
    return competitions.count() > 0

def get_competitions_with_info(userprofile):
    competitions = get_competitions(userprofile)

    for competition in competitions:
        results = competition.get_results()

        if not results:
            continue

        competition.competitor_count = results.exclude(result = None).count()

        if competition.competitor_type == 'single_user' or competition.competitor_type == 'liberos':
            my_results = results.get(userprofile = userprofile)
        elif competition.competitor_type == 'team':
            my_results = results.get(team = userprofile.team)
        elif competition.competitor_type == 'company':
            raise NotImplementedError("Company competitions are not working yet")

        my_results.position = results.filter(result__gt = my_results.result).count()

        competition.my_results = my_results
    return competitions
