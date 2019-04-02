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

import datetime
import logging

from braces.views import LoginRequiredMixin

from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import CreateView, FormView, UpdateView

from registration.backends.simple.views import RegistrationView

from . import company_admin_forms
from . import exceptions
from . import models
from .admin import UserAttendanceResource
from .company_admin_forms import (
    CompanyAdminApplicationForm, CompanyAdminForm, CompanyCompetitionForm, CompanyForm, SelectUsersPayForm, SubsidiaryForm,
)
from .email import company_admin_register_competitor_mail, company_admin_register_no_competitor_mail
from .models import Campaign, Company, CompanyAdmin, Competition, Payment, Subsidiary, UserProfile
from .models.transactions import Status
from .views import RegistrationViewMixin, TitleViewMixin
from .views_mixins import CampaignFormKwargsMixin, CompanyAdminMixin, ExportViewMixin, RequestFormMixin
from .views_permission_mixins import MustBeCompanyAdminMixin, MustBeInInvoicesPhaseMixin, MustBeInPaymentPhaseMixin, MustHaveTeamMixin
logger = logging.getLogger(__name__)


class CompanyStructure(TitleViewMixin, MustBeCompanyAdminMixin, LoginRequiredMixin, TemplateView):
    template_name = 'company_admin/structure.html'
    title = _("Společnost")

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data['company'] = self.company_admin.administrated_company
        context_data['subsidiaries'] = context_data['company'].subsidiaries.prefetch_related(
            'teams__users__userprofile__user',
            'teams__users__team__subsidiary__city',
            'teams__campaign',
            'teams__users__team__campaign',
            'teams__users__representative_payment',
        )
        context_data['company_address'] = models.get_address_string(self.company_admin.administrated_company.address)
        context_data['campaign'] = self.company_admin.campaign
        context_data['Status'] = models.Status
        return context_data


class UserAttendanceExportView(MustBeCompanyAdminMixin, ExportViewMixin, View):

    def dispatch(self, request, *args, extension="csv", **kwargs):
        super().dispatch(request, *args, **kwargs)
        queryset = models.UserAttendance.objects.filter(
            team__subsidiary__company=self.company_admin.administrated_company,
            campaign=request.campaign,
        )
        export_data = UserAttendanceResource().export(queryset)
        return self.generate_export(export_data, extension)


class RelatedCompetitionsView(MustBeCompanyAdminMixin, LoginRequiredMixin, TitleViewMixin, TemplateView):
    template_name = "company_admin/related_competitions.html"
    title = _("Oficiální soutěže")

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data['competitions'] = self.company_admin.administrated_company.get_related_competitions(self.company_admin.campaign)
        context_data['registration_phase'] = "competitions"
        return context_data


class SelectUsersPayView(
        SuccessMessageMixin,
        TitleViewMixin,
        MustBeInPaymentPhaseMixin,
        MustBeCompanyAdminMixin,
        LoginRequiredMixin,
        RequestFormMixin,
        FormView,
):
    template_name = 'company_admin/select_users_pay_for.html'
    form_class = SelectUsersPayForm
    success_url = reverse_lazy('company_admin_pay_for_users')
    success_message = _("Od teď mohou schválení hráči soutěžit.")
    title = _("Startovné")

    def get_initial(self):
        return {
            'company_admin': self.company_admin,
        }

    def form_valid(self, form):
        paying_for = form.cleaned_data['paying_for']
        self.confirmed_count = 0
        for user_attendance in paying_for:
            for payment in user_attendance.payments().all():
                if payment.pay_type == 'fc':
                    self.confirmed_count += 1
                    payment.status = models.Status.COMPANY_ACCEPTS
                    payment.amount = user_attendance.company_admission_fee()
                    payment.description = payment.description + "\nFA %s odsouhlasil dne %s" % (self.request.user.username, datetime.datetime.now())
                    payment.save()
                    break
        logger.info("Company admin %s is paying for following users: %s" % (self.request.user, map(lambda x: x, paying_for)))
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        company_admin = self.company_admin
        context_data["approved"] = Payment.objects.filter(
            user_attendance__team__subsidiary__company=company_admin.administrated_company,
            user_attendance__campaign=company_admin.campaign,
            user_attendance__userprofile__user__is_active=True,
            pay_type='fc',
            payment_status=Status.COMPANY_ACCEPTS,
        ).select_related(
            'user_attendance',
            'user_attendance__userprofile',
            'user_attendance__userprofile__user',
            'user_attendance__team__subsidiary',
        )
        context_data["total_approved_count"] = len(context_data["approved"])
        context_data["total_approved_amount"] = sum(ua.amount for ua in context_data["approved"])
        return context_data

    def dispatch(self, request, *args, **kwargs):
        ret_val = super().dispatch(request, *args, **kwargs)
        if request.user_attendance:
            if not self.company_admin.can_confirm_payments:
                raise exceptions.TemplatePermissionDenied(
                    _("Potvrzování plateb nemáte povoleno"),
                    self.template_name,
                )
            if not self.company_admin.administrated_company.ico:
                raise exceptions.TemplatePermissionDenied(
                    mark_safe(
                        _("Než schválíte startovné za Vaše zaměstnance, %s.") %
                        "<a href='%s'>%s</a>" % (
                            reverse('edit_company'),
                            _("vyplňte prosím IČO společnosti"),
                        ),
                    ),
                    self.template_name,
                    title=_("Podělíte se o firemní IČO?"),
                )
        return ret_val

    def get_success_message(self, cleaned_data):
        return self.success_message


