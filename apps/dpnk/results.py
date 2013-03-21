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
from collections import OrderedDict
from django.db.models import Sum, F

def get_competitors(self):
    if self.without_admission:
        filter_query = {}
        if self.competitor_type == 'single_user':
            filter_query['user__is_active'] = True
            if self.city:
                filter_query['team__subsidiary__city'] = self.city
            if self.company:
                filter_query['team__subsidiary__company'] = self.company
            print filter_query
            return models.UserProfile.objects.filter(**filter_query)
        elif self.competitor_type == 'team':
            filter_query = {}
            if self.city:
                filter_query['subsidiary__city'] = self.city
            if self.company:
                filter_query['subsidiary__company'] = self.company
            print filter_query
            return models.Team.objects.filter(**filter_query)
        elif self.competitor_type == 'company':
            if self.company:
                filter_query['company'] = self.company
            print filter_query
            return models.Company.objects.filter(**filter_query)
    else:
        if self.competitor_type == 'single_user':
            return self.user_competitors.all()
        elif self.competitor_type == 'team':
            return self.team_competitors.all()
        elif self.competitor_type == 'company':
            return self.company_competitors.all()

def get_results(self):
    competitors = self.get_competitors()

    # Can't it be done with annotation queries like this?
    #result = competitors.annotate(result = Sum('answer__choices__points')).order_by('-result')

    if self.type == 'length' or self.type == 'frequency':
        field = 'distance' if self.type == 'length' else 'trip'
        if self.competitor_type == 'single_user':
            #result = competitors.annotate(trip_to = Sum('user_trips__trip_to')).annotate(trip_from = Sum('user_trips__trip_from')).values('trip_to', 'trip_from').extra(
            #    select={ 'result':'trip_to+trip_from'},
            #    #order_by=['-result']
            #)
            result = competitors.extra(
                select=OrderedDict([
                    ('userid', 'dpnk_userprofile.id'),
                    ('result', """SELECT sum(`dpnk_trip`.`%s_to`+`dpnk_trip`.`%s_from`)
                               FROM dpnk_trip
                               LEFT OUTER JOIN dpnk_userprofile ON (dpnk_trip.user_id = dpnk_userprofile.id)
                               LEFT OUTER JOIN auth_user ON (dpnk_userprofile.user_id = auth_user.id)
                               WHERE auth_user.is_active=True AND dpnk_trip.user_id=userid""" % (field, field))
                    ]),
                order_by=['-result']
                )
            print result.query.__str__()
            return result
        elif self.competitor_type == 'team':
            sum_select =   """SELECT sum(`dpnk_trip`.`%s_to`+`dpnk_trip`.`%s_from`) 
                            FROM dpnk_trip 
                            LEFT OUTER JOIN dpnk_userprofile ON (dpnk_trip.user_id = dpnk_userprofile.id) 
                            LEFT OUTER JOIN auth_user ON (dpnk_userprofile.user_id = auth_user.id) 
                            WHERE auth_user.is_active=True AND dpnk_userprofile.team_id=teamid""" % (field, field)
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
            print result.query.__str__()
            return result
        elif self.competitor_type == 'company':
            sum_select =   """SELECT sum(`dpnk_trip`.`%s_to`+`dpnk_trip`.`%s_from`) 
                            FROM dpnk_trip 
                            LEFT OUTER JOIN dpnk_userprofile ON (dpnk_trip.user_id = dpnk_userprofile.id) 
                            LEFT OUTER JOIN dpnk_team ON (dpnk_userprofile.team_id = dpnk_team.id) 
                            LEFT OUTER JOIN dpnk_subsidiary ON (dpnk_team.subsidiary_id = dpnk_subsidiary.id) 
                            LEFT OUTER JOIN auth_user ON (dpnk_userprofile.user_id = auth_user.id) 
                            WHERE auth_user.is_active=True and dpnk_subsidiary.company_id=companyid""" % (field, field)
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
            print result.query.__str__()
            return result
    elif self.type == 'questionnaire':
        select_dict = OrderedDict()

        if self.competitor_type == 'single_user':
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

        if self.competitor_type == 'single_user':
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
        print result.query.__str__()
        return result
