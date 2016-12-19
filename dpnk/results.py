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

from django.db.models import Q, Sum

from . import tasks, util
from .models import Answer, Choice, City, Company, Competition, CompetitionResult, Team, Trip, UserAttendance


def get_competitors_without_admission(competition):  # noqa
    filter_query = {}
    if competition.competitor_type == 'single_user' or competition.competitor_type == 'liberos':
        filter_query['campaign'] = competition.campaign
        filter_query['userprofile__user__is_active'] = True
        filter_query['approved_for_team'] = 'approved'
        if competition.city:
            cities = competition.city.all()
            if cities:
                filter_query['team__subsidiary__city__in'] = cities
        if competition.company:
            filter_query['team__subsidiary__company'] = competition.company
        if competition.sex:
            filter_query['userprofile__sex'] = competition.sex
        return UserAttendance.objects.filter(**filter_query)
    elif competition.competitor_type == 'team':
        filter_query = {}
        filter_query['campaign'] = competition.campaign
        if competition.city:
            cities = competition.city.all()
            if cities:
                filter_query['subsidiary__city__in'] = cities
        if competition.company:
            filter_query['subsidiary__company'] = competition.company
        return Team.objects.filter(**filter_query)
    elif competition.competitor_type == 'company':
        if competition.city:
            cities = competition.city.all()
            if cities:
                filter_query['subsidiaries__city__in'] = cities
        if competition.company:
            filter_query['pk'] = competition.company.pk
        return Company.objects.filter(**filter_query)


def get_competitors(competition, potencial_competitors=False):
    """ Return query with competitors attending given competition """
    if competition.without_admission or potencial_competitors:
        query = get_competitors_without_admission(competition)
    else:
        if competition.competitor_type == 'single_user' or competition.competitor_type == 'liberos':
            query = competition.user_attendance_competitors.all()
        elif competition.competitor_type == 'team':
            query = competition.team_competitors.all()
        elif competition.competitor_type == 'company':
            query = competition.company_competitors.all()

    if competition.competitor_type == 'single_user':
        pass
    elif competition.competitor_type == 'liberos':
        query = query.filter(team__member_count__lte=1)
    elif competition.competitor_type == 'team':
        query = query.filter(member_count__gt=1)
    elif competition.competitor_type == 'company':
        pass

    return query


def get_results(self):
    competitors = self.results.exclude(result=None).order_by('-result', '-team__member_count')
    return competitors


def get_competitions(user_attendance):
    competitions = Competition.objects.filter(is_public=True, campaign=user_attendance.campaign)

    if user_attendance.is_libero():
        competitions = competitions.filter(competitor_type__in=('liberos', 'single_user'))
    else:
        competitions = competitions.exclude(competitor_type='liberos')

    company_admin = user_attendance.related_company_admin
    if company_admin:
        administrated_company = company_admin.administrated_company
        administrated_cities = City.objects.filter(subsidiary__company=administrated_company).distinct()
    else:
        administrated_company = None
        administrated_cities = []

    competitions = competitions.filter(
        (
            Q(competitor_type__in=('liberos', 'team', 'single_user')) &
            (Q(company=None) | Q(company=(user_attendance.company()))) &
            (Q(sex=None) | Q(sex=(user_attendance.userprofile.sex))) &
            (Q(city=None) | Q(city=(user_attendance.team.subsidiary.city if user_attendance.team else None)))
        ) | (
            Q(competitor_type__in=('company',)) &
            (Q(company=None) | Q(company=administrated_company)) &
            (Q(city=None) | Q(city__in=administrated_cities))
        ),
    ).distinct()
    return competitions


def get_competitions_without_admission(user_attendance):
    competitions = get_competitions(user_attendance).filter(
        Q(without_admission=False) & ~(
            Q(user_attendance_competitors=user_attendance) |
            Q(team_competitors=user_attendance.team) |
            Q(company_competitors=user_attendance.company())
        ),
    ).distinct()
    return competitions