class CompanyEditView(TitleViewMixin, MustBeCompanyAdminMixin, LoginRequiredMixin, UpdateView):
    template_name = 'base_generic_form.html'
    form_class = CompanyForm
    model = Company
    success_url = reverse_lazy('company_structure')
    title = _("Adresa společnosti")

    def get_object(self, queryset=None):
        return self.company_admin.administrated_company


class CompanyAdminApplicationView(CampaignFormKwargsMixin, TitleViewMixin, CompanyAdminMixin, RegistrationView):
    template_name = 'base_login.html'
    form_class = CompanyAdminApplicationForm
    model = CompanyAdmin
    success_url = reverse_lazy('company_structure')
    title = _("Registrace nesoutěžícího firemního koordinátora")

    def get_initial(self):
        return {
            'campaign': Campaign.objects.get(slug=self.request.subdomain),
        }

    def form_valid(self, form):
        ret_val = super().form_valid(form)
        new_user = self.request.user
        userprofile = UserProfile(
            user=new_user,
            telephone=form.cleaned_data['telephone'],
        )
        userprofile.save()

        admin = CompanyAdmin(
            motivation_company_admin=form.cleaned_data['motivation_company_admin'],
            will_pay_opt_in=form.cleaned_data['will_pay_opt_in'],
            administrated_company=form.cleaned_data['administrated_company'],
            campaign=form.cleaned_data['campaign'],
            userprofile=userprofile,
        )
        admin.save()
        company_admin_register_no_competitor_mail(admin)
        return ret_val


class CompanyAdminView(CampaignFormKwargsMixin, RegistrationViewMixin, CompanyAdminMixin, MustHaveTeamMixin, LoginRequiredMixin, UpdateView):
    template_name = 'base_generic_registration_form.html'
    form_class = CompanyAdminForm
    model = CompanyAdmin
    success_url = 'profil'
    registration_phase = "typ_platby"
    title = _("Chci se stát firemním koordinátorem")

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        old_company_admin = self.user_attendance.team.subsidiary.company.company_admin.\
            filter(campaign=self.user_attendance.campaign, company_admin_approved='approved').\
            exclude(pk=self.company_admin.pk)
        if old_company_admin.exists():
            return {
                'fullpage_error_message': _("Vaše organizce již svého koordinátora má: %s.") % (", ".join([str(c) for c in old_company_admin.all()])),
                'title': _("Organizace firemního koordinátora má"),
            }
        return context_data

    def get_object(self, queryset=None):
        campaign = self.user_attendance.campaign
        try:
            self.company_admin = self.request.user.userprofile.company_admin.get(campaign=campaign)
        except CompanyAdmin.DoesNotExist:
            self.company_admin = CompanyAdmin(userprofile=self.request.user.userprofile, campaign=campaign)
        self.company_admin.administrated_company = self.user_attendance.team.subsidiary.company
        return self.company_admin

    def form_valid(self, form):
        ret_val = super().form_valid(form)
        company_admin_register_competitor_mail(self.user_attendance)
        return ret_val


