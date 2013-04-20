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
import datetime

def get_competitors(self):
    if self.without_admission:
        filter_query = {}
        if self.competitor_type == 'single_user' or self.competitor_type == 'liberos':
            filter_query['user__is_active'] = True
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

    if self.competitor_type == 'single_user' or self.competitor_type == 'liberos':
        query = query.annotate(team_member_count=Sum('team__users__user__is_active'))
    elif self.competitor_type == 'team':
        query = query.annotate(team_member_count=Sum('users__user__is_active'))
    elif self.competitor_type == 'company':
        query = query.annotate(team_member_count=Sum('subsidiaries__teams__users__user__is_active'))

    if self.competitor_type == 'liberos':
        query = query.filter(team_member_count__lte = 1)
    else:
        query = query.filter(team_member_count__gt = 1)
    return query

def get_results(self):
    competitors = self.get_competitors()

    # Can't it be done with annotation queries like this?
    #result = competitors.annotate(result = Sum('answer__choices__points')).order_by('-result')

    if self.type == 'length' or self.type == 'frequency':
        field = 'distance' if self.type == 'length' else 'trip'
        if self.competitor_type == 'single_user' or self.competitor_type == 'liberos':
            #result = competitors.annotate(trip_to = Sum('user_trips__trip_to')).annotate(trip_from = Sum('user_trips__trip_from')).values('trip_to', 'trip_from').extra(
            #    select={ 'result':'trip_to+trip_from'},
            #    #order_by=['-result']
            #)
            result = competitors.extra(
                select=OrderedDict([
                    ('userid', 'dpnk_userprofile.id'),
                    ('result', """SELECT sum(IFNULL(`dpnk_trip`.`%(field)s_to` + `dpnk_trip`.`%(field)s_from` ,IFNULL(`dpnk_trip`.`%(field)s_to`, `dpnk_trip`.`%(field)s_from`))) 
                               FROM dpnk_trip
                               LEFT OUTER JOIN dpnk_userprofile ON (dpnk_trip.user_id = dpnk_userprofile.id)
                               LEFT OUTER JOIN auth_user ON (dpnk_userprofile.user_id = auth_user.id)
                               WHERE auth_user.is_active=True AND dpnk_trip.user_id=userid""" % {'field': field})
                    ]),
                order_by=['-result']
                )
            return result
        elif self.competitor_type == 'team':
            sum_select =   """SELECT sum(IFNULL(`dpnk_trip`.`%(field)s_to` + `dpnk_trip`.`%(field)s_from` ,IFNULL(`dpnk_trip`.`%(field)s_to`, `dpnk_trip`.`%(field)s_from`)))
                            FROM dpnk_trip 
                            LEFT OUTER JOIN dpnk_userprofile ON (dpnk_trip.user_id = dpnk_userprofile.id) 
                            LEFT OUTER JOIN auth_user ON (dpnk_userprofile.user_id = auth_user.id) 
                            WHERE auth_user.is_active=True AND dpnk_userprofile.team_id=teamid""" % {'field': field}
            count_select =  """SELECT count(dpnk_userprofile.id) 
                            FROM dpnk_userprofile 
                            LEFT OUTER JOIN auth_user ON (dpnk_userprofile.user_id = auth_user.id) 
                            WHERE auth_user.is_active=True AND dpnk_userprofile.team_id=teamid"""
            result = competitors.extra(
                select=OrderedDict([
                    ('teamid', 'dpnk_team.id'),
                    ('sum_distance', sum_select),
                    ('user_count', count_select),
                    ('result', "(%s)/(%s)" % (sum_select, count_select))
                    ]),
                order_by=['-result']
                )
            return result
        elif self.competitor_type == 'company':
            sum_select =   """SELECT sum(IFNULL(`dpnk_trip`.`%(field)s_to` + `dpnk_trip`.`%(field)s_from` ,IFNULL(`dpnk_trip`.`%(field)s_to`, `dpnk_trip`.`%(field)s_from`)))
                            FROM dpnk_trip 
                            LEFT OUTER JOIN dpnk_userprofile ON (dpnk_trip.user_id = dpnk_userprofile.id) 
                            LEFT OUTER JOIN dpnk_team ON (dpnk_userprofile.team_id = dpnk_team.id) 
                            LEFT OUTER JOIN dpnk_subsidiary ON (dpnk_team.subsidiary_id = dpnk_subsidiary.id) 
                            LEFT OUTER JOIN auth_user ON (dpnk_userprofile.user_id = auth_user.id) 
                            WHERE auth_user.is_active=True and dpnk_subsidiary.company_id=companyid""" % {'field': field}
            count_select =  """SELECT count(dpnk_userprofile.id) 
                            FROM dpnk_userprofile 
                            LEFT OUTER JOIN dpnk_team ON (dpnk_userprofile.team_id = dpnk_team.id) 
                            LEFT OUTER JOIN dpnk_subsidiary ON (dpnk_team.subsidiary_id = dpnk_subsidiary.id) 
                            LEFT OUTER JOIN auth_user ON (dpnk_userprofile.user_id = auth_user.id) 
                            WHERE auth_user.is_active=True AND dpnk_subsidiary.company_id=companyid"""
            result = competitors.extra(
                select=OrderedDict([
                    ('companyid', 'dpnk_company.id'),
                    ('sum_distance', sum_select),
                    ('user_count', count_select),
                    ('result', "(%s)/(%s)" % (sum_select, count_select))
                    ]),
                order_by=['-result']
                )
            return result
    elif self.type == 'questionnaire':
        select_dict = OrderedDict()

        if self.competitor_type == 'single_user' or self.competitor_type == 'liberos':
            select_dict['userid'] = 'dpnk_userprofile.id'
        elif self.competitor_type == 'team':
            select_dict['teamid'] = 'dpnk_team.id'
        elif self.competitor_type == 'company':
            select_dict['companyid'] = 'dpnk_company.id'

        #query_str ="""SELECT sum(IF(dpnk_answer.points_given is null, dpnk_choice.points, dpnk_answer.points_given))
        query_str ="""SELECT sum(if(dpnk_answer.points_given is Null, 0, dpnk_answer.points_given) + if(dpnk_choice.points is Null, 0, dpnk_choice.points))
                FROM dpnk_answer 
                LEFT OUTER JOIN dpnk_question ON (dpnk_answer.question_id = dpnk_question.id) 
                LEFT OUTER JOIN dpnk_answer_choices ON (dpnk_answer_choices.answer_id = dpnk_answer.id) 
                LEFT OUTER JOIN dpnk_choice ON (dpnk_answer_choices.choice_id = dpnk_choice.id) """

        if self.competitor_type == 'team' or self.competitor_type == 'company':
                query_str += """LEFT OUTER JOIN dpnk_userprofile ON (dpnk_answer.user_id = dpnk_userprofile.id)
                LEFT OUTER JOIN auth_user ON (dpnk_userprofile.user_id = auth_user.id) """
        if self.competitor_type == 'company':
                query_str += """LEFT OUTER JOIN dpnk_team ON (dpnk_userprofile.team_id = dpnk_team.id) 
                LEFT OUTER JOIN dpnk_subsidiary ON (dpnk_team.subsidiary_id = dpnk_subsidiary.id) """ 
        query_str += " WHERE "

        if self.competitor_type == 'single_user' or self.competitor_type == 'liberos':
            query_str += "dpnk_answer.user_id=userid " 
        elif self.competitor_type == 'team':
            query_str += "dpnk_userprofile.team_id = teamid "
        elif self.competitor_type == 'company':
            query_str += "dpnk_subsidiary.company_id = companyid "
        query_str += """AND dpnk_question.competition_id=%s AND auth_user.is_active=True""" % self.id

        select_dict['result'] = query_str

        result = competitors.extra(
            select=select_dict,
            order_by=['-result']
            )
        return result

