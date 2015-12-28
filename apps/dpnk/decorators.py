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

import six
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from .models import UserAttendance, Campaign
from django.http import Http404
from django.contrib import messages
from django.core.urlresolvers import reverse
from . import models
from . import util
import functools


def must_be_owner(fn):
    @functools.wraps(fn)
    @must_be_competitor
    def wrapper(view, request, *args, **kwargs):
        user_attendance = kwargs['user_attendance']
        view_object = view.get_object()
        if view_object and not user_attendance == view_object.user_attendance:
            response = render_to_response(
                view.template_name,
                {
                    'fullpage_error_message': mark_safe(_(u"Nemůžete vidět cizí objekt")),
                },
                context_instance=RequestContext(request),
                status=403,
            )
            response.status_message = "not_owner"
            return response
        return fn(view, request, *args, **kwargs)
    return wrapper


def must_be_approved_for_team(fn):
    @functools.wraps(fn)
    @must_be_competitor
    def wrapper(view, request, *args, **kwargs):
        user_attendance = kwargs['user_attendance']
        if not user_attendance.team:
            response = render_to_response(
                view.template_name, {
                    'fullpage_error_message': mark_safe(_(u"Nemáte zvolený tým")),
                },
                context_instance=RequestContext(request),
                status=403,
            )
            response.status_message = "team_not_chosen"
            return response
        if user_attendance.approved_for_team == 'approved':
            return fn(view, request, *args, **kwargs)
        else:
            response = render_to_response(
                view.template_name,
                {
                    'fullpage_error_message':
                    mark_safe(
                        _(u"Vaše členství v týmu %(team)s nebylo odsouhlaseno. <a href='%(address)s'>Znovu požádat o ověření členství</a>.") %
                        {'team': user_attendance.team.name, 'address': reverse("zaslat_zadost_clenstvi")}),
                },
                context_instance=RequestContext(request),
                status=403,
            )
            response.status_message = "not_approved_for_team"
            return response
    return wrapper


def must_be_company_admin(fn):
    @functools.wraps(fn)
    def wrapper(view, request, *args, **kwargs):
        try:
            campaign = Campaign.objects.get(slug=request.subdomain)
        except Campaign.DoesNotExist:
            messages.error(request, _(u"Kampaň s identifikátorem %s neexistuje. Zadejte prosím správnou adresu.") % request.subdomain)
            raise Http404()

        company_admin = util.get_company_admin(request.user, campaign)
        if company_admin:
            kwargs['company_admin'] = company_admin
            return fn(view, request, *args, **kwargs)

        response = render_to_response(
            view.template_name,
            {
                'fullpage_error_message':
                mark_safe(_(
                    u"Tato stránka je určená pouze ověřeným Koordinátorům společností. K tuto funkci se musíte nejdříve <a href='%s'>přihlásit</a>" %
                    reverse("company_admin_application"))),
            },
            context_instance=RequestContext(request),
            status=403,
        )
        response.status_message = "not_company_admin"
        return response
    return wrapper


def must_have_team(fn):
    @functools.wraps(fn)
    @must_be_competitor
    def wrapped(view, request, user_attendance=None, *args, **kwargs):
        if not user_attendance.team:
            response = render_to_response(
                view.template_name,
                {
                    'fullpage_error_message': mark_safe(_(u"Napřed musíte mít <a href='%s'>vybraný tým</a>.") % reverse("zmenit_tym")),
                    'user_attendance': user_attendance,
                    'title': getattr(view, 'title', _(u"Musíte mít vybraný tým")),
                    'registration_phase': getattr(view, 'registration_phase', ''),
                    'form': None,
                },
                context_instance=RequestContext(request),
                status=403,
            )
            response.status_message = "have_no_team"
            return response
        return fn(view, request, user_attendance=user_attendance, *args, **kwargs)
    return wrapped


def must_be_in_phase(*phase_type):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapped(view, request, *args, **kwargs):
            try:
                campaign = Campaign.objects.get(slug=request.subdomain)
            except Campaign.DoesNotExist:
                messages.error(request, _(u"Kampaň s identifikátorem %s neexistuje. Zadejte prosím správnou adresu.") % request.subdomain)
                raise Http404()
            phases = campaign.phase_set.filter(type__in=phase_type)
            for phase in phases:
                if phase and phase.is_actual():
                    return fn(view, request, *args, **kwargs)
            phases_string = _(u" a ").join([six.text_type(models.Phase.TYPE_DICT[p]) for p in phase_type])
            response = render_to_response(
                view.template_name, {
                    'fullpage_error_message': mark_safe(_(u"Tento formulář se zobrazuje pouze ve fázích soutěže: %s") % phases_string),
                },
                context_instance=RequestContext(request),
                status=403,
            )
            response.status_message = "out_of_phase"
            return response
        return wrapped
    return decorator


def must_be_competitor(fn):
    @functools.wraps(fn)
    def wrapper(view, request, *args, **kwargs):
        if kwargs.get('user_attendance', None):
            return fn(view, request, *args, **kwargs)

        if util.is_competitor(request.user):
            userprofile = request.user.userprofile
            campaign_slug = request.subdomain
            try:
                campaign = Campaign.objects.get(slug=campaign_slug)
            except Campaign.DoesNotExist:
                messages.error(request, _(u"Kampaň s identifikátorem %s neexistuje. Zadejte prosím správnou adresu.") % campaign_slug)
                raise Http404()
            try:
                user_attendance = userprofile.userattendance_set.select_related('campaign', 'team', 't_shirt_size').get(campaign__slug=campaign_slug)
            except UserAttendance.DoesNotExist:
                user_attendance = UserAttendance(
                    userprofile=userprofile,
                    campaign=campaign,
                    approved_for_team='undecided',
                )
                user_attendance.save()

            kwargs['user_attendance'] = user_attendance
            return fn(view, request, *args, **kwargs)

        response = render_to_response(
            view.template_name,
            {
                'fullpage_error_message':
                mark_safe(_(
                    u"V soutěži Do práce na kole nesoutěžíte. Pokud jste firemním koordinátorem, použijte <a href='%s'>správu firmy</a>.") %
                    reverse("company_structure")),
            },
            context_instance=RequestContext(request),
            status=403,
        )
        response.status_message = "not_competitor"
        return response
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
                response = render_to_response(
                    view.template_name,
                    {
                        'fullpage_error_message': message,
                        'user_attendance': user_attendance,
                        'title': getattr(view, 'title', ''),
                        'registration_phase': getattr(view, 'registration_phase', ''),
                        'form': None,
                    },
                    context_instance=RequestContext(request),
                    status=403,
                )
                response.status_message = "condition_not_fulfilled"
                return response
            return fn(view, request, *args, **kwargs)
        return wrapped
    return decorator


def request_condition(condition, message):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapped(view, request, *args, **kwargs):
            if condition(request, args, kwargs):
                response = render_to_response(
                    view.template_name,
                    {
                        'fullpage_error_message': message,
                    },
                    context_instance=RequestContext(request),
                    status=403,
                )
                response.status_message = "request_condition"
                return response
            return fn(view, request, *args, **kwargs)
        return wrapped
    return decorator
