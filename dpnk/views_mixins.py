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
from django.urls import reverse, reverse_lazy
from django.utils.decorators import classonlymethod
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .util import mark_safe_lazy
from .views_permission_mixins import MustBeInRegistrationPhaseMixin


class CompanyAdminMixin(SuccessMessageMixin):
    success_message = _(
        "Byli jste úspěšně zaregistrování jako firemní koordinátor. "
        "Vaší organizaci můžete spravovat v menu \"Firemní koordinátor\".",
    )
    opening_message = mark_safe_lazy(
        _(
            "<p>"
            "Chcete se stát velitelem svého firemního týmu? "
            "Nemusíte aktivně soutěžit, staňte se firemním koordinátorem. "
            "</p>"
            "<p>"
            "Pomáhejte kolegům ze svého týmu se všemi náležitostmi ohledně uhrazení členského poplatku."
            "</p>"
            "<p>"
            "Vaší úlohou bude požádat zaměstnavatele, aby členský poplatek za Váš tým uhradil. "
            "Poté zajistíte hromadnou platbu přes fakturu. <a href='http://www.dopracenakole.cz/firemni-koordinator'>Jak na to?</a>."
            "</p>"
            "<p>"
            "Nezůstanete bez odměny. Těšit se můžete na vděk svých kolegů a naše speciální slevy pro "
            "<a href='http://www.dopracenakole.cz/firemni-koordinator'>firemní koordinátory</a>."
            "</p>"
        ),
    )


class UserAttendanceParameterMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.user_attendance = request.user_attendance
        return super().dispatch(request, *args, **kwargs)


class UserAttendanceViewMixin(UserAttendanceParameterMixin):
    def get_object(self):
        if hasattr(self, 'user_attendance'):
            return self.user_attendance


