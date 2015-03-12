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
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from models import UserAttendance, Campaign
from wp_urls import wp_reverse
from django.core.urlresolvers import reverse
import models
import functools


def must_be_approved_for_team(fn):
    @functools.wraps(fn)
    @must_be_competitor
    def wrapper(*args, **kwargs):
        user_attendance = kwargs['user_attendance']
        if not user_attendance.team:
            return HttpResponse(_(u"<div class='text-warning'>Nemáte zvolený tým</div>"))
        if user_attendance.approved_for_team == 'approved':
            return fn(*args, **kwargs)
        else:
            return HttpResponse(_(u"<div class='text-warning'>Vaše členství v týmu %(team)s nebylo odsouhlaseno. <a href='%(address)s'>Znovu požádat o ověření členství</a>.</div>") % {'team': user_attendance.team.name, 'address': reverse("zaslat_zadost_clenstvi")})
    return wrapper


def must_be_company_admin(fn):
    @functools.wraps(fn)
    def wrapper(view, request, *args, **kwargs):
        campaign = Campaign.objects.get(slug=request.subdomain)

        company_admin = models.get_company_admin(request.user, campaign)
        if company_admin:
            kwargs['company_admin'] = company_admin
            return fn(view, request, *args, **kwargs)

        return render_to_response(view.template_name, {
            'fullpage_error_message': mark_safe(_(u"Tato stránka je určená pouze ověřeným Koordinátorům společností. K tuto funkci se musíte nejdříve <a href='%s'>přihlásit</a>" % reverse("company_admin_application"))),
        }, context_instance=RequestContext(request))
    return wrapper


def must_have_team(fn):
    @functools.wraps(fn)
    @must_be_competitor
    def wrapped(view, request, user_attendance=None, *args, **kwargs):
        if not user_attendance.team:
            return render_to_response(view.template_name, {
                'fullpage_error_message': mark_safe(_(u"Napřed musíte mít <a href='%s'>vybraný tým</a>.") % reverse("zmenit_tym")),
                'user_attendance': user_attendance,
                'title': _(u"Musíte mít vybraný tým"),
                'current_view': getattr(view, 'current_view', ''),
                'form': None,
                }, context_instance=RequestContext(request))
        return fn(view,request, user_attendance=user_attendance, *args, **kwargs)
    return wrapped


def must_be_in_phase(*phase_type):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapped(view, request, *args, **kwargs):
            campaign = Campaign.objects.get(slug=request.subdomain)
            phases = campaign.phase_set.filter(type__in=phase_type)
            for phase in phases:
                if phase and phase.is_actual():
                    return fn(view, request, *args, **kwargs)
            phases_string = _(u" a ").join([unicode(models.Phase.TYPE_DICT[p]) for p in phase_type])
            return render_to_response(view.template_name, {
                'fullpage_error_message': mark_safe(_(u"Tento formulář se zobrazuje pouze ve fázích soutěže: %s") % phases_string),
            }, context_instance=RequestContext(request))
        return wrapped
    return decorator


def must_be_competitor(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if kwargs.get('user_attendance', None):
            return fn(*args, **kwargs)

        request = args[1]
        if models.is_competitor(request.user):
            userprofile = request.user.userprofile
            campaign_slug = request.subdomain
            try:
                user_attendance = userprofile.userattendance_set.select_related('team__subsidiary__city', 'campaign', 'team__subsidiary__company', 't_shirt_size').get(campaign__slug=campaign_slug)
            except UserAttendance.DoesNotExist:
                user_attendance = UserAttendance(
                    userprofile=userprofile,
                    campaign=Campaign.objects.get(slug=campaign_slug),
                    approved_for_team='undecided',
                    )
                user_attendance.save()

            kwargs['user_attendance'] = user_attendance
            return fn(*args, **kwargs)

        return HttpResponse(_(u"<div class='text-warning'>V soutěži Do práce na kole nesoutěžíte. Pokud jste firemním koordinátorem, použijte <a href='%s'>správu firmy</a>.</div>") % wp_reverse("company_admin"))
    return wrapper


def must_be_in_group(group):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapped(request, *args, **kwargs):
            if request.user.groups.filter(name=group).count() == 0:
                return HttpResponse(_(u"<div class='text-warning'>Pro přístup k této stránce musíte být ve skupině %s</div>") % group)
            return fn(request, *args, **kwargs)
        return wrapped
    return decorator


def user_attendance_has(condition, message):
    def decorator(fn):
        @functools.wraps(fn)
        @must_be_competitor
        def wrapped(view, request, *args, **kwargs):
            user_attendance = kwargs['user_attendance']
            if condition(user_attendance):
                return render_to_response(view.template_name, {
                    'fullpage_error_message': message,
                    'user_attendance': user_attendance,
                    'title': _(u"Musíte mít vybraný tým"),
                    'current_view': getattr(view, 'current_view', ''),
                    'form': None,
                    }, context_instance=RequestContext(request))
            return fn(view, request, *args, **kwargs)
        return wrapped
    return decorator


def request_condition(condition, message):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapped(view, request, *args, **kwargs):
            if condition(request, args, kwargs):
                return render_to_response(view.template_name, {
                    'fullpage_error_message': message,
                }, context_instance=RequestContext(request))
            return fn(view, request, *args, **kwargs)
        return wrapped
    return decorator
