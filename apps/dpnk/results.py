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

import logging

from django.db.models import Q, Sum

from . import models, tasks, util
from .models import (
    Answer,
    Choice,
    City,
    Company,
    Competition,
    CompetitionResult,
    Team,
    Trip,
    UserAttendance,
)

logger = logging.getLogger(__name__)


def _filter_query_single_user(competition):
    filter_query = {}
    filter_query["campaign"] = competition.campaign
    filter_query["userprofile__user__is_active"] = True
    filter_query["approved_for_team"] = "approved"
    filter_query["payment_status__in"] = ("done", "no_admission")
    if competition.city:
        cities = competition.city.all()
        if cities:
            filter_query["team__subsidiary__city__in"] = cities
    if competition.company:
        filter_query["team__subsidiary__company"] = competition.company
    if competition.sex:
        filter_query["userprofile__sex"] = competition.sex
    return filter_query


def _filter_query_team(competition):
    filter_query = {}
    filter_query["campaign"] = competition.campaign
    if competition.city:
        cities = competition.city.all()
        if cities:
            filter_query["subsidiary__city__in"] = cities
    if competition.company:
        filter_query["subsidiary__company"] = competition.company
    return filter_query


def _filter_query_company(competition):
    filter_query = {}
    if competition.city:
        cities = competition.city.all()
        if cities:
            filter_query["subsidiaries__city__in"] = cities
    if competition.company:
        filter_query["pk"] = competition.company.pk
    return filter_query


def _get_competitors_without_admission(competition):
    if (
        competition.competitor_type == "single_user"
        or competition.competitor_type == "liberos"
    ):
        return UserAttendance.objects.filter(**_filter_query_single_user(competition))
    elif competition.competitor_type == "team":
        return Team.objects.filter(**_filter_query_team(competition))
    elif competition.competitor_type == "company":
        return Company.objects.filter(**_filter_query_company(competition))


def get_competitors(competition):
    """Return query with competitors attending given competition"""
    query = _get_competitors_without_admission(competition)

    if competition.competitor_type == "liberos":
        query = query.filter(team__paid_member_count__lte=1)
    if competition.competitor_type == "team":
        query = query.filter(paid_member_count__gt=1)

    return query


def get_results(self):
    competitors = self.results.exclude(result=None).order_by(
        "-result", "-team__paid_member_count", "-id"
    )
    return competitors


def get_competitions(user_attendance):
    competitions = Competition.objects.filter(
        is_public=True, campaign=user_attendance.campaign
    )

    if user_attendance.is_libero():
        competitions = competitions.filter(
            competitor_type__in=("liberos", "single_user")
        )
    else:
        competitions = competitions.exclude(competitor_type="liberos")

    company_admin = user_attendance.related_company_admin
    if company_admin:
        administrated_company = company_admin.administrated_company
        administrated_cities = City.objects.filter(
            subsidiary__company=administrated_company
        ).distinct()
    else:
        administrated_company = None
        administrated_cities = []

    competitions = competitions.filter(
        (
            Q(competitor_type__in=("liberos", "team", "single_user"))
            & (Q(company=None) | Q(company=(user_attendance.company())))
            & (Q(sex=None) | Q(sex=(user_attendance.userprofile.sex)))
            & (
                Q(city=None)
                | Q(
                    city=(
                        user_attendance.team.subsidiary.city
                        if user_attendance.team
                        else None
                    )
                )
            )
        )
        | (
            Q(competitor_type__in=("company",))
            & (Q(company=None) | Q(company=administrated_company))
            & (Q(city=None) | Q(city__in=administrated_cities))
        ),
    ).distinct()
    return competitions


def get_unanswered_questionnaires(user_attendance):
    competitions = (
        get_competitions(user_attendance)
        .filter(
            competition_type="questionnaire",
        )
        .exclude(
            question__answer__user_attendance=user_attendance,
        )
    )
    return competitions