def get_competitions_with_info(user_attendance):
    competitions = get_competitions(user_attendance).select_related('campaign', 'company')

    for competition in competitions:
        results = competition.get_results()

        if not results:
            continue

        competition.competitor_count = results.exclude(result=None).count()

        try:
            if competition.competitor_type == 'single_user' or competition.competitor_type == 'liberos':
                my_results = results.get(user_attendance=user_attendance)
            elif competition.competitor_type == 'team':
                my_results = results.get(team=user_attendance.team)
            elif competition.competitor_type == 'company':
                my_results = results.get(company=user_attendance.company())
        except CompetitionResult.DoesNotExist:
            my_results = CompetitionResult()

        if my_results.result:
            my_results.position = results.filter(result__gt=my_results.result).count() + 1
        else:
            my_results.position = "-"

        competition.my_results = my_results
    return competitions


def get_rides_count(user_attendance, competition, day=None):
    if not day:
        day = util.today()
    days = util.days(competition, day)
    return Trip.objects.filter(user_attendance=user_attendance, commute_mode__in=('bicycle', 'by_foot'), date__in=days).count()


def get_minimum_rides_base_proportional(competition, day):
    days_count = util.days_count(competition, competition.date_to)
    days_count_till_now = util.days_count(competition, day)
    return int(competition.get_minimum_rides_base() * (days_count_till_now / days_count))


def get_working_trips_count(user_attendance, competition=None, day=None):
    if not day:
        day = util.today()
    non_working_days = util.non_working_days(competition, day)
    working_days = util.working_days(competition, day)
    trips_in_non_working_day = Trip.objects.filter(user_attendance=user_attendance, commute_mode__in=('bicycle', 'by_foot', 'by_other_vehicle'), date__in=non_working_days).count()
    non_working_rides_in_working_day = Trip.objects.filter(user_attendance=user_attendance, commute_mode='no_work', date__in=working_days).count()
    working_days_count = len(util.working_days(competition))
    working_trips_count = working_days_count * 2 + trips_in_non_working_day - non_working_rides_in_working_day
    return max(working_trips_count, get_minimum_rides_base_proportional(competition, day))


def get_team_frequency(user_attendancies, competition=None, day=None):
    working_trips_count = 0
    rides_count = 0

    for user_attendance in user_attendancies:
        working_trips_count += get_working_trips_count(user_attendance, competition, day)
        rides_count += get_rides_count(user_attendance, competition, day)
    if working_trips_count == 0:
        return 0, 0, 0
    return rides_count, working_trips_count, float(rides_count) / working_trips_count


def get_userprofile_nonreduced_length(user_attendances, competition):
    days = util.days(competition)
    return Trip.objects.filter(user_attendance__in=user_attendances, commute_mode__in=('bicycle', 'by_foot'), date__in=days).aggregate(Sum('distance'))['distance__sum'] or 0


def get_userprofile_length(user_attendances, competition):
    return get_userprofile_nonreduced_length(user_attendances, competition)

    # In 2016 the trip_plus_distance was disabled
    # trip_plus_distance = (user_attendance.campaign.trip_plus_distance or 0) + (user_attendance.get_distance() or 0)
    # distance_from = (Trip.objects.filter(user_attendance=user_attendance, is_working_ride_from=True, trip_from=True, distance_from__lt=trip_plus_distance).\
    #       aggregate(Sum('distance_from'))['distance_from__sum'] or 0) + \
    #     Trip.objects.filter(user_attendance=user_attendance, is_working_ride_from=True, trip_from=True, distance_from__gte=trip_plus_distance).count() * (trip_plus_distance)
    # distance_to = (Trip.objects.filter(user_attendance=user_attendance, is_working_ride_to=True, trip_to=True, distance_to__lt=trip_plus_distance).\
    #       aggregate(Sum('distance_to'))['distance_to__sum'] or 0) + \
    #     Trip.objects.filter(user_attendance=user_attendance, is_working_ride_to=True, trip_to=True, distance_to__gte=trip_plus_distance).count() * (trip_plus_distance)
    # return distance_from + distance_to


def get_userprofile_frequency(user_attendance, competition=None, day=None):
    return get_team_frequency([user_attendance], competition, day)


