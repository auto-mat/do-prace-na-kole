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
import threading

def get_competitors(self):
    if self.without_admission:
        filter_query = {}
        filter_query['campaign'] = self.campaign
        if self.competitor_type == 'single_user' or self.competitor_type == 'liberos':
            filter_query['userprofile__user__is_active'] = True
            filter_query['approved_for_team'] = 'approved'
            if self.city:
                filter_query['team__subsidiary__city'] = self.city
            if self.company:
                filter_query['team__subsidiary__company'] = self.company
            if self.sex:
                filter_query['userprofile__sex'] = self.sex
            query = models.UserAttendance.objects.filter(**filter_query)
        elif self.competitor_type == 'team':
            filter_query = {}
            filter_query['campaign'] = self.campaign
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
            query = self.user_attendance_competitors.all()
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
    competitors = self.results.exclude(result=None).order_by('-result', '-team__member_count')
    return competitors

def get_competitions(user_attendance):
    competitions = models.Competition.objects.filter(is_public=True, campaign=user_attendance.campaign)

    if user_attendance.is_libero():
        competitions = competitions.filter(competitor_type = 'liberos')
    else:
        competitions = competitions.exclude(competitor_type = 'liberos')

    competitions = competitions.filter(
            (
                  (Q(company=None) | Q(company=(user_attendance.company())))
                & (Q(sex=None)     | Q(sex=(user_attendance.userprofile.sex)))
                & (Q(city=None)    | Q(city=(user_attendance.team.subsidiary.city if user_attendance.team else None)))
            )
        ).distinct()
    return competitions

def get_competitions_with_admission(user_attendance):
    competitions = get_competitions(user_attendance).filter(
            (
                Q(without_admission = True)
            ) | (
                Q(without_admission = False)
                & (
                    Q(user_attendance_competitors = user_attendance)
                    | Q(team_competitors = user_attendance.team)
                    | Q(company_competitors = user_attendance.team.subsidiary.company)
                )
            )
        ).distinct()
    return competitions

def has_distance_competition(user_attendance):
    competitions = get_competitions_with_admission(user_attendance)
    competitions = competitions.filter(type = 'length')
    return competitions.count() > 0

def get_competitions_with_info(user_attendance):
    competitions = get_competitions(user_attendance).select_related('city', 'campaign', 'company')

    for competition in competitions:
        results = competition.get_results()

        if not results:
            continue

        competition.competitor_count = results.exclude(result = None).count()

        try:
            if competition.competitor_type == 'single_user' or competition.competitor_type == 'liberos':
                my_results = results.get(user_attendance = user_attendance)
            elif competition.competitor_type == 'team':
                my_results = results.get(team = user_attendance.team)
            elif competition.competitor_type == 'company':
                my_results = results.get(company = user_attendance.company())
        except models.CompetitionResult.DoesNotExist:
            my_results = models.CompetitionResult()

        if my_results.result:
            my_results.position = results.filter(result__gt = my_results.result).count() + 1
        else:
            my_results.position = "-"

        competition.my_results = my_results
    return competitions

def get_userprofile_frequency(user_attendance):
    trips_from = models.Trip.objects.filter(user_attendance=user_attendance, trip_from=True).count()
    trips_to   = models.Trip.objects.filter(user_attendance=user_attendance, trip_to=True).count()
    return trips_from + trips_to

def get_userprofile_length(user_attendance):
    # distance_from = models.Trip.objects.filter(user_attendance=user_attendance).aggregate(Sum('distance_from'))['distance_from__sum'] or 0
    # distance_to   = models.Trip.objects.filter(user_attendance=user_attendance).aggregate(Sum('distance_to'))['distance_to__sum'] or 0
    distance = 0
    for trip in models.Trip.objects.filter(user_attendance=user_attendance).select_related('user_attendance__campaign'):
        distance += trip.distance_from_cutted()
        distance += trip.distance_to_cutted()
    return distance

def get_team_frequency(team):
    member_count = team.member_count
    members = team.members().all()
        
    if member_count == 0:
        return None
    trips_from = models.Trip.objects.filter(user_attendance__in=members, trip_from=True).count()
    trips_to   = models.Trip.objects.filter(user_attendance__in=members, trip_to=True).count()
    return float(trips_from + trips_to) / float(member_count)

def get_team_length(team):
    member_count = team.member_count
    members = team.members().all()
        
    if member_count == 0:
        return None
    members = team.members().all()
    # distance_from = models.Trip.objects.filter(user__in = members).aggregate(Sum('distance_from'))['distance_from__sum'] or 0
    # distance_to   = models.Trip.objects.filter(user__in = members).aggregate(Sum('distance_to'))['distance_to__sum'] or 0
    distance = 0
    for member in members:
        distance += get_userprofile_length(member)
    return float(distance) / float(member_count)

