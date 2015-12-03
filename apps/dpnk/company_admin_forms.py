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

from django import forms
from .forms import AdressForm
from .models import Company, CompanyAdmin, Competition, UserAttendance, Campaign, Invoice
from django.utils.translation import ugettext_lazy as _
from .util import slugify
from .forms import SubmitMixin
import registration.forms


class SelectUsersPayForm(SubmitMixin, forms.Form):
    paing_for = forms.ModelMultipleChoiceField(
        [],
        label=_(u"Soutěžící, za které bude zaplaceno"),
        help_text=_(u"<div class='text-info'>Tip: Použijte ctrl nebo shift pro výběr více položek nebo jejich rozsahu.</div>"),
        widget=forms.SelectMultiple(attrs={'size': '40'}),
    )

    def __init__(self, *args, **kwargs):
        initial = kwargs.pop('initial', None)
        company_admin = initial['company_admin']
        queryset = UserAttendance.objects.filter(team__subsidiary__company=company_admin.administrated_company, campaign=company_admin.campaign, userprofile__user__is_active=True)

        ret_val = super(SelectUsersPayForm, self).__init__(*args, **kwargs)
        self.fields['paing_for'].queryset = queryset
        choices = [
            (
                user_attendance.pk,
                u"%s Kč: %s (%s)" % (
                    user_attendance.payment()['payment'].amount,
                    user_attendance.userprofile.user.get_full_name(),
                    user_attendance.userprofile.user.email))
            for user_attendance in queryset.all()
            if user_attendance.payment_type() == 'fc' and
            user_attendance.payment_status() != 'done']
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


class CompanyAdminForm(SubmitMixin, forms.ModelForm):
    class Meta:
        model = CompanyAdmin
        fields = ('motivation_company_admin', )

    def __init__(self, request=None, *args, **kwargs):
        ret_val = super(CompanyAdminForm, self).__init__(*args, **kwargs)
        return ret_val


class CompanyAdminApplicationForm(SubmitMixin, registration.forms.RegistrationFormUniqueEmail):
    motivation_company_admin = forms.CharField(
        label=_(u"Pár vět o vaší pozici"),
        help_text=_(u"Napište nám prosím, jakou zastáváte u Vašeho zaměstnavatele pozici, podle kterých můžeme ověřit, že vám funkci firemního administrátora můžeme svěřit."),
        max_length=5000,
        widget=forms.Textarea,
        required=True)
    administrated_company = forms.ModelChoiceField(
        label=_(u"Administrovaná firma"),
        queryset=Company.objects.all(),
        required=True)
    telephone = forms.CharField(
        label="Telefon",
        help_text="Pro možnost kontaktování firemního administrátora",
        max_length=30)
    first_name = forms.CharField(
        label=_(u"Jméno"),
        max_length=30,
        required=True)
    last_name = forms.CharField(
        label=_(u"Příjmení"),
        max_length=30,
        required=True)
    campaign = forms.ModelChoiceField(
        widget=forms.widgets.HiddenInput(),
        queryset=Campaign.objects.all(),
        required=True)

    def clean(self):
        cleaned_data = super(CompanyAdminApplicationForm, self).clean()
        if 'administrated_company' in cleaned_data:
            obj = cleaned_data['administrated_company']
            campaign = cleaned_data['campaign']
            if CompanyAdmin.objects.filter(administrated_company__pk=obj.pk, campaign=campaign).exists():
                raise forms.ValidationError(_(u"Tato společnost již má svého koordinátora."))
        return cleaned_data

    def __init__(self, request=None, *args, **kwargs):
        ret_val = super(CompanyAdminApplicationForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = [
            'campaign',
            'motivation_company_admin',
            'first_name',
            'last_name',
            'administrated_company',
            'email',
            'telephone',
            'username',
            'password1',
            'password2'
        ]

        # self.fields['email'].help_text=_(u"Pro informace v průběhu kampaně, k zaslání zapomenutého loginu")
        return ret_val

    class Meta:
        model = CompanyAdmin
        fields = "__all__"


class CompanyCompetitionForm(SubmitMixin, forms.ModelForm):
    type = forms.ChoiceField(
        label=_(u"Typ soutěže"),
        choices=[x for x in Competition.CTYPES if x[0] != 'questionnaire'],
        required=True)

    competitor_type = forms.ChoiceField(
        label=_(u"Typ soutěžícího"),
        choices=[x for x in Competition.CCOMPETITORTYPES if x[0] in ['single_user', 'team']],
        required=True)

    class Meta:
        model = Competition
        fields = ('name', 'url', 'type', 'competitor_type', )

    def clean_name(self):
        if not self.instance.pk:
            self.instance.slug = 'FA-%s-%s' % (self.instance.campaign.slug, slugify(self.cleaned_data['name'])[0:30])
            if Competition.objects.filter(slug=self.instance.slug).exists():
                raise forms.ValidationError(_(u"%(model_name)s with this %(field_label)s already exists.") % {
                    "model_name": self.instance._meta.verbose_name, "field_label": self.instance._meta.get_field('name').verbose_name})
        return self.cleaned_data['name']

    def save(self, force_insert=False, force_update=False, commit=True):
        competition = super(CompanyCompetitionForm, self).save(commit=False)
        if commit:
            competition.save()
        return competition


class CreateInvoiceForm(SubmitMixin, forms.ModelForm):
    create_invoice = forms.BooleanField(
        label=_(u"Údaje jsou správné, chci vytvořit fakturu"),
    )

    class Meta:
        model = Invoice
        fields = ('company_pais_benefitial_fee', 'order_number', 'create_invoice')
