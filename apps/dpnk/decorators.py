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
from  django.http import HttpResponse
from django.utils.translation import gettext as _
from models import UserProfile, UserAttendance, Campaign
import models

def login_required_simple(fn):
    def wrapper(*args, **kwargs):
        request = args[0]
        if not request.user.is_authenticated():
            return HttpResponse(_(u"<div class='text-error'>Nejste přihlášen</div>"), status=401)
        else:
            return fn(*args, **kwargs)
    return wrapper

def must_be_coordinator(fn):
    @must_be_competitor
    @login_required
    def wrapper(*args, **kwargs):
        request = args[0]
        userprofile = request.user.userprofile
        user_attendance = userprofile.userattendance_set.get(campaign__slug=kwargs.pop('campaign_slug'))
        team = user_attendance.team
        if not models.is_team_coordinator(user_attendance):
            return HttpResponse(_(u"<div class='text-error'>Nejste koordinátorem týmu %(team)s, nemáte tedy oprávnění editovat jeho údaje. Koordinátorem vašeho týmu je %(coordinator)s, vy jste: %(you)s </div>") % {'team': team.name, 'coordinator': team.coordinator_campaign, 'you': user_attendance}, status=401)
        else:
            return fn(*args, **kwargs)
    return wrapper

def must_be_approved_for_team(fn):
    @login_required
    @must_be_competitor
    def wrapper(*args, **kwargs):
        request = args[0]
        user_attendance = kwargs['user_attendance']
        if user_attendance.approved_for_team == 'approved' or models.is_team_coordinator(user_attendance):
            return fn(*args, **kwargs)
        else:
            return HttpResponse(_(u"<div class='text-error'>Vaše členství v týmu %s nebylo odsouhlaseno. O ověření členství můžete požádat v <a href='/registrace/profil'>profilu</a>.</div>") % (user_attendance.team.name,), status=401)
    return wrapper

def must_be_company_admin(fn):
    @login_required
    def wrapper(*args, **kwargs):
        request = args[0]
        try:
            administrated_company = request.user.company_admin.get_administrated_company()
        except CompanyAdmin.DoesNotExist:
            administrated_company = None
        if administrated_company:
            kwargs['administrated_company'] = administrated_company
            return fn(*args, **kwargs)

        return HttpResponse(_(u"<div class='text-error'>Tato stránka je určená pouze ověřeným firemním koordinátorům, a tím vy nejste.</div>"), status=401)
    return wrapper

def must_be_competitor(fn):
    @login_required
    def wrapper(*args, **kwargs):
        request = args[0]
        if models.is_competitor(request.user):
            userprofile = request.user.userprofile
            campaign = Campaign.objects.get(slug=kwargs['campaign_slug'])
            try:
                user_attendance = userprofile.userattendance_set.get(campaign=campaign)
            except UserAttendance.DoesNotExist:
                user_attendance = UserAttendance(userprofile = userprofile,
                            campaign = campaign,
                            approved_for_team = 'undecided',
                            )
                user_attendance.save()
            
            kwargs['user_attendance'] = user_attendance
            return fn(*args, **kwargs)

        return HttpResponse(_(u"<div class='text-error'>V soutěži Do práce na kole nesoutěžíte. Pokud jste firemním správcem, použijte <a href='/fa'>správu firmy</a>.</div>"), status=401) 
    return wrapper
