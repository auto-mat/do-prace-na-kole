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

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.http import Http404
import django.contrib.auth
from django.conf import settings
from django.views.generic.edit import UpdateView, FormView
from decorators import must_be_company_admin
from company_admin_forms import SelectUsersPayForm, CompanyForm, CompanyAdminApplicationForm, CompanyAdminForm, CompanyCompetitionForm
from dpnk.email import company_admin_register_competitor_mail, company_admin_register_no_competitor_mail
from wp_urls import wp_reverse
from util import redirect
from models import Company, CompanyAdmin, Payment, Competition, Campaign
import models
import registration.signals, registration.backends
import registration.backends.simple
import logging
logger = logging.getLogger(__name__)

@must_be_company_admin
@login_required
def company_structure(request,
        template = 'company_admin/structure.html',
        administrated_company = None,
        ):
    return render_to_response(template,
                              {
                                'company': administrated_company,
                                }, context_instance=RequestContext(request))

class SelectUsersPayView(FormView):
    template_name = 'company_admin/pay_for_users.html'
    form_class = SelectUsersPayForm
    success_url = 'company_admin'

    def get_initial(self, **kwargs):
        return self.request.user.company_admin.get_administrated_company()

    def form_valid(self, form):
        paing_for = form.cleaned_data['paing_for']
        for userprofile in paing_for:
            for payment in userprofile.payments.all():
                if payment.pay_type == 'fc':
                    payment.status = Payment.Status.COMPANY_ACCEPTS
                    payment.save()
                    break
        logger.info("Company admin %s is paing for following users: %s" % (self.request.user, map(lambda x: x, paing_for)))
        super(SelectUsersPayView, self).form_valid(form)
        return redirect(wp_reverse(self.success_url))

class CompanyEditView(UpdateView):
    template_name = 'company_admin/edit_company.html'
    form_class = CompanyForm
    model = Company
    success_url = 'company_admin'

    def get_object(self, queryset=None):
        return self.request.user.company_admin.get_administrated_company()

    def form_valid(self, form):
        super(CompanyEditView, self).form_valid(form)
        return redirect(wp_reverse(self.success_url))

class CompanyAdminRegistrationBackend(registration.backends.simple.SimpleBackend):
    def register(self, request, **cleaned_data):
        new_user = super(CompanyAdminRegistrationBackend, self).register(request, **cleaned_data)

        new_user.first_name = cleaned_data['first_name']
        new_user.last_name = cleaned_data['last_name']
        new_user.save()

        admin = CompanyAdmin(
            motivation_company_admin = cleaned_data['motivation_company_admin'],
            telephone = cleaned_data['telephone'],
            administrated_company = cleaned_data['administrated_company'],
            user = new_user,
        )
        admin.save()
        company_admin_register_no_competitor_mail(admin.user)
        return new_user

class CompanyAdminApplicationView(FormView):
    template_name = 'generic_form_template.html'
    form_class = CompanyAdminApplicationForm
    model = CompanyAdmin
    success_url = 'company_admin'

    def form_valid(self, form, backend='dpnk.company_admin_views.CompanyAdminRegistrationBackend'):
        super(CompanyAdminApplicationView, self).form_valid(form)
        backend = registration.backends.get_backend(backend)
        new_user = backend.register(self.request, **form.cleaned_data)
        auth_user = django.contrib.auth.authenticate(
            username=self.request.POST['username'],
            password=self.request.POST['password1'])
        django.contrib.auth.login(self.request, auth_user)

        return redirect(wp_reverse(self.success_url))

class CompanyAdminView(UpdateView):
    template_name = 'generic_form_template.html'
    form_class = CompanyAdminForm
    model = CompanyAdmin
    success_url = 'profil'

    def get_object(self, queryset=None):
        try:
            company_admin = self.request.user.company_admin
        except CompanyAdmin.DoesNotExist:
            company_admin = CompanyAdmin(user = self.request.user)
        company_admin.administrated_company = models.UserAttendance.objects.get(campaign__slug=self.kwargs['campaign_slug'], userprofile=self.request.user.userprofile).team.subsidiary.company
        company_admin.save()
        return company_admin

    def form_valid(self, form):
        super(CompanyAdminView, self).form_valid(form)
        company_admin_register_competitor_mail(self.request.user, models.UserAttendance.objects.get(campaign__slug=self.kwargs['campaign_slug'], userprofile=self.request.user.userprofile))
        return redirect(wp_reverse(self.success_url))

class CompanyCompetitionView(UpdateView):
    template_name = 'generic_form_template.html'
    form_class = CompanyCompetitionForm
    model = Competition
    success_url = 'company_admin'

    def __init__(self, *args, **kwargs):
        ret_val = super(CompanyCompetitionView, self).__init__(*args, **kwargs)
        return ret_val

    def get_object(self, queryset=None):
        company = self.request.user.company_admin.administrated_company
        competition_slug = self.kwargs.get('competition_slug', None)
        campaign_slug = self.kwargs.get('campaign_slug', None)
        campaign = Campaign.objects.get(slug = campaign_slug)
        if competition_slug:
            competition = get_object_or_404(Competition.objects, slug = competition_slug)
            if competition.company != company:
                raise Http404(_(u"<div class='text-error'>K editování této soutěže nemáte oprávnění.</div>"))
        else:
            if Competition.objects.filter(company = company).count() >= settings.MAX_COMPETITIONS_PER_COMPANY:
                raise Http404(_(u"<div class='text-error'>Překročen maximální počet soutěží.</div>"))
            phase = campaign.phase_set.get(type='competition')
            competition = Competition(company=company, campaign=campaign, date_from=phase.date_from, date_to=phase.date_to )
        return competition


    def form_valid(self, form):
        super(CompanyCompetitionView, self).form_valid(form)
        return redirect(wp_reverse(self.success_url))

@must_be_company_admin
@login_required
def competitions(request,
        template = 'company_admin/competitions.html',
        administrated_company = None,
        ):
    return render_to_response(template,
                              {
                                'competitions': Competition.objects.filter(company = administrated_company),
                                }, context_instance=RequestContext(request))