def get_competitions_with_info(user_attendance, competition_types=None):
    competitions = get_competitions(user_attendance).select_related(
        "campaign", "company"
    )
    if competition_types:
        competitions = competitions.filter(competition_type__in=competition_types)

    for competition in competitions:
        results = competition.get_results()

        if not results:
            continue

        competition.competitor_count = results.exclude(result=None).count()

        try:
            if (
                competition.competitor_type == "single_user"
                or competition.competitor_type == "liberos"
            ):
                my_results = results.get(user_attendance=user_attendance)
            elif competition.competitor_type == "team":
                my_results = results.get(team=user_attendance.team)
            elif competition.competitor_type == "company":
                my_results = results.get(company=user_attendance.company())
        except CompetitionResult.DoesNotExist:
            my_results = CompetitionResult()

        if my_results.result:
            my_results.position = (
                results.filter(result__gt=my_results.result).count() + 1
            )
        else:
            my_results.position = "-"

        competition.my_results = my_results
    return competitions


def get_trips(user_attendances, competition, day=None, recreational=False):
    if not day:
        day = util.today()
    days = util.days(competition, day)
    trip_query = Trip.objects.all()
    if isinstance(competition, models.Phase):
        trip_query = trip_query.filter(
            commute_mode__eco=True, commute_mode__does_count=True
        )
    else:
        trip_query = trip_query.filter(commute_mode__in=competition.commute_modes.all())
        if competition.recreational:
            recreational = True
    if not recreational:
        trip_query = trip_query.filter(direction__in=("trip_to", "trip_from"))
    return trip_query.filter(
        user_attendance__in=user_attendances,
        date__in=days,
    )


def get_rides_count(user_attendance, competition, day=None, recreational=False):
    return get_trips(
        [user_attendance], competition, day, recreational=recreational
    ).count()


def get_minimum_rides_base_proportional(competition, day):
    days_count = util.days_count(competition, competition.date_to)
    days_count_till_now = util.days_count(competition, day)
    return int(
        competition.get_minimum_rides_base() * (days_count_till_now / days_count)
    )


def get_working_trips_count_without_minimum(
    user_attendance, competition=None, day=None
):
    if not day:
        day = util.today()
    non_working_days = util.non_working_days(competition, day)
    working_days = util.working_days(competition, day)
    trips_in_non_working_day = Trip.objects.filter(
        user_attendance=user_attendance,
        commute_mode__does_count=True,
        date__in=non_working_days,
    ).count()
    non_working_rides_in_working_day = Trip.objects.filter(
        user_attendance=user_attendance,
        commute_mode__does_count=False,
        date__in=working_days,
        direction__in=("trip_to", "trip_from"),
    ).count()
    working_days_count = len(util.working_days(competition))
    working_trips_count = (
        working_days_count * 2
        + trips_in_non_working_day
        - non_working_rides_in_working_day
    )
    return working_trips_count


def get_working_trips_count(user_attendance, competition=None, day=None):
    working_trips_count = get_working_trips_count_without_minimum(
        user_attendance, competition, day
    )
    return max(
        working_trips_count, get_minimum_rides_base_proportional(competition, day)
    )


def get_team_frequency(user_attendancies, competition=None, day=None):
    working_trips_count = 0
    rides_count = 0

    for user_attendance in user_attendancies:
        if user_attendance.campaign != competition.campaign:
            logger.error(
                "Campaign mismatch while recalculating results",
                extra={"user_attendance": user_attendance, "competition": competition},
            )
        working_trips_count += get_working_trips_count(
            user_attendance, competition, day
        )
        rides_count += get_rides_count(user_attendance, competition, day)
    if working_trips_count == 0:
        return 0, 0, 0
    return rides_count, working_trips_count, float(rides_count) / working_trips_count


def get_userprofile_length(user_attendances, competition, recreational=False):
    return (
        get_trips(user_attendances, competition, recreational=recreational).aggregate(
            Sum("distance")
        )["distance__sum"]
        or 0
    )


def get_userprofile_frequency(user_attendance, competition=None, day=None):
    return get_team_frequency([user_attendance], competition, day)


def get_team_length(team, competition):
    members = team.paid_members().all()
    distance = 0
    for member in members:
        distance += get_userprofile_length([member], competition)
    return distance


def get_team_avg_length(team, competition):
    member_count = team.paid_member_count

    if member_count == 0 or member_count is None:
        return 0, 0, 0

    distance = get_team_length(team, competition)
    return distance, member_count, float(distance) / float(member_count)


