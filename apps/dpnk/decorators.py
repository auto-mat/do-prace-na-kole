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
from models import CompanyAdmin, UserProfile

def login_required_simple(fn):
    def wrapper(*args, **kwargs):
        request = args[0]
        if not request.user.is_authenticated():
            return HttpResponse(_(u"<div class='text-error'>Nejste přihlášen</div>"), status=401)
        else:
            return fn(*args, **kwargs)
    return wrapper

def must_be_coordinator(fn):
    @login_required
    def wrapper(*args, **kwargs):
        request = args[0]
        team = request.user.userprofile.team
        userprofile = request.user.userprofile
        if not userprofile.is_team_coordinator():
            return HttpResponse(_(u"<div class='text-error'>Nejste koordinátorem týmu %(team)s, nemáte tedy oprávnění editovat jeho údaje. Koordinátorem vašeho týmu je %(coordinator)s, vy jste: %(you)s </div>") % {'team': team.name, 'coordinator': team.coordinator, 'you': request.user.userprofile}, status=401)
        else:
            return fn(*args, **kwargs)
    return wrapper

def must_be_approved_for_team(fn):
    @login_required
    @must_be_competitor
    def wrapper(*args, **kwargs):
        request = args[0]
        userprofile = request.user.userprofile
        if userprofile.approved_for_team == 'approved' or userprofile.is_team_coordinator():
            return fn(*args, **kwargs)
        else:
            return HttpResponse(_(u"<div class='text-error'>Vaše členství v týmu %s nebylo odsouhlaseno. O ověření členství můžete požádat v <a href='/registrace/profil'>profilu</a>.</div>") % (userprofile.team.name,), status=401)
    return wrapper

def must_be_company_admin(fn):
    @login_required
    def wrapper(*args, **kwargs):
        request = args[0]
        try:
            company_admin = request.user.company_admin
            if company_admin.is_company_admin():
                return fn(*args, **kwargs)
        except CompanyAdmin.DoesNotExist:
            pass

        return HttpResponse(_(u"<div class='text-error'>Tato stránka je určená pouze ověřeným firemním koordinátorům, a tím vy nejste.</div>"), status=401)
    return wrapper

def must_be_competitor(fn):
    @login_required
    def wrapper(*args, **kwargs):
        request = args[0]
        try:
            userprofile = request.user.userprofile
            if userprofile:
                return fn(*args, **kwargs)
        except UserProfile.DoesNotExist:
            pass
        return HttpResponse(_(u"<div class='text-error'>V soutěži Do práce na kole nesoutěžíte. Pokud jste firemním správcem, použijte <a href='/fa'>správu firmy</a>.</div>"), status=401) 
    return wrapper
