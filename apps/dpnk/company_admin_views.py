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
import django.contrib.auth
from django.views.generic.edit import UpdateView, FormView
from decorators import must_be_company_admin
from company_admin_forms import SelectUsersPayForm, CompanyForm, CompanyAdminApplicationForm
from wp_urls import wp_reverse
from util import redirect
from models import Company, CompanyAdmin, Payment
import registration.signals, registration.backends
import registration.backends.simple

@must_be_company_admin
@login_required
def company_structure(request,
        template = 'company_admin/structure.html',
        ):
    return render_to_response(template,
                              {
                                'company': request.user.company_admin.administrated_company,
                                }, context_instance=RequestContext(request))

class SelectUsersPayView(FormView):
    template_name = 'company_admin/pay_for_users.html'
    form_class = SelectUsersPayForm
    success_url = 'company_admin'

    def get_initial(self, **kwargs):
        return self.request.user.company_admin.administrated_company

    def form_valid(self, form):
        for userprofile in form.cleaned_data['paing_for']:
            for payment in userprofile.payments.all():
                if payment.pay_type == 'fc':
                    payment.status = Payment.Status.COMPANY_ACCEPTS
                    payment.save()
                    break
        super(SelectUsersPayView, self).form_valid(form)
        return redirect(wp_reverse(self.success_url))

class CompanyEditView(UpdateView):
    template_name = 'company_admin/edit_company.html'
    form_class = CompanyForm
    model = Company
    success_url = 'company_admin'

    def get_object(self, queryset=None):
        return self.request.user.company_admin.administrated_company

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
