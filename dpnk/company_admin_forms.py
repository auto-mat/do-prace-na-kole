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

from ajax_select.fields import AutoCompleteSelectWidget

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import string_concat, ugettext_lazy as _

import registration.forms

from .forms import AdressForm
from .forms import SubmitMixin
from .models import Campaign, City, Company, CompanyAdmin, Competition, Invoice, Subsidiary, UserAttendance
from .util import slugify


class SelectUsersPayForm(SubmitMixin, forms.Form):
    paing_for = forms.ModelMultipleChoiceField(
        [],
        label=_(u"Soutěžící, za které bude zaplaceno"),
        help_text=string_concat(
            _(u"<div class='text-info'>Tip: Použijte ctrl nebo shift pro výběr více položek nebo jejich rozsahu.</div>"),
            _("<br/>Ceny jsou uváděny bez DPH"),
        ),
        widget=forms.SelectMultiple(attrs={'size': '40'}),
    )

    def __init__(self, *args, **kwargs):
        initial = kwargs.pop('initial', None)
        company_admin = initial['company_admin']
        queryset = UserAttendance.objects.filter(
            team__subsidiary__company=company_admin.administrated_company,
            campaign=company_admin.campaign,
            userprofile__user__is_active=True,
        )

        ret_val = super(SelectUsersPayForm, self).__init__(*args, **kwargs)
        self.fields['paing_for'].queryset = queryset
        choices = [
            (
                user_attendance.pk,
                u"%s Kč: %s (%s)" % (
                    user_attendance.company_admission_fee(),
                    user_attendance.userprofile.user.get_full_name(),
                    user_attendance.userprofile.user.email))
            for user_attendance in queryset.all()
            if user_attendance.representative_payment and user_attendance.representative_payment.pay_type == 'fc' and
            user_attendance.payment_status != 'done']
        self.fields['paing_for'].choices = choices
        return ret_val


class CompanyForm(SubmitMixin, AdressForm):
    class Meta:
        model = Company
        fields = ('name', 'address_recipient', 'address_street', 'address_street_number', 'address_psc', 'address_city', 'ico', 'dic')

    def __init__(self, request=None, *args, **kwargs):
        ret_val = super(CompanyForm, self).__init__(*args, **kwargs)
        self.fields['address_recipient'].label = _(u"Adresát na faktuře")
        self.fields['address_recipient'].help_text = _(u"Např. Výrobna, a.s., Příspěvková, p.o., Nevládka, o.s., Univerzita Karlova")
        return ret_val


class SubsidiaryForm(SubmitMixin, AdressForm):
    class Meta:
        model = Subsidiary
        fields = (
            'address_recipient',
            'address_street',
            'address_street_number',
            'address_psc',
            'address_city',
            'box_addressee_name',
            'box_addressee_telephone',
            'box_addressee_email',
            'city',
        )

    def __init__(self, *args, **kwargs):
        initial = kwargs.pop('initial', None)
        company_admin = initial['company_admin']
        ret_val = super().__init__(*args, **kwargs)
        self.fields['city'].queryset = City.objects.filter(cityincampaign__campaign=company_admin.campaign)
        return ret_val


