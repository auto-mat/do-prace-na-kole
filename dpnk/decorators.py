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

from braces.views import GroupRequiredMixin

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import render
from django.utils import formats
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from .string_lazy import mark_safe_lazy


class MustBeInPhaseMixin(object):
    def dispatch(self, request, *args, **kwargs):
        try:
            phase = request.campaign.phase_set.get(phase_type=self.must_be_in_phase_type)
        except ObjectDoesNotExist:
            raise PermissionDenied(_("Tato stránka nemůže být v této kampani zobrazena."))

        if phase.is_actual():
            return super().dispatch(request, *args, **kwargs)

        if phase.has_started():
            raise PermissionDenied(_("Již skončil čas, kdy se tato stránka zobrazuje."))
        raise PermissionDenied(
            mark_safe_lazy(
                _("Ještě nenastal čas, kdy by se měla tato stránka zobrazit.<br/>Stránka se zobrazí až %s")
                % formats.date_format(phase.date_from, "SHORT_DATE_FORMAT"),
            ),
        )


class MustBeInRegistrationPhaseMixin(object):
    must_be_in_phase = "registration"


class MustBeInPaymentPhaseMixin(object):
    must_be_in_phase = "payment"


class MustBeInInvoicesPhaseMixin(object):
    must_be_in_phase = "invoices"


class GroupRequiredResponseMixin(GroupRequiredMixin):
    def get_error_message(self, request):
        raise PermissionDenied(_("Pro přístup k této stránce musíte být ve skupině %s") % self.group_required)


class MustHaveTeamMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user_attendance.team:
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied(mark_safe_lazy(_("Napřed musíte mít <a href='%s'>vybraný tým</a>.") % reverse_lazy("zmenit_tym")))


class MustBeApprovedForTeamMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user_attendance.team and request.user_attendance.is_team_approved():
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied(
            format_html(
                _("Vaše členství v týmu {team} nebylo odsouhlaseno. <a href='{address}'>Znovu požádat o ověření členství</a>."),
                team=request.user_attendance.team.name, address=reverse("zaslat_zadost_clenstvi"),
            ),
        )


class MustBeOwner(object):
    def dispatch(self, request, *args, **kwargs):
        view_object = self.get_object()
        if view_object and request.user_attendance == view_object.user_attendance:
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied(_("Nemůžete vidět cizí objekt"))


class MustBeCompanyAdmin(object):
    """
    Tests if user is company admin.
    Also sets CompanyAdmin object to self.company_admin
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user_attendance:
            return super().dispatch(request, *args, **kwargs)

        self.company_admin = request.user_attendance.related_company_admin
        if self.company_admin and self.company_admin.is_approved():
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied(
            mark_safe_lazy(
                "Tato stránka je určená pouze ověřeným firemním koordinátorům. "
                "K této funkci se musíte nejdříve <a href='%s'>přihlásit</a>, a vyčkat na naše ověření. "
                "Pokud na ověření čekáte příliš dlouho, kontaktujte naši podporu na "
                "<a href='mailto:kontakt@dopracenakole.cz?subject=Neexistující soutěž'>kontakt@dopracenakole.cz</a>." %
                reverse("company_admin_application"),
            ),
        )


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
