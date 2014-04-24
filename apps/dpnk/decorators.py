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

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from models import UserAttendance, Campaign
from wp_urls import wp_reverse
from util import redirect
import models


def login_required_simple(fn):
    def wrapper(*args, **kwargs):
        request = args[0]
        if not request.user.is_authenticated():
            return redirect(wp_reverse("login"))
        else:
            return fn(*args, **kwargs)
    return wrapper


def must_be_coordinator(fn):
    @must_be_competitor
    @login_required
    def wrapper(*args, **kwargs):
        user_attendance = kwargs['user_attendance']
        team = user_attendance.team
        if not user_attendance.is_team_coordinator():
            return HttpResponse(_(u"<div class='text-warning'>Nejste koordinátorem týmu %(team)s, nemáte tedy oprávnění editovat jeho údaje. Koordinátorem vašeho týmu je %(coordinator)s, vy jste: %(you)s </div>") % {'team': team.name if team else u"neznámý", 'coordinator': team.coordinator_campaign if team else u"nikdo", 'you': user_attendance}, status=401)
        else:
            return fn(*args, **kwargs)
    return wrapper


def must_be_approved_for_team(fn):
    @login_required
    @must_be_competitor
    def wrapper(*args, **kwargs):
        user_attendance = kwargs['user_attendance']
        if not user_attendance.team:
            return HttpResponse(_(u"<div class='text-warning'>Nemáte zvolený tým</div>"), status=401)
        if user_attendance.approved_for_team == 'approved' or user_attendance.is_team_coordinator():
            return fn(*args, **kwargs)
        else:
            return HttpResponse(_(u"<div class='text-warning'>Vaše členství v týmu %(team)s nebylo odsouhlaseno týmovým koordinátorem. <a href='%(address)s'>Znovu požádat o ověření členství</a>.</div>") % {'team': user_attendance.team.name, 'address': wp_reverse("zaslat_zadost_clenstvi")}, status=401)
    return wrapper


def must_be_company_admin(fn):
    @login_required
    def wrapper(request, campaign_slug="", *args, **kwargs):
        campaign = Campaign.objects.get(slug=campaign_slug)

        company_admin = models.get_company_admin(request.user, campaign)
        if company_admin:
            kwargs['company_admin'] = company_admin
            return fn(request, *args, **kwargs)

        return HttpResponse(_(u"<div class='text-warning'>Tato stránka je určená pouze ověřeným firemním koordinátorům, a tím vy nejste.</div>"), status=401)
    return wrapper


def must_have_team(fn):
    @must_be_competitor
    def wrapper(request, user_attendance=None, *args, **kwargs):
        if not user_attendance.team:
            return HttpResponse(_(u"<div class='text-warning'>Napřed musíte mít vybraný tým.</div>"), status=401)
        return fn(request, user_attendance=user_attendance, *args, **kwargs)
    return wrapper


def must_be_in_phase(phase_type):
    def decorator(fn):
        def wrapped(request, *args, **kwargs):
            campaign = Campaign.objects.get(slug=kwargs.get('campaign_slug'))
            try:
                phase = campaign.phase_set.get(type=phase_type)
            except models.Phase.DoesNotExist:
                phase = None
            if not phase or not phase.is_actual():
                return HttpResponse(_(u"<div class='text-warning'>Tento formulář se zobrazuje pouze v %s fázi soutěže.</div>") % models.Phase.TYPE_DICT[phase_type], status=401)
            return fn(request, *args, **kwargs)
        return wrapped
    return decorator


def must_be_competitor(fn):
    @login_required
    def wrapper(*args, **kwargs):
        if kwargs.get('user_attendance', None):
            return fn(*args, **kwargs)

        request = args[0]
        if models.is_competitor(request.user):
            userprofile = request.user.userprofile
            campaign = Campaign.objects.get(slug=kwargs.pop('campaign_slug'))
            try:
                user_attendance = userprofile.userattendance_set.get(campaign=campaign)
            except UserAttendance.DoesNotExist:
                user_attendance = UserAttendance(
                    userprofile=userprofile,
                    campaign=campaign,
                    approved_for_team='undecided',
                    )
                user_attendance.save()

            kwargs['user_attendance'] = user_attendance
            return fn(*args, **kwargs)

        return HttpResponse(_(u"<div class='text-warning'>V soutěži Do práce na kole nesoutěžíte. Pokud jste firemním koordinátorem, použijte <a href='%s'>správu firmy</a>.</div>") % wp_reverse("company_admin"), status=401)
    return wrapper


def must_be_in_group(group):
    def decorator(fn):
        def wrapped(request, *args, **kwargs):
            if request.user.groups.filter(name=group).count() == 0:
                return HttpResponse(_(u"<div class='text-warning'>Pro přístup k této stránce musíte být ve skupině %s</div>") % group, status=401)
            return fn(request, *args, **kwargs)
        return wrapped
    return decorator


def user_attendance_has(condition, message):
    def decorator(fn):
        @must_be_competitor
        def wrapped(request, *args, **kwargs):
            user_attendance = kwargs['user_attendance']
            if condition(user_attendance):
                return HttpResponse(message.encode('utf8'), status=401)
            return fn(request, *args, **kwargs)
        return wrapped
    return decorator


def request_condition(condition, message):
    def decorator(fn):
        def wrapped(request, *args, **kwargs):
            if condition(request, args, kwargs):
                return HttpResponse(message.encode('utf8'), status=401)
            return fn(request, *args, **kwargs)
        return wrapped
    return decorator
