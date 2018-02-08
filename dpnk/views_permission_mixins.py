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
from braces.views import GroupRequiredMixin

from django.core.exceptions import ObjectDoesNotExist
try:
    from django.urls import reverse, reverse_lazy
except ImportError:  # Django<2.0
    from django.core.urlresolvers import reverse, reverse_lazy
from django.utils import formats
from django.utils.translation import ugettext_lazy as _

from dpnk import exceptions
from dpnk.models import PHASE_TYPE_DICT

from .string_lazy import format_html_lazy, mark_safe_lazy


class PhaseMixin(object):
    def get_phase(self, request):
        try:
            return request.campaign.phase_set.get(phase_type=self.must_be_in_phase)
        except ObjectDoesNotExist:
            raise exceptions.TemplatePermissionDenied(
                _("Tato stránka nemůže být v této kampani zobrazena. Neexistuje v ní fáze %s." % PHASE_TYPE_DICT[self.must_be_in_phase]),
                template_name=getattr(self, 'template_name', None),
            )


class MustBeInPhaseMixin(PhaseMixin):
    def dispatch(self, request, *args, **kwargs):
        phase = self.get_phase(request)

        if phase.is_actual():
            return super().dispatch(request, *args, **kwargs)

        if phase.has_started():
            raise exceptions.TemplatePermissionDenied(
                _("Již skončil čas, kdy se tato stránka zobrazuje."),
                template_name=getattr(self, 'template_name', None),
            )
        raise exceptions.TemplatePermissionDenied(
            mark_safe_lazy(
                _("Ještě nenastal čas, kdy by se měla tato stránka zobrazit.<br/>Stránka se zobrazí až %s")
                % formats.date_format(phase.date_from, "SHORT_DATE_FORMAT"),
            ),
            template_name=getattr(self, 'template_name', None),
        )


class MustBeInRegistrationPhaseMixin(PhaseMixin):
    must_be_in_phase = "registration"

    def dispatch(self, request, *args, **kwargs):
        phase = self.get_phase(request)

        if phase.is_actual() or (self.user_attendance and self.user_attendance.entered_competition()):
            return super().dispatch(request, *args, **kwargs)

        if phase.has_started():
            raise exceptions.TemplatePermissionDenied(
                _("Registrace již byla ukončena."),
                template_name=getattr(self, 'template_name', None),
            )
        raise exceptions.TemplatePermissionDenied(
            mark_safe_lazy(
                _("Registrace ještě nezačala.<br/>Registrovat se budete moct od %s")
                % formats.date_format(phase.date_from, "SHORT_DATE_FORMAT"),
            ),
            template_name=getattr(self, 'template_name', None),
        )


class MustBeInPaymentPhaseMixin(MustBeInPhaseMixin):
    must_be_in_phase = "payment"


class MustBeInInvoicesPhaseMixin(MustBeInPhaseMixin):
    must_be_in_phase = "invoices"


class GroupRequiredResponseMixin(GroupRequiredMixin):
    def no_permissions_fail(self, request):
        if request.user.is_authenticated:
            raise exceptions.TemplatePermissionDenied(
                _("Pro přístup k této stránce musíte být ve skupině %s") % self.group_required,
                template_name=getattr(self, 'template_name', None),
            )
        return super().no_permissions_fail(request)


class MustHaveTeamMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user_attendance and not request.user_attendance.team:
            raise exceptions.TemplatePermissionDenied(
                mark_safe_lazy(_("Napřed musíte mít <a href='%s'>vybraný tým</a>.") % reverse_lazy("zmenit_tym")),
                template_name=getattr(self, 'template_name', None),
            )

        return super().dispatch(request, *args, **kwargs)


class MustBeApprovedForTeamMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if (
                request.user_attendance and
                request.user_attendance.team and
                not (request.user_attendance.team and request.user_attendance.is_team_approved())
        ):
            raise exceptions.TemplatePermissionDenied(
                format_html_lazy(
                    _("Vaše členství v týmu {team} nebylo odsouhlaseno. <a href='{address}'>Znovu požádat o ověření členství</a>."),
                    team=request.user_attendance.team.name, address=reverse("zaslat_zadost_clenstvi"),
                ),
                template_name=getattr(self, 'template_name', None),
            )
        return super().dispatch(request, *args, **kwargs)


class MustBeOwnerMixin(object):
    def dispatch(self, request, *args, **kwargs):
        view_object = self.get_object()
        if request.user_attendance and view_object and request.user_attendance == view_object.user_attendance:
            return super().dispatch(request, *args, **kwargs)

        raise exceptions.TemplatePermissionDenied(
            _("Nemůžete vidět cizí objekt"),
            template_name=getattr(self, 'template_name', None),
        )


class MustBeCompanyAdminMixin(object):
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

        raise exceptions.TemplatePermissionDenied(
            mark_safe_lazy(
                "Tato stránka je určená pouze ověřeným firemním koordinátorům. "
                "K této funkci se musíte nejdříve <a href='%s'>přihlásit</a>, a vyčkat na naše ověření. "
                "Pokud na ověření čekáte příliš dlouho, kontaktujte naši podporu na "
                "<a href='mailto:kontakt@dopracenakole.cz?subject=Neexistující soutěž'>kontakt@dopracenakole.cz</a>." %
                reverse("company_admin_application"),
            ),
            template_name=getattr(self, 'template_name', None),
        )