class EditSubsidiaryView(TitleViewMixin, MustBeCompanyAdminMixin, LoginRequiredMixin, UpdateView):
    template_name = 'base_generic_form.html'
    form_class = SubsidiaryForm
    success_url = reverse_lazy('company_structure')
    model = Subsidiary
    title = _("Upravit adresu pobočky")

    def get_initial(self):
        return {
            'company_admin': self.company_admin,
        }

    def get_queryset(self):
        return super().get_queryset().filter(company=self.company_admin.administrated_company)


class CompanyViewException(Exception):
    pass


class CompanyCompetitionView(TitleViewMixin, MustBeCompanyAdminMixin, LoginRequiredMixin, UpdateView):
    template_name = 'base_generic_form.html'
    form_class = CompanyCompetitionForm
    model = Competition
    success_url = reverse_lazy('company_admin_competitions')
    title = _("Vypsat firemní soutěž")

    def get(self, *args, **kwargs):
        try:
            return super().get(*args, **kwargs)
        except CompanyViewException as e:
            return render(self.request, self.template_name, context={'fullpage_error_message': e.args[0], 'title': e.args[1]})

    def get_object(self, queryset=None):
        company = self.company_admin.administrated_company
        competition_slug = self.kwargs.get('competition_slug', None)
        campaign = self.company_admin.campaign
        if competition_slug:
            competition = get_object_or_404(Competition.objects, slug=competition_slug)
            if competition.company != company:
                raise CompanyViewException(_(u"K editování této soutěže nemáte oprávnění."), _("Nedostatečné oprávnění"))
        else:
            if Competition.objects.filter(company=company, campaign=campaign).count() >= settings.MAX_COMPETITIONS_PER_COMPANY:
                raise CompanyViewException(_(u"Překročen maximální počet soutěží pro organizaci."), _("Dosažen maximální počet soutěží"))
            phase = campaign.phase('competition')
            competition = Competition(company=company, campaign=campaign, date_from=phase.date_from, date_to=phase.date_to)
        return competition

    def get_initial(self):
        if self.object.id is None:
            return {'commute_modes': models.competition.default_commute_modes()}


class CompanyCompetitionsShowView(TitleViewMixin, MustBeCompanyAdminMixin, LoginRequiredMixin, TemplateView):
    template_name = 'company_admin/competitions.html'
    title = _("Firemní soutěže")

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['competitions'] = self.company_admin.administrated_company.competition_set.filter(campaign=self.company_admin.campaign)
        return context_data


class InvoicesView(TitleViewMixin, MustBeInInvoicesPhaseMixin, MustBeCompanyAdminMixin, LoginRequiredMixin, CreateView):
    template_name = 'company_admin/create_invoice.html'
    form_class = company_admin_forms.CreateInvoiceForm
    success_url = reverse_lazy('invoices')
    title = _("Faktury")

    def get_initial(self):
        campaign = Campaign.objects.get(slug=self.request.subdomain)
        return {
            'campaign': campaign,
        }

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.company = self.company_admin.administrated_company
        self.object.campaign = self.company_admin.campaign
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        payments = models.payments_to_invoice(self.company_admin.administrated_company, self.company_admin.campaign)
        context['payments'] = payments
        context['company'] = self.company_admin.administrated_company

        context['invoices'] = self.company_admin.administrated_company.invoice_set.filter(campaign=self.company_admin.campaign)
        return context

    def dispatch(self, request, *args, **kwargs):
        ret_val = super().dispatch(request, *args, **kwargs)
        if request.user_attendance:
            if not self.company_admin.administrated_company.has_filled_contact_information():
                raise exceptions.TemplatePermissionDenied(
                    mark_safe(
                        _("Před vystavením faktury %s.") %
                        "<a href='%s'>%s</a>" % (
                            reverse('edit_company'),
                            _("prosím vyplňte údaje o Vaší společnosti"),
                        ),
                    ),
                    self.template_name,
                    title=_("Řekněte nám něco o sobě"),
                )
            if not self.company_admin.can_confirm_payments:
                raise exceptions.TemplatePermissionDenied(
                    _("Vystavování faktur nemáte povoleno"),
                    self.template_name,
                )
        return ret_val
