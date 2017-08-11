# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2015 o.s. Auto*Mat
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

from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Div, Field, HTML, Layout, Submit

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import MinLengthValidator, RegexValidator
from django.db.models import Q
from django.forms.widgets import HiddenInput
from django.http import Http404
from django.utils import formats
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import string_concat, ugettext_lazy as _

from django_gpxpy import gpx_parse

from initial_field import InitialFieldsMixin

from leaflet.forms.widgets import LeafletWidget

import registration.forms

from selectable.forms.widgets import AutoCompleteSelectWidget

from smart_selects.form_fields import ChainedModelChoiceField

from . import email, models, util
from .fields import CommaFloatField, ShowPointsMultipleModelChoiceField
from .string_lazy import format_html_lazy, mark_safe_lazy
from .widgets import CommuteModeSelect

logger = logging.getLogger(__name__)


class UserLeafletWidget(LeafletWidget):
    def __init__(self, *args, **kwargs):
        user_attendance = kwargs['user_attendance']
        settings_overrides = {}
        if user_attendance.team and user_attendance.team.subsidiary.city.location:
            settings_overrides['DEFAULT_CENTER'] = (user_attendance.team.subsidiary.city.location.y, user_attendance.team.subsidiary.city.location.x)
            settings_overrides['DEFAULT_ZOOM'] = 13

        super(UserLeafletWidget, self).__init__(
            attrs={
                "geom_type": 'MULTILINESTRING',
                "map_height": "500px",
                "map_width": "100%",
                'settings_overrides': settings_overrides,
            },
        )


class SubmitMixin(object):
    def __init__(self, url_name="", *args, **kwargs):
        self.helper = FormHelper()
        super(SubmitMixin, self).__init__(*args, **kwargs)
        self.helper.add_input(Submit('submit', _(u'Odeslat')))


class PrevNextMixin(object):
    def __init__(self, url_name="", *args, **kwargs):
        self.helper = FormHelper()
        if not hasattr(self, 'no_prev'):
            prev_url = kwargs.pop('prev_url', None)
            if not hasattr(self, 'no_dirty'):
                self.helper.form_class = "dirty-check"
            self.helper.add_input(
                Button('prev', _('Předchozí'), css_class="btn-default form-actions", onclick='window.location.href="{}"'.format(reverse(prev_url))),
            )
        if not hasattr(self, 'no_next'):
            self.helper.add_input(Submit('next', _(u'Další'), css_class="form-actions"))
        return super(PrevNextMixin, self).__init__(*args, **kwargs)