def recalculate_result_competition(competition):
    models.CompetitionResult.objects.filter(competition = competition).delete()
    for competitor in competition.get_competitors():
        recalculate_result(competition, competitor)
    
class RecalculateResultCompetitorThread(threading.Thread):
    def __init__(self, user_attendance, **kwargs):
        self.user_attendance = user_attendance
        super(RecalculateResultCompetitorThread, self).__init__(**kwargs)

    def run(self):
        recalculate_result_competitor_nothread(self.user_attendance)

def recalculate_result_competitor_nothread(user_attendance):
    for competition in get_competitions(user_attendance):
        if competition.competitor_type == 'team' and user_attendance.team:
            recalculate_result(competition, user_attendance.team)
        elif competition.competitor_type == 'single_user' or competition.competitor_type == 'liberos':
            recalculate_result(competition, user_attendance)
        elif competition.competitor_type == 'company':
            recalculate_result(competition, user_attendance.company())

def recalculate_result_competitor(user_attendance):
    RecalculateResultCompetitorThread(user_attendance).start()

def recalculate_results_team(team):
    #TODO: it's enough to recalculate just team competitions
    for team_member in team.members():
        recalculate_result_competitor(team_member)

def recalculate_result(competition, competitor):
    if competitor == None:
        return

    if competition.competitor_type == 'team':
        team = competitor

        if team.coordinator_campaign and not competition.has_admission(team.coordinator_campaign):
            models.CompetitionResult.objects.filter(team = team, competition = competition).delete()
            return

        competition_result, created = models.CompetitionResult.objects.get_or_create(team = team, competition = competition)

        member_count = team.member_count
        members = team.members()
            
        if member_count == 0:
            competition_result.result = None
            competition_result.save()
            return

        if competition.type == 'questionnaire':
            points = models.Choice.objects.filter(answer__user_attendance__in = members, answer__question__competition = competition).aggregate(Sum('points'))['points__sum'] or 0
            points_given = models.Answer.objects.filter(user_attendance__in = members, question__competition = competition).aggregate(Sum('points_given'))['points_given__sum'] or 0
            competition_result.result = float(points + points_given)
        elif competition.type == 'length':
            competition_result.result = get_team_length(team)
        elif competition.type == 'frequency':
            competition_result.result = get_team_frequency(team)
    
    elif competition.competitor_type == 'single_user' or competition.competitor_type == 'liberos':
        user_attendance = competitor
        if not (competition.has_admission(user_attendance) and user_attendance.userprofile.user.is_active and user_attendance.approved_for_team == 'approved'):
            models.CompetitionResult.objects.filter(user_attendance = user_attendance, competition = competition).delete()
            return

        competition_result, created = models.CompetitionResult.objects.get_or_create(user_attendance = user_attendance, competition = competition)

        if competition.type == 'questionnaire':
            points = models.Choice.objects.filter(answer__user_attendance = user_attendance, answer__question__competition = competition).aggregate(Sum('points'))['points__sum'] or 0
            points_given = models.Answer.objects.filter(user_attendance = user_attendance, question__competition = competition).aggregate(Sum('points_given'))['points_given__sum'] or 0
            competition_result.result = points + points_given
        elif competition.type == 'length':
            competition_result.result = get_userprofile_length(user_attendance)
        elif competition.type == 'frequency':
            competition_result.result = get_userprofile_frequency(user_attendance)

    elif competition.competitor_type == 'company':
        company = competitor
        try:
            company_admin = company.company_admin.get(campaign=competition.campaign).user_attendance()
        except models.CompanyAdmin.DoesNotExist:
            return
        if not (competition.has_admission(company_admin)):
            models.CompetitionResult.objects.filter(company=company, competition=competition).delete()
            return

        competition_result, created = models.CompetitionResult.objects.get_or_create(company=company, competition=competition)

        if competition.type == 'questionnaire':
            points = models.Choice.objects.filter(answer__user_attendance=company_admin, answer__question__competition=competition).aggregate(Sum('points'))['points__sum'] or 0
            points_given = models.Answer.objects.filter(user_attendance=company_admin, question__competition=competition).aggregate(Sum('points_given'))['points_given__sum'] or 0
            competition_result.result = points + points_given
        elif competition.type == 'length' or  competition.type == 'frequency':
            raise NotImplementedError("Company length and frequency competitions are not implemented yet")

    competition_result.save()

