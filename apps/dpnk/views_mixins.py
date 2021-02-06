# -*- coding: utf-8 -*-
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2017 o.s. Auto*Mat
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

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import classonlymethod
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from dpnk import models
from dpnk import notification_types

from .util import mark_safe_lazy
from .views_permission_mixins import MustBeInRegistrationPhaseMixin


class CompanyAdminMixin(SuccessMessageMixin):
    success_message = _(
        "Byli jste úspěšně zaregistrování jako firemní koordinátor. "
        'Vaší organizaci můžete spravovat v menu "Firemní koordinátor".',
    )
    opening_message = mark_safe_lazy(
        _(
            "<p>"
            "Chcete se stát velitelem svého firemního týmu? "
            "Nemusíte aktivně soutěžit, staňte se firemním koordinátorem. "
            "</p>"
            "<p>"
            "Pomáhejte kolegům ze svého týmu se všemi náležitostmi ohledně uhrazení startovného."
            "</p>"
            "<p>"
            "Vaší úlohou bude požádat zaměstnavatele, aby startovné za Váš tým uhradil. "
            "Poté zajistíte hromadnou platbu přes fakturu."
            "<a target='_blank' href='http://www.dopracenakole.cz/pro-firmy/firemni-koordinator'>Jak na to?</a>."
            "</p>"
            "<p>"
            "Nezůstanete bez odměny. Těšit se můžete na vděk svých kolegů a "
            "<a target='_blank' href='http://www.dopracenakole.cz/pro-firmy/firemni-koordinator'>velkou moc</a>, "
            "se kterou přichází velká zodpovědost."
            "</p>"
        ),
    )


class UserAttendanceParameterMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.user_attendance = request.user_attendance
        return super().dispatch(request, *args, **kwargs)


class UserAttendanceViewMixin(UserAttendanceParameterMixin):
    def get_object(self):
        if hasattr(self, "user_attendance"):
            return self.user_attendance


class RegistrationMessagesMixin(UserAttendanceParameterMixin):
    def get(self, request, *args, **kwargs):  # noqa
        ret_val = super().get(request, *args, **kwargs)

        notification_types.UnapprovedMembersInTeam(self.registration_phase).update(
            self.user_attendance
        )
        notification_types.AloneInTeam(self.registration_phase).update(
            self.user_attendance
        )
        if self.registration_phase == "registration_uncomplete":
            if self.user_attendance.team:
                if self.user_attendance.approved_for_team == "undecided":
                    messages.error(
                        request,
                        format_html(
                            _(
                                "<b>Podpořte týmového ducha.</b><br/>"
                                "Vaši kolegové v týmu {team} ještě nepotvrdili Vaše členství. "
                                "<a href='{address}'>Je na čase je trochu popostrčit</a>."
                            ),
                            team=self.user_attendance.team.name,
                            address=reverse("zaslat_zadost_clenstvi"),
                        ),
                    )
                elif self.user_attendance.approved_for_team == "denied":
                    messages.error(
                        request,
                        mark_safe(
                            _(
                                'Vaše členství v týmu bylo bohužel zamítnuto, budete si muset <a href="%s">zvolit jiný tým</a>',
                            )
                            % reverse("zmenit_tym"),
                        ),
                    )

            if not self.user_attendance.has_paid():
                messages.error(
                    request,
                    format_html(
                        _(
                            "<b>Pořádek dělá přátele.</b><br/>"
                            "Vaše platba ({payment_type}) je stále v řízení. "
                            "Počkejte prosím na její schválení. "
                            'Nebo si <a href="{url}">vyberte jiný způsob platby</a>.'
                        ),
                        payment_type=self.user_attendance.payment_type_string(),
                        url=reverse("typ_platby"),
                    ),
                )

        if self.registration_phase == "profile_view":
            questionnaires = models.Competition.objects.filter(
                campaign=self.user_attendance.campaign,
                competition_type="questionnaire",
            )
            for questionnaire in questionnaires:
                notification_types.Questionnaire(questionnaire).update(
                    self.user_attendance
                )
        company_admin = self.user_attendance.related_company_admin
        if company_admin and company_admin.company_admin_approved == "undecided":
            messages.error(
                request,
                _("Vaše žádost o funkci koordinátora organizace čeká na vyřízení."),
            )
        if company_admin and company_admin.company_admin_approved == "denied":
            messages.error(
                request,
                _("Vaše žádost o funkci koordinátora organizace byla zamítnuta."),
            )
        return ret_val


class TitleViewMixin(object):
    @classonlymethod
    def as_view(self, *args, **kwargs):
        if "title" in kwargs:
            self.title = kwargs.get("title")
        return super().as_view(*args, **kwargs)

    def get_title(self, *args, **kwargs):
        return self.title

    def get_opening_message(self, *args, **kwargs):
        if hasattr(self, "opening_message"):
            return self.opening_message
        else:
            return ""

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data["title"] = self.get_title(*args, **kwargs)
        context_data["opening_message"] = self.get_opening_message(*args, **kwargs)
        return context_data


class RegistrationPersonalViewMixin(
    RegistrationMessagesMixin, TitleViewMixin, UserAttendanceViewMixin
):
    template_name = "base_generic_registration_form.html"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data["registration_phase"] = self.registration_phase
        return context_data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self, "prev_url"):
            kwargs["prev_url"] = self.prev_url
        return kwargs

    def get_next_url(self):
        return self.next_url

    def get_success_url(self):
        if "next" in self.request.POST:
            return reverse(self.get_next_url())
        elif "submit" in self.request.POST:
            if self.success_url:
                return reverse(self.success_url)
            else:
                return reverse(self.registration_phase)
        else:
            return reverse(self.prev_url)


class RegistrationViewMixin(
    MustBeInRegistrationPhaseMixin, RegistrationPersonalViewMixin
):
    pass


class UserAttendanceFormKwargsMixin(object):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user_attendance"] = self.user_attendance
        return kwargs


class CampaignParameterMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.campaign = self.request.campaign
        return super().dispatch(request, *args, **kwargs)


class CampaignFormKwargsMixin(CampaignParameterMixin):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["campaign"] = self.campaign
        return kwargs


class RequestFormMixin(CampaignParameterMixin):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class ExportViewMixin:
    def generate_export(self, export_data, extension):
        fformat = {
            "csv": {
                "export": export_data.csv,
                "content_type": "text/csv; encoding=utf-8",
                "filename_extension": "csv",
            },
            "ods": {
                "export": export_data.ods,
                "content_type": "text/xml; encoding=utf-8",
                "filename_extension": "ods",
            },
            "xls": {
                "export": export_data.xls,
                "content_type": "application/vnd.ms-excel",
                "filename_extension": "xls",
            },
        }[extension]
        response = HttpResponse(fformat["export"], content_type=fformat["content_type"])
        response["Content-Disposition"] = (
            "attachment; filename=results.%s" % fformat["filename_extension"]
        )
        return response


class ProfileRedirectMixin(object):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse("profil"))
        else:
            return super().get(request, *args, **kwargs)
