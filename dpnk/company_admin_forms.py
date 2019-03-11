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
from crispy_forms.layout import HTML, Layout

from django import forms
from django.contrib.auth.models import User
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils.html import format_html
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from selectable.forms.widgets import AutoCompleteSelectWidget

from table_select_widget import TableSelectMultiple

from . import models
from .forms import AddressForm, RegistrationBaseForm, SubmitMixin, UserAttendanceUpdateForm
from .models import Campaign, City, Company, CompanyAdmin, Competition, Invoice, Subsidiary, UserAttendance


class SelectUsersPayForm(SubmitMixin, forms.Form):
    submit_text = _('Schválit')
    paying_for = forms.ModelMultipleChoiceField(
        UserAttendance.objects.none(),
        label=_("Vyberte týmové hráče, za které Vaše společnost zaplatí startovné."),
        required=False,
        help_text=_("Ceny jsou uváděny bez DPH"),
        widget=TableSelectMultiple(
            item_attrs=[
                ('company_admission_fee_intcomma', _("Částka")),
                ('userprofile__user__first_name', _("Jméno")),
                ('userprofile__user__last_name', _("Příjmení")),
                ('userprofile__nickname', _("Přezdívka")),
                ('userprofile__user__email', _("E-mail")),
                ('team__subsidiary__city', _("Město")),
                ('created', _("Čas registrace")),
            ],
            enable_shift_select=True,
            enable_datatables=True,
            bootstrap_style=True,
        ),
    )

    def __init__(self, request=None, *args, **kwargs):
        initial = kwargs.pop('initial', None)
        company_admin = initial['company_admin']
        queryset = UserAttendance.objects.filter(
            team__subsidiary__company=company_admin.administrated_company,
            campaign=company_admin.campaign,
            userprofile__user__is_active=True,
            representative_payment__pay_type='fc',
        ).exclude(
            payment_status='done',
        ).select_related(
            'userprofile__user',
            'campaign',
            'team__subsidiary__city',
            't_shirt_size',
            'representative_payment',
        ).order_by(
            'team__subsidiary__city',
            'userprofile__user__last_name',
            'userprofile__user__first_name',
        )

        ret_val = super().__init__(*args, **kwargs)
        self.fields['paying_for'].queryset = queryset
        self.helper.form_class = "dirty-check"
        self.helper.form_id = "fa-select-users-pay-form"
        self.helper.layout = Layout(
            HTML("<div class='text-info'>"),
            HTML(_("Tip: Použijte shift pro výběr rozsahu položek.")),
            HTML("</div><br/>"),
            'paying_for',
        )

        self.fields['paying_for'].widget.datatable_options = {
            'language': {'url': static("/js/datatables-plugins/i18n/%s.json" % request.LANGUAGE_CODE)},
        }
        return ret_val


class CompanyForm(SubmitMixin, AddressForm):
    submit_text = _('Hotovo')

    class Meta:
        model = Company
        fields = ('name', 'address_recipient', 'address_street', 'address_street_number', 'address_psc', 'address_city', 'ico', 'dic')
        error_messages = {
            'ico': {'stdnum_format': models.company.ICO_ERROR_MESSAGE},
            'dic': {'stdnum_format': models.company.DIC_ERROR_MESSAGE},
        }

    def __init__(self, request=None, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        self.fields['address_recipient'].label = _(u"Adresát na faktuře")
        self.fields['address_recipient'].help_text = _("Zadejte pokud potřebujete mít na faktuře jiného adresáta, než název společnosti.")
        self.fields['ico'].required = True
        self.helper.layout.insert(1, 'name')
        self.helper.layout.append('ico')
        self.helper.layout.append('dic')
        self.helper.form_id = "fa-company-address-form"
        return ret_val


class SubsidiaryForm(SubmitMixin, AddressForm):
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


class CompanyAdminForm(SubmitMixin, UserAttendanceUpdateForm):
    motivation_company_admin = forms.CharField(
        label=_("S kým máme tu čest?"),
        help_text=_(
            "Řekněte nám něco o pozici, kterou ve společnosti zastupujete."
        ),
        max_length=100,
        required=True,
    )
    will_pay_opt_in = forms.BooleanField(
        label=_("Zajistím, aby společnost uhradila startovné za náš zaměstnanecký tým."),
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
        super().__init__(*args, **kwargs)
        self.helper.form_class = "noAsterisks"
        self.helper.form_id = "fa-company-admin-form"


class CompanyAdminApplicationForm(CompanyAdminForm, RegistrationBaseForm):
    administrated_company = forms.ModelChoiceField(
        label=_("Název společnosti"),
        widget=AutoCompleteSelectWidget(
            lookup_class='dpnk.lookups.CompanyLookup',
            attrs={
                'class': "autocompletewidget form-control textinput textInput form-control",
                'name': 'admin_company',
            },
        ),
        queryset=Company.objects.all(),
        required=True,
        help_text=_("Začnete psát název organizace a vyberte si z nabídky."),
    )
    telephone = forms.CharField(
        label="Telefon",
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

    def clean_administrated_company(self):
        company = self.cleaned_data['administrated_company']
        campaign = self.get_campaign()
        if CompanyAdmin.objects.filter(administrated_company__pk=company.pk, campaign=campaign, company_admin_approved='approved').exists():
            raise forms.ValidationError(_(u"Tato organizace již má svého firemního koordinátora."))
        return company

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
    submit_text = _('Vypsat')
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
        fields = ('name', 'url', 'competition_type', 'competitor_type', 'commute_modes')

    def clean_name(self):
        if not self.instance.pk:
            self.instance.slug = 'FA-%s-%s' % (self.instance.campaign.pk, slugify(self.cleaned_data['name'])[0:30])
            if Competition.objects.filter(slug=self.instance.slug).exists():
                raise forms.ValidationError(
                    _(u"%(model_name)s with this %(field_label)s already exists.") % {
                        "model_name": self.instance._meta.verbose_name, "field_label": self.instance._meta.get_field('name').verbose_name,
                    },
                )
        return self.cleaned_data['name']


class CreateInvoiceForm(SubmitMixin, forms.ModelForm):
    submit_text = _('Vystavit fakturu')

    create_invoice = forms.BooleanField(
        label=_("Údaje jsou správné. Chci vytvořit fakturu"),
    )

    def __init__(self, request=None, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        amount = kwargs['initial']['campaign'].benefitial_admission_fee_company
        self.fields['company_pais_benefitial_fee'].help_text = format_html(
            _("Benefiční startovné je {amount} Kč za osobu bez DPH."),
            amount=amount,
        )
        return ret_val

    class Meta:
        model = Invoice
        fields = ('company_pais_benefitial_fee', 'order_number', 'create_invoice')
