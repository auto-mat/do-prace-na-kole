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

def must_be_coordinator(fn):
    @login_required
    def wrapper(*args, **kwargs):
        request = args[0]
        team = request.user.userprofile.team
        if team.is_team_coordinator():
            return HttpResponse(_(u"<div class='text-error'>Nejste koordinátorem týmu %(team)s, nemáte tedy oprávnění editovat jeho údaje. Koordinátorem vašeho týmu je %(coordinator)s, vy jste: %(you)s </div>") % {'team': team.name, 'coordinator': team.coordinator, 'you': request.user.userprofile}, status=401)
        else:
            return fn(*args, **kwargs)
    return wrapper

def must_be_approved_for_team(fn):
    @login_required
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
        userprofile = request.user.userprofile
        if userprofile.is_company_admin():
            return fn(*args, **kwargs)
        else:
            return HttpResponse(_(u"<div class='text-error'>Tato stránka je určená pouze firemním koordinátorům, a tím vy nejste.</div>"), status=401)
    return wrapper

def must_have_team(fn):
    @login_required
    def wrapper(*args, **kwargs):
        request = args[0]
        userprofile = request.user.userprofile
        if userprofile.team:
            return fn(*args, **kwargs)
        else:
            return HttpResponse(_(u"<div class='text-error'>Nemáte zvolený žádný tým (pravděpodobně protože jste firemním administrátorem). Tento obsah tedy nemůžete vidět.</div>"), status=401)
    return wrapper