def get_team_length(team, competition):
    member_count = team.member_count
    members = team.members().all()

    if member_count == 0:
        return None, None, None
    members = team.members().all()
    # distance_from = Trip.objects.filter(user__in=members).aggregate(Sum('distance_from'))['distance_from__sum'] or 0
    # distance_to   = Trip.objects.filter(user__in=members).aggregate(Sum('distance_to'))['distance_to__sum'] or 0
    distance = 0
    for member in members:
        distance += get_userprofile_length([member], competition)
    return distance, member_count, float(distance) / float(member_count)


def recalculate_result_competition(competition):
    CompetitionResult.objects.filter(competition=competition).delete()
    for competitor in competition.get_competitors():
        recalculate_result(competition, competitor)


def recalculate_result_competitor_nothread(user_attendance):
    for competition in get_competitions(user_attendance):
        if competition.competitor_type == 'team' and user_attendance.team:
            recalculate_result(competition, user_attendance.team)
        elif competition.competitor_type == 'single_user' or competition.competitor_type == 'liberos':
            recalculate_result(competition, user_attendance)
        elif competition.competitor_type == 'company':
            recalculate_result(competition, user_attendance.company())


def recalculate_result_competitor(user_attendance):
    tasks.recalculate_competitor_task.apply_async([user_attendance.pk])


def recalculate_results_team(team):
    # TODO: it's enough to recalculate just team competitions
    for team_member in team.members():
        recalculate_result_competitor(team_member)


def points_questionnaire(user_attendances, competition):
    points = Choice.objects.filter(answer__user_attendance__in=user_attendances, answer__question__competition=competition).aggregate(Sum('points'))['points__sum'] or 0
    points_given = Answer.objects.filter(user_attendance__in=user_attendances, question__competition=competition).aggregate(Sum('points_given'))['points_given__sum'] or 0
    return points, points_given


def recalculate_result(competition, competitor):  # noqa
    if competitor is None:
        return

    if competition.competitor_type == 'team':
        team = competitor

        competition_result, created = CompetitionResult.objects.get_or_create(team=team, competition=competition)

        member_count = team.member_count
        members = team.members()

        if member_count == 0:
            competition_result.result = None
            competition_result.save()
            return

        if competition.type == 'questionnaire':
            points, points_given = points_questionnaire(members, competition)
            competition_result.result = float(points + points_given)
        elif competition.type == 'length':
            competition_result.result_divident, competition_result.result_divisor, competition_result.result = get_team_length(team, competition)
        elif competition.type == 'frequency':
            competition_result.result_divident, competition_result.result_divisor, competition_result.result = get_team_frequency(team.members(), competition)

    elif competition.competitor_type == 'single_user' or competition.competitor_type == 'liberos':
        user_attendance = competitor
        if not (competition.has_admission(user_attendance) and user_attendance.userprofile.user.is_active and user_attendance.approved_for_team == 'approved'):
            CompetitionResult.objects.filter(user_attendance=user_attendance, competition=competition).delete()
            return

        competition_result, created = CompetitionResult.objects.get_or_create(user_attendance=user_attendance, competition=competition)

        if competition.type == 'questionnaire':
            points, points_given = points_questionnaire([user_attendance], competition)
            competition_result.result = points + points_given
        elif competition.type == 'length':
            competition_result.result = get_userprofile_length([user_attendance], competition)
        elif competition.type == 'frequency':
            competition_result.result_divident, competition_result.result_divisor, competition_result.result = get_userprofile_frequency(user_attendance, competition)

    elif competition.competitor_type == 'company':
        company = competitor
        user_attendances = UserAttendance.objects.filter(related_company_admin__administrated_company=company, campaign=competition.campaign)
        if not user_attendances:
            CompetitionResult.objects.filter(company=company, competition=competition).delete()
            return

        competition_result, created = CompetitionResult.objects.get_or_create(company=company, competition=competition)

        if competition.type == 'questionnaire':
            points, points_given = points_questionnaire(user_attendances, competition)
            competition_result.result = points + points_given
        elif competition.type == 'length':
            competition_result.result = get_userprofile_length(user_attendances, competition)
        elif competition.type == 'frequency':
            competition_result.result_divident, competition_result.result_divisor, competition_result.result = get_team_frequency(user_attendances, competition)

    competition_result.save()
