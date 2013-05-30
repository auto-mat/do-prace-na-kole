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
    competitions = models.Competition.objects.filter(is_public = True)

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

        try:
            if competition.competitor_type == 'single_user' or competition.competitor_type == 'liberos':
                my_results = results.get(userprofile = userprofile)
            elif competition.competitor_type == 'team':
                my_results = results.get(team = userprofile.team)
            elif competition.competitor_type == 'company':
                raise NotImplementedError("Company competitions are not working yet")
        except models.CompetitionResult.DoesNotExist:
            my_results = models.CompetitionResult()

        if my_results.result:
            my_results.position = results.filter(result__gt = my_results.result).count() + 1
        else:
            my_results.position = "-"

        competition.my_results = my_results
    return competitions

def get_userprofile_frequency(userprofile):
    trips_from = models.Trip.objects.filter(user=userprofile).aggregate(Sum('trip_from'))['trip_from__sum'] or 0
    trips_to   = models.Trip.objects.filter(user=userprofile).aggregate(Sum('trip_to'))['trip_to__sum'] or 0
    return trips_from + trips_to

def get_userprofile_length(userprofile):
    distance_from = models.Trip.objects.filter(user=userprofile).aggregate(Sum('distance_from'))['distance_from__sum'] or 0
    distance_to   = models.Trip.objects.filter(user=userprofile).aggregate(Sum('distance_to'))['distance_to__sum'] or 0
    return distance_from + distance_to

def get_team_frequency(team):
    member_count = team.members().count()
    members = team.members().all()
        
    if member_count == 0:
        return None
    trips_from = models.Trip.objects.filter(user__in = members).aggregate(Sum('trip_from'))['trip_from__sum'] or 0
    trips_to   = models.Trip.objects.filter(user__in = members).aggregate(Sum('trip_to'))['trip_to__sum'] or 0
    return float(trips_from + trips_to) / float(member_count)

def get_team_length(team):
    member_count = team.members().count()
    members = team.members().all()
        
    if member_count == 0:
        return None
    members = team.members().all()
    distance_from = models.Trip.objects.filter(user__in = members).aggregate(Sum('distance_from'))['distance_from__sum'] or 0
    distance_to   = models.Trip.objects.filter(user__in = members).aggregate(Sum('distance_to'))['distance_to__sum'] or 0
    return float(distance_from + distance_to) / float(member_count)

def recalculate_result_competition(competition):
    models.CompetitionResult.objects.filter(competition = competition).delete()
    for competitor in competition.get_competitors():
        recalculate_result(competition, competitor)
    

def recalculate_result_competitor(userprofile):
    for competition in models.Competition.objects.all():
        if competition.competitor_type == 'team':
            recalculate_result(competition, userprofile.team)
        elif competition.competitor_type == 'single_user' or competition.competitor_type == 'liberos':
            recalculate_result(competition, userprofile)
        elif competition.competitor_type == 'company':
            raise NotImplementedError("Company competitions are not working yet")

def recalculate_results_team(team):
    #TODO: it's enough to recalculate just team competitions
    for team_member in team.members():
        recalculate_result_competitor(team_member)

def recalculate_result(competition, competitor):
    if competition.competitor_type == 'team':
        team = competitor

        if team.coordinator and not competition.has_admission(team.coordinator):
            models.CompetitionResult.objects.filter(team = team, competition = competition).delete()
            return

        competition_result, created = models.CompetitionResult.objects.get_or_create(team = team, competition = competition)

        member_count = team.members().count()
        members = team.members()
            
        if member_count == 0:
            competition_result.result = None
            competition_result.save()
            return

        if competition.type == 'questionnaire':
            points = models.Choice.objects.filter(answer__user__in = members, answer__question__competition = competition).aggregate(Sum('points'))['points__sum'] or 0
            points_given = models.Answer.objects.filter(user__in = members, question__competition = competition).aggregate(Sum('points_given'))['points_given__sum'] or 0
            competition_result.result = float(points + points_given)
        elif competition.type == 'length':
            competition_result.result = get_team_length(team)
        elif competition.type == 'frequency':
            competition_result.result = get_team_frequency(team)
    
    elif competition.competitor_type == 'single_user' or competition.competitor_type == 'liberos':
        userprofile = competitor
        if not (competition.has_admission(userprofile) and userprofile.user.is_active and userprofile.approved_for_team == 'approved'):
            models.CompetitionResult.objects.filter(userprofile = userprofile, competition = competition).delete()
            return

        competition_result, created = models.CompetitionResult.objects.get_or_create(userprofile = userprofile, competition = competition)

        if competition.type == 'questionnaire':
            points = models.Choice.objects.filter(answer__user = userprofile, answer__question__competition = competition).aggregate(Sum('points'))['points__sum'] or 0
            points_given = models.Answer.objects.filter(user = userprofile, question__competition = competition).aggregate(Sum('points_given'))['points_given__sum'] or 0
            competition_result.result = points + points_given
        elif competition.type == 'length':
            competition_result.result = get_userprofile_length(userprofile)
        elif competition.type == 'frequency':
            competition_result.result = get_userprofile_frequency(userprofile)

    elif competition.competitor_type == 'company':
        raise NotImplementedError("Company competitions are not working yet")

    competition_result.save()