class CompanyAdminForm(SubmitMixin, forms.ModelForm):
    motivation_company_admin = forms.CharField(
        label=_("Pár vět o vaší pozici"),
        help_text=_(
            "Napište nám prosím, jakou zastáváte u vašeho zaměstnavatele pozici, "
            "podle kterých můžeme ověřit, že vám funkci firemního koordinátora můžeme svěřit."
        ),
        max_length=100,
        required=True,
    )
    will_pay_opt_in = forms.BooleanField(
        label=_("Zavazuji se, že já, resp. moje organizace, uhradí startovné za zaměstnance jejichž platbu schválím."),
        required=True,
    )
    personal_data_opt_in = forms.BooleanField(
        required=True,
    )

    class Meta:
        model = CompanyAdmin
        fields = (
            'motivation_company_admin',
            'will_pay_opt_in',
            'personal_data_opt_in',
        )

    def get_campaign(self):
        return self.instance.campaign

    def __init__(self, request=None, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        self.fields['personal_data_opt_in'].label = _(
            "Souhlasím se zpracováním osobních údajů podle "
            "<a target='_blank' href='http://www.auto-mat.cz/zasady'>Zásad o ochraně a zpracování údajů Auto*Mat z.s.</a> "
            "a s <a target='_blank' href='http://www.dopracenakole.cz/obchodni-podminky'>Obchodními podmínkami soutěže %s</a>." % self.get_campaign(),
        )
        return ret_val


class CompanyAdminApplicationForm(CompanyAdminForm, registration.forms.RegistrationFormUniqueEmail):
    administrated_company = forms.ModelChoiceField(
        label=_(u"Koordinovaná organizace"),
        widget=AutoCompleteSelectWidget(
            'companies',
        ),
        queryset=Company.objects.all(),
        required=True,
    )
    telephone = forms.CharField(
        label="Telefon",
        help_text="Pro možnost kontaktování koordinátora organizace",
        max_length=30,
    )
    first_name = forms.CharField(
        label=_(u"Jméno"),
        max_length=30,
        required=True,
    )
    last_name = forms.CharField(
        label=_(u"Příjmení"),
        max_length=30,
        required=True,
    )
    campaign = forms.ModelChoiceField(
        widget=forms.widgets.HiddenInput(),
        queryset=Campaign.objects.all(),
        required=True,
    )
    username = forms.CharField(widget=forms.HiddenInput, required=False)

    def get_campaign(self):
        return self.initial['campaign']

    def clean(self):
        cleaned_data = super(CompanyAdminApplicationForm, self).clean()
        if not self.errors:
            self.cleaned_data['username'] = '%s%s' % (self.cleaned_data['email'].split('@', 1)[0], User.objects.count())

        if 'administrated_company' in cleaned_data:
            obj = cleaned_data['administrated_company']
            campaign = cleaned_data['campaign']
            if CompanyAdmin.objects.filter(administrated_company__pk=obj.pk, campaign=campaign, company_admin_approved='approved').exists():
                raise forms.ValidationError(_(u"Tato organizace již má svého firemního koordinátora."))
        return cleaned_data

    class Meta:
        model = User
        fields = (
            'campaign',
            'motivation_company_admin',
            'first_name',
            'last_name',
            'administrated_company',
            'email',
            'telephone',
            'password1',
            'password2',
            'username',
            'will_pay_opt_in',
            'personal_data_opt_in',
        )


class CompanyCompetitionForm(SubmitMixin, forms.ModelForm):
    competition_type = forms.ChoiceField(
        label=_(u"Typ soutěže"),
        choices=[x for x in Competition.CTYPES if x[0] != 'questionnaire'],
        required=True,
    )

    competitor_type = forms.ChoiceField(
        label=_(u"Typ soutěžícího"),
        choices=[x for x in Competition.CCOMPETITORTYPES if x[0] in ['single_user', 'team']],
        required=True,
    )

    class Meta:
        model = Competition
        fields = ('name', 'url', 'competition_type', 'competitor_type', 'sex', )

    def clean_name(self):
        if not self.instance.pk:
            self.instance.slug = 'FA-%s-%s' % (self.instance.campaign.slug, slugify(self.cleaned_data['name'])[0:30])
            if Competition.objects.filter(slug=self.instance.slug).exists():
                raise forms.ValidationError(
                    _(u"%(model_name)s with this %(field_label)s already exists.") % {
                        "model_name": self.instance._meta.verbose_name, "field_label": self.instance._meta.get_field('name').verbose_name,
                    },
                )
        return self.cleaned_data['name']

    def save(self, force_insert=False, force_update=False, commit=True):
        competition = super(CompanyCompetitionForm, self).save(commit=False)
        if commit:
            competition.save()
        return competition


class CreateInvoiceForm(SubmitMixin, forms.ModelForm):
    create_invoice = forms.BooleanField(
        label=_(u"Údaje jsou správné, v mé organizaci již nepřibudou žádní další soutěžící. Chci vytvořit fakturu"),
    )

    def __init__(self, request=None, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        amount = kwargs['initial']['campaign'].benefitial_admission_fee_company
        self.fields['company_pais_benefitial_fee'].help_text = _(u"Benefiční startovné je %i Kč za osobu bez DPH." % amount)
        return ret_val

    class Meta:
        model = Invoice
        fields = ('company_pais_benefitial_fee', 'order_number', 'create_invoice')