def get_competitions(userprofile):
    competitions = models.Competition.objects.filter(
            (
                Q(without_admission = True)
                & (Q(company = None) | Q(company = userprofile.team.subsidiary.company))
                & (Q(city = None)    | Q(city = userprofile.team.subsidiary.city))
            ) | (
                Q(without_admission = False)
                & (
                    Q(user_competitors = userprofile)
                    | Q(team_competitors = userprofile.team)
                    | Q(company_competitors = userprofile.team.subsidiary.company)
                )
            )
        ).exclude(Q(date_from__gt = datetime.date.today())).distinct()
    return competitions

def has_distance_dompetition(userprofile):
    competitions = get_competitions(userprofile)
    competitions = competitions.filter(type = 'length')
    return competitions.count() > 0

def get_competitions_with_info(userprofile):
    competitions = get_competitions(userprofile)

    for competition in competitions:
        if competition.competitor_type == 'single_user' or competition.competitor_type == 'liberos':
            try:
                my_results = competition.get_results().get(pk = userprofile.pk)
            except models.UserProfile.DoesNotExist:
                my_results = None
            if not isinstance(my_results, models.UserProfile):
                my_results = None
        elif competition.competitor_type == 'team':
            try:
                my_results = competition.get_results().get(pk = userprofile.team.pk)
            except models.Team.DoesNotExist:
                my_results = None
            if not isinstance(my_results, models.Team):
                my_results = None
        elif competition.competitor_type == 'company':
            try:
                my_results = competition.get_results().get(pk = userprofile.team.subsidiary.company.pk)
            except models.Company.DoesNotExist:
                my_results = None
            if not isinstance(my_results, models.Company):
                my_results = None

        for i, competitor in enumerate(competition.get_results()):
            if competitor == my_results:
                my_results.position = i

        my_results.count = competition.get_results().count()

        #if my_results:
        #    #Big hack:
        #    result = my_results.result if my_results.result else 0
        #    where = '1)) HAVING (result > ' + str(result)
        #    my_results.position = competition.get_results().extra(where=[where]).count()

        competition.my_results = my_results
    return competitions

def get_competitions_for_admission(userprofile):
    competitions = models.Competition.objects

    if not userprofile.is_team_coordinator():
        competitions = competitions.exclude(competitor_type = 'team')

    if not userprofile.is_company_admin():
        competitions = competitions.exclude(competitor_type = 'company')

    competitions = competitions.filter(
                Q(without_admission = False)
                & (Q(company = None) | Q(company = userprofile.team.subsidiary.company))
                & (Q(city = None)    | Q(city = userprofile.team.subsidiary.city))
            ).exclude(
                (
                    Q(type = 'questionnaire')
                    & (Q(date_from__gt = datetime.date.today())
                    | Q(date_to__lte = datetime.date.today()))
                ) | (
                    (Q(type = 'length') | Q(type = 'frequency'))
                    & Q(date_from__lte = datetime.date.today())
                )
            ).distinct()
    return competitions