class RegistrationMessagesMixin(UserAttendanceParameterMixin):
    def get(self, request, *args, **kwargs):  # noqa
        ret_val = super().get(request, *args, **kwargs)

        if self.registration_phase in ('registration_uncomplete', 'profile_view'):
            if self.user_attendance.approved_for_team == 'approved' and \
                    self.user_attendance.team and \
                    self.user_attendance.team.unapproved_member_count and \
                    self.user_attendance.team.unapproved_member_count > 0:
                messages.warning(
                    request,
                    mark_safe(
                        _('Ve vašem týmu jsou neschválení členové, prosíme, <a href="%s">posuďte jejich členství</a>.') % reverse('team_members'),
                    ),
                )
            elif self.user_attendance.is_libero():
                # TODO: get WP slug for city
                messages.warning(
                    request,
                    format_html(
                        _(
                            'Jste sám/sama v týmu, znamená to že budete moci soutěžit pouze v kategoriích určených pro jednotlivce!'
                            ' <ul><li><a href="{invite_url}">Pozvěte</a> své kolegy do vašeho týmu, pokud jste tak již učinil/a, '
                            'vyčkejte na potvrzující e-mail a schvalte jejich členství v týmu.</li>'
                            '<li>Můžete se pokusit <a href="{join_team_url}">přidat se k jinému týmu</a>.</li>'
                            '<li>Pokud nemůžete sehnat spolupracovníky, '
                            ' <a href="https://www.dopracenakole.cz/locations/{city}/seznamka" target="_blank">najděte si cykloparťáka</a>.</li></ul>'
                        ),
                        invite_url=reverse('pozvanky'),
                        join_team_url=reverse('zmenit_tym'),
                        city=self.user_attendance.team.subsidiary.city.slug,
                    ),
                )
            if not self.user_attendance.track_complete() and self.user_attendance.campaign.tracks:
                messages.info(
                    request,
                    format_html(
                        "<b>{header}</b>"
                        "<br>"
                        "{body}"
                        "<br>"
                        "<br>"
                        "<a href='{track_link_url}'>{track_link_description}</a>",
                        header=_('Vyplňte typickou trasu'),
                        body=format_html(
                            _(
                                'Na této stránce si každý den zapište jízdy nebo zkontrolujte správné zapsání jízdy z mobilní aplikace. '
                                ' Pokud budete zadávat jízdy ručně, doporučujeme Vám pro usnadnění vyplnit si typickou trasu.'
                                ' Na základě typické trasy se v průběhu soutěže předvyplní vaše denní trasa a vzdálenost vaší cesty. '
                                ' Vaše vyplněná trasa se objeví na {heatmap_link}'
                                ' a pomůže při plánování cyklistické infrastruktury ve vašem městě.',
                            ),
                            heatmap_link=format_html(
                                '<a target="_blank" href="https://mapa.prahounakole.cz/?layers=_Wgt">{}</a>',
                                _("cyklistické dopravní heatmapě"),
                            ),
                        ),
                        track_link_url=reverse('upravit_trasu'),
                        track_link_description=_('Vyplnit typickou trasu'),
                    ),
                )

        if self.registration_phase == 'registration_uncomplete':
            if self.user_attendance.team:
                if self.user_attendance.approved_for_team == 'undecided':
                    messages.warning(
                        request,
                        format_html(
                            _(
                                "Vaši kolegové v týmu {team} ještě musí potvrdit vaše členství."
                                " Pokud to trvá podezřele dlouho, můžete zkusit"
                                " <a href='{address}'>znovu požádat o ověření členství</a>."),
                            team=self.user_attendance.team.name, address=reverse("zaslat_zadost_clenstvi"),
                        ),
                    )
                elif self.user_attendance.approved_for_team == 'denied':
                    messages.error(
                        request,
                        mark_safe(
                            _(
                                'Vaše členství v týmu bylo bohužel zamítnuto, budete si muset <a href="%s">zvolit jiný tým</a>',
                            ) % reverse('zmenit_tym'),
                        ),
                    )

            if not self.user_attendance.has_paid():
                messages.info(
                    request,
                    format_html(
                        _(
                            'Vaše platba typu {payment_type} ještě nebyla vyřízena. '
                            'Počkejte prosím na její schválení. '
                            'Pokud schválení není možné, můžete <a href="{url}">zadat jiný typ platby</a>. '
                            'Po schválení bude registrace dokončena a my vám tuto skutečnost potvrdíme e-mailem.',
                        ),
                        payment_type=self.user_attendance.payment_type_string(), url=reverse('typ_platby'),
                    ),
                )

        if self.registration_phase == 'profile_view':
            if self.user_attendance.has_unanswered_questionnaires:
                competitions = format_html_join(
                    ", ",
                    "<a href='{}'>{}</a>",
                    ((
                        reverse_lazy("questionnaire", kwargs={"questionnaire_slug": q.slug}),
                        q.name
                    ) for q in self.user_attendance.unanswered_questionnaires().all()),
                )
                messages.info(request, format_html(_('Nezapomeňte vyplnit odpovědi v následujících soutěžích: {}!'), competitions))

        company_admin = self.user_attendance.related_company_admin
        if company_admin and company_admin.company_admin_approved == 'undecided':
            messages.warning(request, _('Vaše žádost o funkci koordinátora organizace čeká na vyřízení.'))
        if company_admin and company_admin.company_admin_approved == 'denied':
            messages.error(request, _('Vaše žádost o funkci koordinátora organizace byla zamítnuta.'))
        return ret_val


class TitleViewMixin(object):
    @classonlymethod
    def as_view(self, *args, **kwargs):
        if 'title' in kwargs:
            self.title = kwargs.get('title')
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
        context_data['title'] = self.get_title(*args, **kwargs)
        context_data['opening_message'] = self.get_opening_message(*args, **kwargs)
        return context_data


class RegistrationViewMixin(RegistrationMessagesMixin, TitleViewMixin, UserAttendanceViewMixin, MustBeInRegistrationPhaseMixin):
    template_name = 'base_generic_registration_form.html'

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data['registration_phase'] = self.registration_phase
        return context_data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self, 'prev_url'):
            kwargs['prev_url'] = self.prev_url
        return kwargs

    def get_next_url(self):
        return self.next_url

    def get_success_url(self):
        if 'next' in self.request.POST:
            return reverse(self.get_next_url())
        elif 'submit' in self.request.POST:
            return reverse(self.success_url)
        else:
            return reverse(self.prev_url)


class UserAttendanceFormKwargsMixin(object):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user_attendance'] = self.user_attendance
        return kwargs


class CampaignParameterMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.campaign = self.request.campaign
        return super().dispatch(request, *args, **kwargs)


class CampaignFormKwargsMixin(CampaignParameterMixin):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['campaign'] = self.campaign
        return kwargs


class RequestFormMixin(CampaignParameterMixin):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class ExportViewMixin():
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
        response['Content-Disposition'] = 'attachment; filename=results.%s' % fformat["filename_extension"]
        return response
