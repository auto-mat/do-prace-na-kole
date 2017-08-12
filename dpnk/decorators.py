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
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import render
from django.utils import formats
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .string_lazy import format_lazy, mark_safe_lazy


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

    def fullpage_error_response(self, request, message, title=_("Nedostatečné oprávnění")):
        return render(
            request,
            self.get_template_name(),
            {
                'fullpage_error_message': message,
                'title': title,
            },
            status=403,
        )
        return

    def handle_no_permission(self, request):
        if request.user.is_authenticated():
            return self.fullpage_error_response(
                request,
                self.get_error_message(request),
                self.get_error_title(request),
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
    error_message = mark_safe_lazy(
        format_lazy(
            _("Napřed musíte mít <a href='{addr}'>vybraný tým</a>."),
            addr=reverse_lazy("zmenit_tym"),
        ),
    )

    def test_func(self, user_attendance):
        return user_attendance.team is not None


class MustBeApprovedForTeamMixin(MustHaveTeamMixin, FullPageMessageMixin, UserAttendancePassesTestMixin):
    error_title = _("Členství v týmu neověřeno")

    def test_func(self, user_attendance):
        return user_attendance.is_team_approved()

    def get_error_message(self, request):
        if request.user_attendance.team:
            return format_html(
                _("Vaše členství v týmu {team} nebylo odsouhlaseno. <a href='{address}'>Znovu požádat o ověření členství</a>."),
                team=request.user_attendance.team.name, address=reverse("zaslat_zadost_clenstvi"),
            )
        else:
            return super().get_error_message(request)


class MustBeOwner(FullPageMessageMixin, UserAttendancePassesTestMixin):
    error_message = _("Nemůžete vidět cizí objekt")
    error_title = _("Chybí oprávnění")

    def test_func(self, user_attendance):
        view_object = self.get_object()
        return view_object and user_attendance == view_object.user_attendance


class MustBeCompanyAdmin(FullPageMessageMixin, UserAttendancePassesTestMixin):
    """
    Tests if user is company admin.
    Also sets CompanyAdmin object to self.company_admin
    """
    error_message = mark_safe_lazy(
        format_lazy(
            "Tato stránka je určená pouze ověřeným firemním koordinátorům. "
            "K této funkci se musíte nejdříve <a href='{addr}'>přihlásit</a>, a vyčkat na naše ověření. "
            "Pokud na ověření čekáte příliš dlouho, kontaktujte naši podporu na "
            "<a href='mailto:kontakt@dopracenakole.cz?subject=Neexistující soutěž'>kontakt@dopracenakole.cz</a>.",
            addr=reverse_lazy("company_admin_application"),
        ),
    )
    error_title = _("Nedostatečné oprávnění")

    def test_func(self, user_attendance):
        self.company_admin = user_attendance.related_company_admin
        return self.company_admin is not None and self.company_admin.is_approved()


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