def recalculate_result_competition(competition):
    CompetitionResult.objects.filter(competition=competition).delete()
    for competitor in competition.get_competitors():
        recalculate_result(competition, competitor)


def recalculate_result_competitor_nothread(user_attendance):
    for competition in get_competitions(user_attendance):
        if competition.competitor_type == "team" and user_attendance.team:
            recalculate_result(competition, user_attendance.team)
        elif (
            competition.competitor_type == "single_user"
            or competition.competitor_type == "liberos"
        ):
            recalculate_result(competition, user_attendance)
        elif competition.competitor_type == "company":
            recalculate_result(competition, user_attendance.company())


def recalculate_result_competitor(user_attendance):
    tasks.recalculate_competitor_task.apply_async([user_attendance.pk])


def recalculate_results_team(team):
    # TODO: it's enough to recalculate just team competitions
    for team_member in team.paid_members():
        recalculate_result_competitor(team_member)


def points_questionnaire(user_attendances, competition):
    points = (
        Choice.objects.filter(
            answer__user_attendance__in=user_attendances,
            answer__question__competition=competition,
        ).aggregate(Sum("points"))["points__sum"]
        or 0
    )
    points_given = (
        Answer.objects.filter(
            user_attendance__in=user_attendances,
            question__competition=competition,
        ).aggregate(Sum("points_given"))["points_given__sum"]
        or 0
    )
    return points + points_given


def recalculate_result(competition, competitor):  # noqa
    if (
        competition.competition_type == "questionnaire"
        and type(competitor) == UserAttendance
        and not Answer.objects.filter(
            user_attendance=competitor, question__competition=competition
        ).exists()
    ):
        return

    if competitor is None:
        return

    if competition.competitor_type == "team":
        team = competitor

        competition_result, created = CompetitionResult.objects.get_or_create(
            team=team, competition=competition
        )

        member_count = team.paid_member_count
        members = team.paid_members()

        if member_count == 0:
            competition_result.result = None
            competition_result.save()
            return

        if competition.competition_type == "questionnaire":
            competition_result.result = float(
                points_questionnaire(members, competition)
            )
        elif competition.competition_type == "length":
            (
                competition_result.result_divident,
                competition_result.result_divisor,
                competition_result.result,
            ) = get_team_avg_length(team, competition)
        elif competition.competition_type == "frequency":
            (
                competition_result.result_divident,
                competition_result.result_divisor,
                competition_result.result,
            ) = get_team_frequency(team.paid_members(), competition)

    elif (
        competition.competitor_type == "single_user"
        or competition.competitor_type == "liberos"
    ):
        user_attendance = competitor
        if not (
            competition.has_admission(user_attendance)
            and user_attendance.userprofile.user.is_active
            and user_attendance.approved_for_team == "approved"
        ):
            CompetitionResult.objects.filter(
                user_attendance=user_attendance, competition=competition
            ).delete()
            return

        competition_result, created = CompetitionResult.objects.get_or_create(
            user_attendance=user_attendance, competition=competition
        )

        if competition.competition_type == "questionnaire":
            competition_result.result = points_questionnaire(
                [user_attendance], competition
            )
        elif competition.competition_type == "length":
            competition_result.result = get_userprofile_length(
                [user_attendance], competition
            )
        elif competition.competition_type == "frequency":
            (
                competition_result.result_divident,
                competition_result.result_divisor,
                competition_result.result,
            ) = get_userprofile_frequency(user_attendance, competition)

    elif competition.competitor_type == "company":
        company = competitor
        user_attendances = UserAttendance.objects.filter(
            team__subsidiary__company=company, campaign=competition.campaign
        )
        if not user_attendances:
            CompetitionResult.objects.filter(
                company=company, competition=competition
            ).delete()
            return

        competition_result, created = CompetitionResult.objects.get_or_create(
            company=company, competition=competition
        )

        if competition.competition_type == "questionnaire":
            competition_result.result = points_questionnaire(
                user_attendances, competition
            )
        elif competition.competition_type == "length":
            competition_result.result = get_userprofile_length(
                user_attendances, competition
            )
        elif competition.competition_type == "frequency":
            (
                competition_result.result_divident,
                competition_result.result_divisor,
                competition_result.result,
            ) = get_team_frequency(user_attendances, competition)

    competition_result.save()
