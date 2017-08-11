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
import functools

from braces.views import GroupRequiredMixin, UserPassesTestMixin

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.utils import formats
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


def must_be_owner(fn):
    @functools.wraps(fn)
    def wrapper(view, request, *args, **kwargs):
        user_attendance = request.user_attendance
        view_object = view.get_object()
        if view_object and not user_attendance == view_object.user_attendance:
            response = render(
                request,
                view.template_name,
                {
                    'fullpage_error_message': _(u"Nemůžete vidět cizí objekt"),
                    'title': _("Chybí oprávnění"),
                },
                status=403,
            )
            response.status_message = "not_owner"
            return response
        return fn(view, request, *args, **kwargs)
    return wrapper


def must_be_company_admin(fn):
    @functools.wraps(fn)
    def wrapper(view, request, *args, **kwargs):
        campaign = request.campaign
        company_admin = request.user.userprofile.get_company_admin_for_campaign(campaign=campaign)
        if company_admin and company_admin.is_approved():
            kwargs['company_admin'] = company_admin
            return fn(view, request, *args, **kwargs)

        response = render(
            request,
            view.template_name,
            {
                'fullpage_error_message':
                mark_safe(
                    _(
                        "Tato stránka je určená pouze ověřeným firemním koordinátorům. "
                        "K této funkci se musíte nejdříve <a href='%s'>přihlásit</a>, a vyčkat na naše ověření. "
                        "Pokud na ověření čekáte příliš dlouho, kontaktujte naši podporu na "
                        "<a href='mailto:kontakt@dopracenakole.cz?subject=Neexistující soutěž'>kontakt@dopracenakole.cz</a>." %
                        reverse("company_admin_application"),
                    ),
                ),
                'title': _("Nedostatečné oprávnění"),
            },
            status=403,
        )
        response.status_message = "not_company_admin"
        return response
    return wrapper


def must_be_in_phase(phase_type):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapped(view, request, *args, **kwargs):
            campaign = request.campaign
            try:
                phase = campaign.phase_set.get(phase_type=phase_type)
            except ObjectDoesNotExist:
                phase = None
            if phase and phase.is_actual():
                return fn(view, request, *args, **kwargs)
            if not phase or phase.has_started():
                message = mark_safe(_(u"Již skončil čas, kdy se tato stránka zobrazuje."))
            else:
                message = mark_safe(
                    _(u"Ještě nenastal čas, kdy by se měla tato stránka zobrazit.<br/>Stránka se zobrazí až %s")
                    % formats.date_format(phase.date_from, "SHORT_DATE_FORMAT"),
                )
            response = render(
                request,
                view.template_name, {
                    'fullpage_error_message': message,
                    'title': _("Nedostupná stránka"),
                },
                status=403,
            )
            response.status_message = "out_of_phase"
            return response
        return wrapped
    return decorator


class FullPageMessageMixin(object):
    def get_error_message(self, request):
        return self.error_message

    def get_error_title(self, request):
        return self.error_title

    def get_template_name(self):
        return self.template_name

    def handle_no_permission(self, request):
        if request.user.is_authenticated():
            return render(
                request,
                self.get_template_name(),
                {
                    'fullpage_error_message': self.get_error_message(request),
                    'title': self.get_error_title(request),
                },
                status=403,
            )
        return super().handle_no_permission(request)


class GroupRequiredResponseMixin(FullPageMessageMixin, GroupRequiredMixin):
    def get_error_message(self, request):
        return _("Pro přístup k této stránce musíte být ve skupině %s") % self.group_required
    error_title = _("Nedostatečné oprávnění")


class UserAttendancePassesTestMixin(UserPassesTestMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user_attendance:
            user_test_result = self.get_test_func()(request.user_attendance)
        else:
            user_test_result = False

        if not user_test_result:
            return self.handle_no_permission(request)

        return super(UserPassesTestMixin, self).dispatch(
            request, *args, **kwargs,
        )


class MustHaveTeamMixin(FullPageMessageMixin, UserAttendancePassesTestMixin):
    error_title = _("Musíte mít vybraný tým")

    def get_error_message(self, request):
        return mark_safe(_("Napřed musíte mít <a href='%s'>vybraný tým</a>.") % reverse("zmenit_tym"))

    def test_func(self, user_attendance):
        return user_attendance.team


class MustBeApprovedForTeamMixin(MustHaveTeamMixin, FullPageMessageMixin, UserAttendancePassesTestMixin):
    error_title = _("Členství v týmu neověřeno")

    def test_func(self, user_attendance):
        return user_attendance.is_team_approved()

    def get_error_message(self, request):
        if request.user_attendance.team:
            return format_html(
                _(u"Vaše členství v týmu {team} nebylo odsouhlaseno. <a href='{address}'>Znovu požádat o ověření členství</a>."),
                team=request.user_attendance.team.name, address=reverse("zaslat_zadost_clenstvi"),
            )
        else:
            return super().get_error_message(request)


def user_attendance_has(condition, message):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapped(view, request, *args, **kwargs):
            user_attendance = request.user_attendance
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


def request_condition(condition, message, title=_("Nedostatečné oprávnění")):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapped(view, request, *args, **kwargs):
            if condition(request, args, kwargs):
                response = render(
                    request,
                    view.template_name,
                    {
                        'fullpage_error_message': message,
                        'title': title,
                    },
                    status=403,
                )
                response.status_message = "request_condition"
                return response
            return fn(view, request, *args, **kwargs)
        return wrapped
    return decorator
