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

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from .models import UserAttendance, Campaign
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.contrib import messages
from django.core.urlresolvers import reverse
from . import util
import functools
from django.utils import formats


def must_be_owner(fn):
    @functools.wraps(fn)
    @must_be_competitor
    def wrapper(view, request, *args, **kwargs):
        user_attendance = kwargs['user_attendance']
        view_object = view.get_object()
        if view_object and not user_attendance == view_object.user_attendance:
            response = render(
                request,
                view.template_name,
                {
                    'fullpage_error_message': mark_safe(_(u"Nemůžete vidět cizí objekt")),
                },
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
            response = render(
                request,
                view.template_name, {
                    'fullpage_error_message': mark_safe(_(u"Nemáte zvolený tým")),
                },
                status=403,
            )
            response.status_message = "team_not_chosen"
            return response
        if user_attendance.approved_for_team == 'approved':
            return fn(view, request, *args, **kwargs)
        else:
            response = render(
                request,
                view.template_name,
                {
                    'fullpage_error_message':
                    mark_safe(
                        _(u"Vaše členství v týmu %(team)s nebylo odsouhlaseno. <a href='%(address)s'>Znovu požádat o ověření členství</a>.") %
                        {'team': user_attendance.team.name, 'address': reverse("zaslat_zadost_clenstvi")}),
                },
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

        response = render(
            request,
            view.template_name,
            {
                'fullpage_error_message':
                mark_safe(_(
                    "Tato stránka je určená pouze ověřeným Koordinátorům společností. "
                    "K tuto funkci se musíte nejdříve <a href='%s'>přihlásit</a>, a vyčkat na naše ověření. "
                    "Pokud na ověření čekáte příliš dlouho, kontaktujte naši podporu na "
                    "<a href='mailto:kontakt@dopracenakole.cz?subject=Neexistující soutěž'>kontakt@dopracenakole.cz</a>." %
                    reverse("company_admin_application"))),
            },
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
            response = render(
                request,
                view.template_name,
                {
                    'fullpage_error_message': mark_safe(_(u"Napřed musíte mít <a href='%s'>vybraný tým</a>.") % reverse("zmenit_tym")),
                    'user_attendance': user_attendance,
                    'title': getattr(view, 'title', _(u"Musíte mít vybraný tým")),
                    'registration_phase': getattr(view, 'registration_phase', ''),
                    'form': None,
                },
                status=403,
            )
            response.status_message = "have_no_team"
            return response
        return fn(view, request, user_attendance=user_attendance, *args, **kwargs)
    return wrapped


def must_be_in_phase(phase_type):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapped(view, request, *args, **kwargs):
            try:
                campaign = Campaign.objects.get(slug=request.subdomain)
            except Campaign.DoesNotExist:
                messages.error(request, _(u"Kampaň s identifikátorem %s neexistuje. Zadejte prosím správnou adresu.") % request.subdomain)
                raise Http404()
            try:
                phase = campaign.phase_set.get(type=phase_type)
            except ObjectDoesNotExist:
                phase = None
            if phase and phase.is_actual():
                return fn(view, request, *args, **kwargs)
            if not phase or phase.has_started():
                message = mark_safe(_(u"Již skončil čas, kdy se tato stránka zobrazuje."))
            else:
                message = mark_safe(
                    _(u"Ještě nenastal čas, kdy by se měla tato stránka zobrazit.<br/>Stránka se zobrazí až %s")
                    % formats.date_format(phase.date_from, "SHORT_DATE_FORMAT")
                )
            response = render(
                request,
                view.template_name, {
                    'fullpage_error_message': message,
                },
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
            campaign_slug = request.subdomain
            user_attendance = request.user_attendance
            if user_attendance is None:
                try:
                    campaign = Campaign.objects.get(slug=campaign_slug)
                except Campaign.DoesNotExist:
                    messages.error(request, _(u"Kampaň s identifikátorem %s neexistuje. Zadejte prosím správnou adresu.") % campaign_slug)
                    raise Http404()
                user_attendance = UserAttendance(
                    userprofile=request.user.userprofile,
                    campaign=campaign,
                    approved_for_team='undecided',
                )
                user_attendance.save()

            kwargs['user_attendance'] = user_attendance
            return fn(view, request, *args, **kwargs)

        response = render(
            request,
            view.template_name,
            {
                'fullpage_error_message':
                mark_safe(_(
                    u"V soutěži Do práce na kole nesoutěžíte. Pokud jste firemním koordinátorem, použijte <a href='%s'>správu firmy</a>.") %
                    reverse("company_structure")),
            },
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
                response = render(
                    request,
                    view.template_name,
                    {
                        'fullpage_error_message': message,
                        'user_attendance': user_attendance,
                        'title': getattr(view, 'title', ''),
                        'registration_phase': getattr(view, 'registration_phase', ''),
                        'form': None,
                    },
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
                response = render(
                    request,
                    view.template_name,
                    {
                        'fullpage_error_message': message,
                    },
                    status=403,
                )
                response.status_message = "request_condition"
                return response
            return fn(view, request, *args, **kwargs)
        return wrapped
    return decorator