class AuthenticationFormDPNK(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        campaign = kwargs.pop('campaign')
        ret_val = super(AuthenticationFormDPNK, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'username', 'password',
            HTML(
                format_html_lazy(
                    '<a class="btn btn-block btn-social btn-google" href="{{% url "social:begin" "google-oauth2" %}}">'
                    '  <span class="fa fa-google"></span>{}'
                    '</a>'
                    '<a class="btn btn-block btn-social btn-facebook" href="{{% url "social:begin" "facebook" %}}">'
                    '  <span class="fa fa-facebook"></span>{}'
                    '</a>'
                    '<br/><br/>',
                    _("Přihlásit se pomocí Google"),
                    _("Přihlásit se pomocí Facebooku"),
                ),
            ),
            HTML(
                _(
                    '<a href="{%% url "password_reset" %%}">Zapomněli jste své přihlašovací údaje?</a>'
                    '<br/><br/>'
                    'Ještě nemáte účet? <a href="{%% url "registration_access" %%}">Registrujte se</a> do soutěže %(campaign)s.'
                    '<br/><br/>'
                ) % {
                    'campaign': campaign,
                },
            ),
        )
        self.helper.add_input(Submit('submit', _(u'Přihlásit')))
        self.fields['username'].label = _(u"E-mail (uživatelské jméno)")
        return ret_val


class RegisterCompanyForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    def clean_ico(self):
        ico = self.cleaned_data['ico']
        if ico and models.Company.objects.filter(
            ico=ico,
            active=True,
        ).exists():
            raise ValidationError('Organizace s tímto IČO již existuje, nezakládemte prosím novou, ale vyberte jí prosím ze seznamu')

    class Meta:
        model = models.Company
        fields = ('name', 'ico')


class AddressForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    address_psc = forms.CharField(
        label=_(u"PSČ"),
        help_text=_(u"Např.: „130 00“"),
    )

    def clean_address_psc(self):
        address_psc = self.cleaned_data['address_psc']
        try:
            address_psc = int(address_psc.replace(' ', ''))
        except (TypeError, ValueError):
            raise ValidationError('PSČ musí být pěticiferné číslo')
        if address_psc > 99999 or address_psc < 10000:
            raise ValidationError('PSČ musí být pěticiferné číslo')
        return address_psc

    def __init__(self, *args, **kwargs):
        campaign = kwargs.pop('campaign', None)
        super(AddressForm, self).__init__(*args, **kwargs)
        if 'city' in self.fields:
            self.fields['city'].queryset = models.City.objects.filter(cityincampaign__campaign=campaign)

    class Meta:
        model = models.Subsidiary
        fields = ('city', 'address_recipient', 'address_street', 'address_street_number', 'address_psc', 'address_city')


class RegisterSubsidiaryForm(AddressForm):
    company = forms.ModelChoiceField(
        label=_("Organizace"),
        queryset=models.Company.objects.filter(active=True),
        widget=AutoCompleteSelectWidget(lookup_class='dpnk.lookups.CompanyLookup'),
        required=True,
    )

    class Meta:
        model = models.Subsidiary
        fields = ('company', 'city', 'address_recipient', 'address_street', 'address_street_number', 'address_psc', 'address_city')


class RegisterTeamForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    campaign = forms.ModelChoiceField(
        label=_(u"Kampaň"),
        queryset=models.Campaign.objects.all(),
        widget=HiddenInput(),
    )
    subsidiary = forms.ModelChoiceField(
        queryset=models.Subsidiary.objects.filter(active=True),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subsidiary'].queryset = kwargs['initial']['subsidiary'].company.subsidiaries.filter(active=True)
        self.fields['subsidiary'].empty_label = None

    class Meta:
        model = models.Team
        fields = ('subsidiary', 'name', 'campaign')


class ChangeTeamForm(PrevNextMixin, forms.ModelForm):
    company = forms.ModelChoiceField(
        label=_(u"Organizace"),
        queryset=models.Company.objects.filter(active=True),
        widget=AutoCompleteSelectWidget(lookup_class='dpnk.lookups.CompanyLookup'),
        required=True,
    )
    subsidiary = ChainedModelChoiceField(
        chained_field="company_1",
        to_app_name="dpnk",
        to_model_name="Subsidiary",
        chained_model_field="company",
        show_all=False,
        auto_choose=True,
        label=_(u"Adresa pobočky/organizace"),
        foreign_key_app_name="dpnk",
        foreign_key_model_name="Subsidiary",
        foreign_key_field_name="company",
        queryset=models.Subsidiary.objects.filter(active=True),
        required=True,
    )
    team = ChainedModelChoiceField(
        chained_field="subsidiary",
        to_app_name="dpnk",
        to_model_name="Team",
        chained_model_field="subsidiary",
        show_all=False,
        auto_choose=False,
        foreign_key_app_name="dpnk",
        foreign_key_model_name="Subsidiary",
        foreign_key_field_name="company",
        label=_(u"Tým"),
        queryset=models.Team.objects.all(),
        required=True,
    )

    def clean(self):
        cleaned_data = super(ChangeTeamForm, self).clean()

        if 'subsidiary' in cleaned_data:
            subsidiary = cleaned_data['subsidiary']
            if subsidiary and not models.CityInCampaign.objects.filter(city=subsidiary.city, campaign__slug=self.instance.campaign.slug).exists():
                logger.error("Subsidiary in city that doesn't belong to this campaign", extra={'subsidiary': subsidiary})
                raise forms.ValidationError(
                    _(
                        "Zvolená pobočka je registrována ve městě, které v aktuální kampani nesoutěží. "
                        "Prosím žádejte změnu po vašem vnitrofiremním koordinátorovi."
                    ),
                )

            if not self.instance.campaign.competitors_choose_team():  # We ask only for comapny and subsidiary
                team = cleaned_data['team']
                team.subsidiary = subsidiary
                team.save()
                self.instance.team = team
                self.instance.approved_for_team = 'approved'
                self.instance.save()

        return cleaned_data

    def clean_team(self):
        if self.instance.campaign.competitors_choose_team():  # We ask only for team
            team = self.cleaned_data['team']
            if team.campaign.slug != self.instance.campaign.slug:
                logger.error("Team not in campaign", extra={'team': team.pk, 'subdomain': self.instance.campaign.slug})
                raise forms.ValidationError(_("Zvolený tým není dostupný v aktuální kampani"))
        elif not self.instance.team:
                team = models.Team(campaign=self.instance.campaign)
        else:
            team = self.instance.team
        return team

    def save(self, *args, **kwargs):
        user_attendance = super().save(*args, **kwargs)
        if user_attendance.approved_for_team != 'approved':
            email.approval_request_mail(user_attendance)
        return user_attendance

    def __init__(self, *args, **kwargs):
        super(ChangeTeamForm, self).__init__(*args, **kwargs)

        self.fields["team"].widget.manager = 'team_in_campaign_%s' % self.instance.campaign.slug

        company = self.initial.get('company')
        subsidiary = self.initial.get('subsidiary')
        self.helper.layout = Layout(
            FieldWithButtons(
                'company',
                StrictButton(
                    string_concat('<span class="glyphicon glyphicon-plus"></span> ', _('Přidat společnost')),
                    href=reverse("register_company"),
                    data_fm_head=_("Vytvořit novou společnost"),
                    data_fm_callback="createCompanyCallback",
                    css_class="btn-success fm-create",
                    id="fm-create-company",
                ),
            ),
            FieldWithButtons(
                'subsidiary',
                StrictButton(
                    string_concat('<span class="glyphicon glyphicon-plus"></span> ', _('Přidat pobočku')),
                    href=reverse("register_subsidiary", args=(company.id,)) if company else "",
                    data_fm_head=_("Vytvořit novou pobočku"),
                    data_fm_callback="createSubsidiaryCallback",
                    css_class="btn-success fm-create",
                    id="fm-create-subsidiary",
                    **({'disabled': True} if company is None else {}),  # Disable button if no company is selected
                ),
            ),
            FieldWithButtons(
                'team',
                StrictButton(
                    string_concat('<span class="glyphicon glyphicon-plus"></span> ', _('Přidat tým')),
                    href=reverse("register_team", args=(subsidiary.id,)) if subsidiary else "",
                    data_fm_head=_("Vytvořit nový tým"),
                    data_fm_callback="createTeamCallback",
                    css_class="btn-success fm-create",
                    id="fm-create-team",
                    **({'disabled': True} if subsidiary is None else {}),  # Disable button if no subsidiary is selected
                ),
            ),
        )

        if not self.instance.campaign.competitors_choose_team():  # We ask only for comapny and subsidiary
            self.fields["team"].widget = HiddenInput()
            self.fields["team"].required = False
            del self.helper.layout.fields[2]

    class Meta:
        model = models.UserAttendance
        fields = ('company', 'subsidiary', 'team')


class RegistrationAccessFormDPNK(SubmitMixin, forms.Form):
    email = forms.CharField(
        required=True,
        label=_(u"E-mail (uživatelské jméno)"),
        help_text=_(u"Zadejte váš e-mail. Pokud jste se účastnili v minulém roce, zadejte stejný e-mail jako v minulém roce."),
    )


class EmailUsernameMixin():
    def clean_username(self):
        "This function is required to overwrite an inherited username clean"
        return self.cleaned_data['username']

    def clean(self):
        cleaned_data = super().clean()
        if not self.errors:
            cleaned_data['username'] = '%s%s' % (cleaned_data['email'].split('@', 1)[0], User.objects.count())
        return cleaned_data


class RegistrationFormDPNK(EmailUsernameMixin, registration.forms.RegistrationFormUniqueEmail):
    required_css_class = 'required'

    username = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, request=None, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _(u'Odeslat')))
        self.helper.layout = Layout(
            'email', 'password1', 'password2', 'username',
            HTML(
                _(
                    'Chcete se stát firemním koordinátorem a nechcete soutěžit?'
                    ' <a href="%(company_admin_registration)s">Využijte registraci firemního koordinátora</a>.'
                    '<br/><br/>'
                ) % {
                    'company_admin_registration': reverse("register_admin"),
                },
            ),
        )

        super(RegistrationFormDPNK, self).__init__(*args, **kwargs)

        self.fields['email'].help_text = _("Tento e-mail bude použit pro zasílání informací v průběhu kampaně a k zaslání zapomenutého hesla.")

    def clean_email(self):
        if User.objects.filter(email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError(
                mark_safe(
                    _(
                        "Tato e-mailová adresa se již používá. "
                        "Pokud je vaše, buď se rovnou <a href='%(login)s'>přihlašte</a>, "
                        "nebo použijte <a href='%(password)s'> obnovu hesla</a>."
                    ) % {
                        'password': reverse('password_reset'),
                        'login': reverse('login'),
                    },
                ),
            )
        return self.cleaned_data['email']

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', 'username')


class InviteForm(SubmitMixin, forms.Form):
    required_css_class = 'required'
    error_css_class = 'error'

    email1 = forms.EmailField(
        label=_(u"E-mail kolegy 1"),
        required=False,
    )

    email2 = forms.EmailField(
        label=_(u"E-mail kolegy 2"),
        required=False,
    )

    email3 = forms.EmailField(
        label=_(u"E-mail kolegy 3"),
        required=False,
    )

    email4 = forms.EmailField(
        label=_(u"E-mail kolegy 4"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "dirty-check"
        self.helper.layout = Layout(
            HTML(
                format_html_lazy(
                    _(
                        "Můžete pozvat kolegy do týmu přes náš rozesílač - stačí napsat níže e-maily "
                        "kolegů, které chcete do svého týmu (samozřejmě je můžete pozvat jakkoliv, "
                        "třeba osobně).<br/>"
                        "Následně vyčkejte, až se k vám někdo do týmu připojí "
                        "(tato informace vám přijde e-mailem, stav vašeho týmu můžete sledovat na <a "
                        "href=\"{}\">stránce vašeho týmu</a>, tamtéž můžete i potvrdit členství "
                        "vašich kolegů).<br/>"
                        "Tým může mít maximálně 5 členů."
                        "<br/><br/>"
                    ),
                    reverse("team_members"),
                ),
            ),
            'email1',
            'email2',
            'email3',
            'email4',
        )
        self.helper.add_input(Submit('submit', _('Odeslat pozvánky')))
        self.helper.add_input(
            Button('submit', _('Neposílat, přeskočit'), css_class="btn-default", onclick='window.location.href="{}"'.format(reverse("zmenit_triko"))),
        )
        return ret_val


class TeamAdminForm(SubmitMixin, forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'
    campaign = forms.ModelChoiceField(
        label=_(u"Kampaň"),
        queryset=models.Campaign.objects.all(),
        widget=HiddenInput(),
    )

    class Meta:
        model = models.Team
        fields = ('name', 'campaign')


class PaymentTypeForm(PrevNextMixin, forms.Form):
    no_dirty = True
    payment_type = forms.ChoiceField(
        label=_(u"Typ platby"),
        widget=forms.RadioSelect(),
    )

    def clean_payment_type(self):
        payment_type = self.cleaned_data['payment_type']
        if payment_type == 'company' and not self.user_attendance.get_asociated_company_admin().exists():
            raise forms.ValidationError(
                format_html(
                    _("Váš zaměstnavatel {employer} nemá zvoleného firemního koordinátora."
                      "Vaše organizace bude muset nejprve ustanovit zástupce, který za ní bude schvalovat platby ve vaší organizaci."
                      "<ul><li><a href='{url}'>Chci se stát firemním koordinátorem</a></li></ul>"),
                    employer=self.user_attendance.team.subsidiary.company,
                    url=reverse('company_admin_application'),
                ),
            )
        return payment_type

    def __init__(self, *args, **kwargs):
        self.user_attendance = kwargs.pop('user_attendance')
        ret_val = super().__init__(*args, **kwargs)
        self.fields['payment_type'].choices = [
            ('pay', _("Zaplatím běžný účastnický poplatek %s Kč.") % intcomma(self.user_attendance.admission_fee())),
            ('pay_beneficiary', mark_safe_lazy(
                _("Podpořím soutěž benefičním poplatkem %s Kč. <i class='fa fa-heart'></i>") %
                intcomma(self.user_attendance.beneficiary_admission_fee()),
            )),
            ('company', _("Učastnický poplatek mi platí zaměstnavatel.")),
            ('member_wannabe', mark_safe_lazy(
                _(
                    "Chci účastnický poplatek zdarma (pro ty, kteří chtějí trvale podporovat udržitelnou mobilitu). "
                    "<i class='fa fa-heart'></i>",
                ),
            )),
            ('coupon', _("Chci uplatnit voucher (sleva či účastnický poplatek zdarma, např. pro Klub přátel).")),
        ]
        return ret_val


class AnswerForm(forms.ModelForm):
    choices = ShowPointsMultipleModelChoiceField(queryset=models.Choice.objects.none(), label="", help_text="")

    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question')
        show_points = kwargs.pop('show_points')
        is_actual = kwargs.pop('is_actual')
        ret_val = super(AnswerForm, self).__init__(*args, **kwargs)
        if question.comment_type:
            if question.comment_type == 'link':
                self.fields['comment'] = forms.URLField(
                    help_text=_("Adresa URL včetně úvodního http:// nebo https://"),
                )
            if question.comment_type == 'one-liner':
                self.fields['comment'] = forms.CharField()
            self.fields['comment'].label = ""
            if question.question_type == 'text':
                self.fields['comment'].required = question.required
        else:
            del self.fields['comment']

        choices_layout = Field('choices')
        if question.question_type != 'text':
            if question.question_type == 'choice':
                choices_layout = Field('choices', template="widgets/radioselectmultiple.html")
            self.fields['choices'].widget = forms.CheckboxSelectMultiple()
            if question.choice_type:
                self.fields['choices'].queryset = question.choice_type.choice_set.all()
            else:
                self.fields['choices'].queryset = models.Choice.objects.none()
            self.fields['choices'].show_points = show_points
            self.fields['choices'].required = question.required
            self.fields['choices'].help_text = ""
        else:
            del self.fields['choices']

        if not question.with_attachment:
            del self.fields['attachment']

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                choices_layout if question.question_type != 'text' else None,
                'comment' if question.comment_type else None,
                'attachment' if question.with_attachment else None,
                css_class=None if is_actual else 'readonly',
            ),
        )
        self.helper.form_tag = False
        return ret_val

    class Meta:
        model = models.Answer
        fields = ('choices', 'comment', 'attachment')


class ConfirmTeamInvitationForm(InitialFieldsMixin, SubmitMixin, forms.ModelForm):
    initial_fields = ('team', 'campaign')
    question = forms.BooleanField(
        label=_(u"Chci být zařazen do nového týmu"),
    )

    class Meta:
        model = models.UserAttendance
        fields = ('team', 'question', 'campaign')


class BikeRepairForm(SubmitMixin, forms.ModelForm):
    user_attendance = forms.CharField(
        label=_(u"Uživatelské jméno zákazníka"),
        help_text=_(u"Uživatelské jméno, které vám sdělí zákazník"),
        max_length=100,
    )
    description = forms.CharField(
        label=_(u"Poznámka"),
        max_length=500,
        required=False,
    )

    def clean_user_attendance(self):
        campaign = self.initial['campaign']
        user_attendance = self.cleaned_data.get('user_attendance')
        try:
            user_attendance = models.UserAttendance.objects.get(
                Q(userprofile__user__username=user_attendance) | Q(userprofile__user__email=user_attendance),
                campaign=campaign,
            )
        except models.UserAttendance.DoesNotExist:
            raise forms.ValidationError(_(u"Takový uživatel neexistuje"))

        other_user_attendances = user_attendance.other_user_attendances(campaign)
        if other_user_attendances.count() > 0:
            raise forms.ValidationError(
                _(u"Tento uživatel není nováček, soutěžil již v předcházejících kampaních: %s") %
                ", ".join([u.campaign.name for u in other_user_attendances]),
            )

        return user_attendance

    def clean(self):
        try:
            transaction = models.CommonTransaction.objects.get(
                user_attendance=self.cleaned_data.get('user_attendance'),
                status=models.Status.BIKE_REPAIR,
            )
        except models.CommonTransaction.DoesNotExist:
            transaction = None
        if transaction:
            created_formated_date = formats.date_format(transaction.created, "SHORT_DATETIME_FORMAT")
            raise forms.ValidationError(
                _(u"Tento uživatel byl již %(time)s v cykloservisu %(bike_shop)s (poznámka: %(note)s).") % {
                    'time': created_formated_date,
                    'bike_shop': transaction.author.get_full_name(),
                    'note': transaction.description,
                },
            )
        return super(BikeRepairForm, self).clean()

    def save(self, *args, **kwargs):
        self.instance.status = models.Status.BIKE_REPAIR
        return super(BikeRepairForm, self).save(*args, **kwargs)

    class Meta:
        model = models.CommonTransaction
        fields = ('user_attendance', 'description')


class TrackUpdateForm(SubmitMixin, forms.ModelForm):
    gpx_file = forms.FileField(
        label=_("GPX soubor"),
        help_text=mark_safe_lazy(
            _(
                "Zadat trasu nahráním souboru GPX. "
                "Pro vytvoření GPX souboru s trasou můžete použít vyhledávání na naší "
                "<a href='http://mapa.prahounakole.cz/#hledani' target='_blank'>mapě</a>."
            ),
        ),
        required=False,
    )

    def clean(self):
        cleaned_data = super(TrackUpdateForm, self).clean()

        if cleaned_data['gpx_file']:
            try:
                gpx_string = cleaned_data['gpx_file'].read().decode("utf-8")
            except UnicodeDecodeError:
                raise ValidationError({'gpx_file': _('Chyba při načítání GPX souboru. Jste si jistí, že jde o GPX soubor?')})
            cleaned_data['track'] = gpx_parse.parse_gpx(gpx_string)

        if cleaned_data['dont_want_insert_track']:
            cleaned_data['track'] = None
        else:
            if cleaned_data['track'] is None:
                raise forms.ValidationError({'track': _("Nezadali jste žádnou trasu. Zadejte trasu, nebo zaškrtněte, že trasu nechcete zadávat.")})
        return cleaned_data

    class Meta:
        model = models.UserAttendance
        fields = ('track', 'gpx_file', 'dont_want_insert_track', 'distance')

    def __init__(self, *args, **kwargs):
        instance = kwargs['instance']
        super(TrackUpdateForm, self).__init__(*args, **kwargs)

        self.fields['track'].widget = UserLeafletWidget(user_attendance=instance)


class ProfileUpdateForm(PrevNextMixin, forms.ModelForm):
    no_prev = True

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

    email = forms.EmailField(
        label=_("E-mail"),
        help_text=_(u"E-mail slouží jako přihlašovací jméno"),
        required=True,
    )
    dont_show_name = forms.BooleanField(
        label=_(u"Nechci, aby moje skutečné jméno bylo veřejně zobrazováno"),
        required=False,
    )
    personal_data_opt_in = forms.BooleanField(
        required=True,
    )
    mailing_opt_in = forms.ChoiceField(
        label=_(u"Soutěžní e-maily"),
        help_text=_(u"Odběr e-mailů můžete kdykoliv v průběhu soutěže zrušit."),
        choices=[
            (True, _("Přeji si dostávat e-mailem informace o akcích, událostech a dalších záležitostech souvisejících se soutěží.")),
            (False, _("Nechci dostávat e-maily (a beru na vědomí, že mi mohou uniknout důležité informace o průběhu soutěže).")),
        ],
        widget=forms.RadioSelect(),
    )
    telephone = forms.CharField(
        label=_(u"Telefon"),
        validators=[RegexValidator(r'^[0-9+ ]*$', _(u'Telefon musí být složen s čísel, mezer a znaku plus.')), MinLengthValidator(9)],
        help_text=_("Telefonní číslo slouží jako kontakt pro help desk a pro kurýra, který vám přiveze soutěžní triko."),
        max_length=30,
    )

    def save(self, *args, **kwargs):
        ret_val = super(ProfileUpdateForm, self).save(*args, **kwargs)
        self.instance.user.email = self.cleaned_data.get('email')
        self.instance.user.first_name = self.cleaned_data.get('first_name')
        self.instance.user.last_name = self.cleaned_data.get('last_name')
        self.instance.user.save()
        return ret_val

    def clean_nickname(self):
        nickname = self.cleaned_data['nickname']
        if self.cleaned_data['dont_show_name']:
            if nickname:
                return nickname
            else:
                raise forms.ValidationError(_(u"Pokud si nepřejete zobrazovat své jméno, zadejte, co se má zobrazovat místo něj"))
        else:
            return None

    def clean_email(self):
        """
        Validate that the email is not already in use.
        """
        if User.objects.filter(email__iexact=self.cleaned_data['email']).exclude(pk=self.instance.user.pk).exists():
            raise forms.ValidationError(_(u"Tento e-mail již je v našem systému zanesen."))
        else:
            return self.cleaned_data['email']

    def clean_sex(self):
        if self.cleaned_data['sex'] == 'unknown':
            raise forms.ValidationError(_(u"Zadejte pohlaví"))
        else:
            return self.cleaned_data['sex']

    def __init__(self, *args, **kwargs):
        campaign = kwargs.pop('campaign')
        ret_val = super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.fields['email'].initial = self.instance.user.email
        self.fields['first_name'].initial = self.instance.user.first_name
        self.fields['last_name'].initial = self.instance.user.last_name
        self.fields['dont_show_name'].initial = self.instance.nickname is not None
        self.fields['mailing_opt_in'].initial = None
        self.fields['personal_data_opt_in'].label = _(
            "Souhlasím se zpracováním osobních údajů podle "
            "<a target='_blank' href='http://www.auto-mat.cz/zasady'>Zásad o ochraně a zpracování údajů Auto*Mat z.s.</a> "
            "a s <a target='_blank' href='http://www.dopracenakole.cz/obchodni-podminky'>Obchodními podmínkami soutěže %s</a>.",
        ) % campaign
        return ret_val

    class Meta:
        model = models.UserProfile
        fields = (
            'sex',
            'first_name',
            'last_name',
            'dont_show_name',
            'nickname',
            'occupation',
            'age_group',
            'mailing_opt_in',
            'email',
            'language',
            'telephone',
            'personal_data_opt_in',
        )


class TripForm(forms.ModelForm):
    distance = CommaFloatField(
        label=_("Vzdálenost (km)"),
        required=False,
    )

    def working_day(self):
        return util.working_day(self.initial['date'])

    def get_direction(self):
        return self.initial['direction'] or self.instance.direction

    def get_date(self):
        return self.initial['date'] or self.instance.date

    def clean_user_attendance(self):
        return self.instance.user_attendance or self.initial['user_attendance']

    def clean_direction(self):
        return self.initial['direction']

    def clean_date(self):
        return self.initial['date']

    def clean(self):
        cleaned_data = super().clean()

        if 'commute_mode' in cleaned_data:
            commute_mode_slug = cleaned_data['commute_mode'].slug
            if commute_mode_slug in ('bicycle', 'by_foot') and not cleaned_data.get('distance', False):
                raise forms.ValidationError(_("Musíte vyplnit vzdálenost"))

            if commute_mode_slug == 'by_foot' and cleaned_data['distance'] < 1.5:
                raise forms.ValidationError(_("Pěší cesta musí mít minimálně jeden a půl kilometru"))

        return cleaned_data

    def has_changed(self, *args, **kwargs):
        return True

    class Meta:
        model = models.Trip
        fields = ('commute_mode', 'distance', 'direction', 'user_attendance', 'date')
        widgets = {
            'user_attendance': forms.HiddenInput(),
            'direction': HiddenInput(),
            'date': HiddenInput(),
            'commute_mode': CommuteModeSelect(),
        }


class GpxFileForm(forms.ModelForm):
    def clean_user_attendance(self):
        return self.initial['user_attendance']

    def clean_trip_date(self):
        return self.initial['trip_date']

    def clean_direction(self):
        return self.initial['direction']

    def clean_track(self):
        if not self.day_active:
            return getattr(self.initial, 'track', None)
        return self.cleaned_data['track']

    def clean_file(self):
        if not self.day_active:
            return getattr(self.initial, 'file', None)
        return self.cleaned_data['file']

    def __init__(self, *args, **kwargs):
        super(GpxFileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.user_attendance = self.initial['user_attendance']
        try:
            self.trip_date = self.instance.trip_date or datetime.datetime.strptime(self.initial['trip_date'], "%Y-%m-%d").date()
            if util.day_active(self.trip_date, self.user_attendance.campaign):
                self.helper.add_input(Submit('submit', _(u'Odeslat')))
                self.day_active = True
            else:
                self.day_active = False
        except ValueError:
            raise Http404

        self.fields['track'].widget = UserLeafletWidget(user_attendance=self.user_attendance)
        self.fields['track'].widget.attrs['geom_type'] = 'MULTILINESTRING'

        self.fields['trip_date'].required = False
        self.fields['direction'].required = False

    class Meta:
        model = models.GpxFile
        fields = ('trip_date', 'direction', 'user_attendance', 'track', 'file')
        widgets = {
            'user_attendance': HiddenInput(),
            'trip_date': forms.TextInput(attrs={'readonly': 'readonly', 'disabled': 'disabled'}),
            'direction': forms.Select(attrs={'readonly': 'readonly', 'disabled': 'disabled'}),
        }
