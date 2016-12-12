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

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, HTML, Layout, Submit

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import MinLengthValidator, RegexValidator
from django.db.models import Q
from django.forms.widgets import HiddenInput
from django.http import Http404
from django.utils import formats
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from django_gpxpy import gpx_parse

from dpnk.fields import CommaFloatField, ShowPointsMultipleModelChoiceField
from dpnk.widgets import CommuteModeSelect, SelectChainedOrCreate, SelectOrCreateAutoComplete

from leaflet.forms.widgets import LeafletWidget

import registration.forms

from smart_selects.form_fields import ChainedModelChoiceField

from . import models, util
from .string_lazy import format_html_lazy, mark_safe_lazy
logger = logging.getLogger(__name__)


def team_full(team):
    if team.campaign.too_much_members(
            models.UserAttendance.objects.
            filter(Q(approved_for_team='approved') | Q(approved_for_team='undecided'), team=team, userprofile__user__is_active=True).
            count(),):
        raise forms.ValidationError(_(u"Tento tým již má plný počet členů"))


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
            self.helper.add_input(Submit('prev', _(u'Předchozí'), css_class="form-actions"))
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
                _(
                    """<a href="%(password_reset_address)s">Zapomněli jste své přihlašovací údaje?</a>
                    <br/><br/>
                    Ještě nemáte účet? <a href="%(registration_address)s">Registrujte se</a> do soutěže %(campaign)s.<br/><br/>
                    """ % {
                        'password_reset_address': reverse("password_reset"),
                        'registration_address': reverse("registration_access"),
                        'campaign': campaign,
                    },
                ),
            ),
        )
        self.helper.add_input(Submit('submit', _(u'Přihlásit')))
        self.fields['username'].label = _(u"Email (uživatelské jméno)")
        return ret_val


class RegisterCompanyForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    class Meta:
        model = models.Company
        fields = ('name', )


class AdressForm(forms.ModelForm):
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
        super(AdressForm, self).__init__(*args, **kwargs)
        if campaign:
            self.fields['city'].queryset = models.City.objects.filter(cityincampaign__campaign=campaign)

    class Meta:
        model = models.Subsidiary
        fields = ('city', 'address_recipient', 'address_street', 'address_street_number', 'address_psc', 'address_city')


class RegisterSubsidiaryForm(AdressForm):
    pass


class RegisterTeamForm(forms.ModelForm):
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


class ChangeTeamForm(PrevNextMixin, forms.ModelForm):
    company = forms.ModelChoiceField(
        label=_(u"Organizace"),
        queryset=models.Company.objects.filter(active=True),
        widget=SelectOrCreateAutoComplete(
            'companies',
            RegisterCompanyForm,
            prefix="company",
            new_description=_(u"Organizace v seznamu není, chci vyplnit novou"),
        ),
        required=True,
    )
    subsidiary = ChainedModelChoiceField(
        chained_field="company",
        to_app_name="dpnk",
        to_model_name="Subsidiary",
        chained_model_field="company",
        show_all=False,
        auto_choose=True,
        label=_(u"Adresa pobočky/organizace"),
        foreign_key_app_name="dpnk",
        foreign_key_model_name="Subsidiary",
        foreign_key_field_name="company",
        widget=SelectChainedOrCreate(
            RegisterSubsidiaryForm,
            view_name='',
            prefix="subsidiary",
            new_description=_(u"Adresa pobočky/organizace v seznamu není, chci vyplnit novou"),
            chained_field="company",
            chained_model_field="company",
            to_app_name="dpnk",
            foreign_key_app_name="dpnk",
            foreign_key_model_name="Subsidiary",
            foreign_key_field_name="company",
            to_model_name="Subsidiary",
            to_model_field="company",
            manager="active_objects",
            show_all=False,
            auto_choose=True,
        ),
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
        widget=SelectChainedOrCreate(
            RegisterTeamForm,
            view_name='',
            prefix="team",
            new_description=_(u"Můj tým v seznamu není, vytvořit nový"),
            chained_field="subsidiary",
            chained_model_field="subsidiary",
            to_app_name="dpnk",
            foreign_key_app_name="dpnk",
            foreign_key_model_name="Subsidiary",
            foreign_key_field_name="company",
            to_model_name="Team",
            to_model_field="subsidiary",
            show_all=False,
            auto_choose=False,
        ),
        label=_(u"Tým"),
        queryset=models.Team.objects.all(),
        required=True,
    )

    def clean(self):
        cleaned_data = super(ChangeTeamForm, self).clean()
        if self.instance.payment_status == 'done' and self.instance.team:
            if 'team' in cleaned_data and cleaned_data['team'].subsidiary != self.instance.team.subsidiary:
                raise forms.ValidationError(_(u"Po zaplacení není možné měnit tým mimo pobočku"))

        if 'subsidiary' in cleaned_data:
            subsidiary = cleaned_data['subsidiary']
            if subsidiary and not models.CityInCampaign.objects.filter(city=subsidiary.city, campaign__slug=self.request.subdomain).exists():
                logger.error("Pobočka ve špatém městě", extra={'request': self.request, 'subsidiary': subsidiary})
                raise forms.ValidationError(
                    _(
                        "Zvolená pobočka je registrována ve městě, které v aktuální kampani nesoutěží. "
                        "Prosím žádejte změnu po vašem vnitrofiremním koordinátorovi."
                    ),
                )
        return cleaned_data

    def clean_team(self):
        data = self.cleaned_data['team']
        if not data:
            return self.instance.team
        else:
            if data.campaign.slug != self.request.subdomain:
                logger.error("Team %s not in campaign %s" % (data.pk, self.request.subdomain), extra={'request': self.request})
                raise forms.ValidationError(_(u"Zvolený tým není dostupný v aktuální kampani"))
        if type(data) != RegisterTeamForm:
            if data != self.instance.team:
                team_full(data)
        return data

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        initial = kwargs.get('initial', {})
        instance = kwargs.get('instance', False)

        if instance:
            previous_user_attendance = instance.previous_user_attendance()
            if previous_user_attendance and previous_user_attendance.team:
                initial['subsidiary'] = previous_user_attendance.team.subsidiary
                initial['company'] = previous_user_attendance.team.subsidiary.company.pk

            if instance.team:
                initial['team'] = instance.team
                initial['subsidiary'] = instance.team.subsidiary
                initial['company'] = instance.team.subsidiary.company.pk

        if request and 'team' in request.GET:
                initial['team'] = request.GET['team']

        kwargs['initial'] = initial

        super(ChangeTeamForm, self).__init__(*args, **kwargs)

        if request:
            self.fields["team"].widget.manager = 'team_in_campaign_%s' % request.subdomain

        if instance and 'team' not in initial:
            previous_user_attendance = instance.previous_user_attendance()
            if previous_user_attendance:
                self.fields["team"].widget.create = True

        if self.instance.payment_status == 'done' and self.instance.team:
            self.fields["subsidiary"].widget = HiddenInput()
            self.fields["company"].widget = HiddenInput()
            self.fields["team"].queryset = models.Team.objects.filter(subsidiary__company=self.instance.team.subsidiary.company)

    class Meta:
        model = models.UserAttendance
        fields = ('company', 'subsidiary', 'team')


class RegistrationAccessFormDPNK(SubmitMixin, forms.Form):
    email = forms.CharField(
        required=True,
        label=_(u"E-mail (uživatelské jméno)"),
        help_text=_(u"Zadejte váš email. Pokud jste se účastnili v minulém roce, zadejte stejný email jako v minulém roce."),
    )


class RegistrationFormDPNK(registration.forms.RegistrationFormUniqueEmail):
    required_css_class = 'required'

    username = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_username(self):
        "This function is required to overwrite an inherited username clean"
        return self.cleaned_data['username']

    def clean(self):
        if not self.errors:
            self.cleaned_data['username'] = '%s%s' % (self.cleaned_data['email'].split('@', 1)[0], User.objects.count())
        super(RegistrationFormDPNK, self).clean()
        return self.cleaned_data

    def __init__(self, request=None, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _(u'Odeslat')))

        super(RegistrationFormDPNK, self).__init__(*args, **kwargs)

        self.fields['email'].help_text = _(u"Pro informace v průběhu kampaně, k zaslání zapomenutého loginu")

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
        label=_(u"Email kolegy 1"),
        required=False,
    )

    email2 = forms.EmailField(
        label=_(u"Email kolegy 2"),
        required=False,
    )

    email3 = forms.EmailField(
        label=_(u"Email kolegy 3"),
        required=False,
    )

    email4 = forms.EmailField(
        label=_(u"Email kolegy 4"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML(
                format_html_lazy(
                    _(
                        """Napište zde emaily kolegů, které chcete pozvat do svého týmu. Následně vyčkejte, """
                        """až se k vám někdo do týmu připojí (tato informace vám přijde emailem, """
                        """stav vašeho týmu můžete sledovat na <a href="{}">stránce týmu</a> a potvrdit členství vašich kolegů)."""
                        """<br/><br/>"""
                    ),
                    reverse("team_members"),
                ),
            ),
            'email1',
            'email2',
            'email3',
            'email4',
        )
        self.helper.add_input(Submit('submit', _(u'Odeslat')))
        self.helper.add_input(Submit('submit', _(u'Přeskočit')))
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


def small(string):
    return format_html_lazy("<small>{}</small>", string)


class PaymentTypeForm(PrevNextMixin, forms.Form):
    CHOICES = [
        ('pay', _(u"Účastnický poplatek si platím sám.")),
        ('pay_beneficiary', mark_safe_lazy(_(u"Chci podpořit tuto soutěž a zaplatit benefiční startovné. <i class='fa fa-heart'></i>"))),
        ('company', _(u"Účastnický poplatek za mě zaplatí zaměstnavatel, mám to domluvené.")),
        ('member_wannabe', mark_safe_lazy(_(u"Chci podpořit městskou cyklistiku a mít startovné trvale zdarma. <i class='fa fa-heart'></i>"))),
        ('coupon', _("Chci uplatnit voucher.")),
    ]

    payment_type = forms.ChoiceField(
        label=_(u"Typ platby"),
        choices=CHOICES,
        widget=forms.RadioSelect(),
    )

    def clean_payment_type(self):
        payment_type = self.cleaned_data['payment_type']
        if payment_type == 'company' and not self.user_attendance.get_asociated_company_admin().exists():
            raise forms.ValidationError(
                format_html(
                    _("Váš zaměstnavatel {employer} nemá zvoleného koordinátora organizace."
                      " Vaše organizace bude muset nejprve ustanovit zástupce, který za ní bude schvalovat platby ve vaší organizaci."
                      "<ul><li><a href='{url}'>Chci se stát koordinátorem mé organizace</a></li></ul>"),
                    employer=self.user_attendance.team.subsidiary.company,
                    url=reverse('company_admin_application'),
                ),
            )
        return payment_type


class DiscountCouponForm(PrevNextMixin, forms.Form):
    code = forms.CharField(
        label=_("Kód voucheru"),
        max_length=10,
        required=True,
        validators=[RegexValidator(r'^[a-zA-Z]+-[abcdefghjklmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ]+$', _('Nesprávný formát voucheru')), MinLengthValidator(9)],
    )

    def clean(self):
        cleaned_data = super().clean()
        if 'code' in cleaned_data:
            prefix, base_code = cleaned_data['code'].upper().split("-")
            try:
                cleaned_data['discount_coupon'] = models.DiscountCoupon.objects.get(
                    coupon_type__prefix=prefix,
                    token=base_code,
                    user_attendance=None,
                )
            except models.DiscountCoupon.DoesNotExist:
                raise ValidationError(_("Tento slevový kupón neexistuje, nebo již byl použit"))
        return cleaned_data


class AnswerForm(forms.ModelForm):
    choices = ShowPointsMultipleModelChoiceField(queryset=(), label="", help_text="")

    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question')
        show_points = kwargs.pop('show_points')
        is_actual = kwargs.pop('is_actual')
        ret_val = super(AnswerForm, self).__init__(*args, **kwargs)
        if question.comment_type:
            if question.comment_type == 'link':
                self.fields['comment'] = forms.URLField()
            if question.comment_type == 'one-liner':
                self.fields['comment'] = forms.CharField()
            self.fields['comment'].label = ""
            if question.type == 'text':
                self.fields['comment'].required = question.required
        else:
            del self.fields['comment']

        choices_layout = Field('choices')
        if question.type != 'text':
            if question.type == 'choice':
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
                choices_layout if question.type != 'text' else None,
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


class ConfirmTeamInvitationForm(SubmitMixin, forms.Form):
    question = forms.BooleanField(
        label=_(u"Chci být zařazen do nového týmu"),
    )


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
            user_attendance = models.UserAttendance.objects.get(Q(userprofile__user__username=user_attendance) | Q(userprofile__user__email=user_attendance), campaign=campaign)
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
            transaction = models.CommonTransaction.objects.get(user_attendance=self.cleaned_data.get('user_attendance'), status=models.Status.BIKE_REPAIR)
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


class TShirtUpdateForm(PrevNextMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        self.fields['t_shirt_size'].required = True
        self.fields['t_shirt_size'].queryset = models.TShirtSize.objects.filter(campaign=self.instance.campaign, available=True)
        return ret_val

    class Meta:
        model = models.UserAttendance
        fields = ('t_shirt_size', )


class TrackUpdateForm(SubmitMixin, forms.ModelForm):
    gpx_file = forms.FileField(
        label=_("GPX soubor"),
        help_text=mark_safe_lazy(
            _(
                "Zadat trasu nahráním souboru GPX. "
                "Pro vytvoření GPX souboru s trasou můžete použít vyhledávání na naší <a href='http://mapa.prahounakole.cz/#hledani' target='_blank'>mapě</a>."
            ),
        ),
        required=False,
    )

    def clean(self):
        cleaned_data = super(TrackUpdateForm, self).clean()

        if cleaned_data['gpx_file']:
            gpx_string = cleaned_data['gpx_file'].read().decode("utf-8")
            cleaned_data['track'] = gpx_parse.parse_gpx(gpx_string)

        if cleaned_data['dont_want_insert_track']:
            cleaned_data['track'] = None
        else:
            if cleaned_data['track'] is None:
                raise forms.ValidationError(_("Nezadali jste žádnou trasu. Zadejte trasu, nebo zaškrtněte, že trasu nechcete zadávat."))
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
        help_text=_(u"Email slouží jako přihlašovací jméno"),
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
        label=_(u"Soutěžní emaily"),
        help_text=_(u"Odběr emailů můžete kdykoliv v průběhu soutěže zrušit."),
        choices=[
            (True, _("Přeji si dostávat emailem informace o akcích, událostech a dalších informacích souvisejících se soutěží.")),
            (False, _("Nechci dostávat emaily, mohou mi uniknout důležité informace o průběhu soutěže.")),
        ],
        widget=forms.RadioSelect(),
    )
    telephone = forms.CharField(
        label=_(u"Telefon"),
        validators=[RegexValidator(r'^[0-9+ ]*$', _(u'Telefon musí být složen s čísel, mezer a znaku plus.')), MinLengthValidator(9)],
        help_text=_(u"Telefon použije kurýr, který Vám přiveze soutěžní triko, slouží pro HelpDesk a další účely"),
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
            raise forms.ValidationError(_(u"Tento email již je v našem systému zanesen."))
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
            "a s <a target='_blank' href='http://www.dopracenakole.cz/obchodni-podminky'>Obchodními podmínkami soutěže %s</a>." % campaign,
        )
        return ret_val

    class Meta:
        model = models.UserProfile
        fields = ('sex', 'first_name', 'last_name', 'dont_show_name', 'nickname', 'mailing_opt_in', 'email', 'language', 'telephone', 'personal_data_opt_in')


class TripForm(forms.ModelForm):
    commute_mode = forms.ChoiceField(
        label=_("Dopravní prostředek"),
        choices=models.Trip.MODES,
        widget=CommuteModeSelect(),
    )
    distance = CommaFloatField(
        label=_("Vzdálenost"),
        required=False,
    )

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

    def __repr__(self):
        # This is here for debugging reasons
        return "<TripForm initial: %s>" % (self.initial)

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data['commute_mode'] in ('bicycle', 'by_foot') and not cleaned_data['distance']:
            raise forms.ValidationError(_("Musíte vyplnit vzdálenost"))

        if cleaned_data['commute_mode'] == 'by_foot' and cleaned_data['distance'] < 1.5:
            raise forms.ValidationError(_("Pěší cesta musí mít minimálně jeden a půl kilometru"))

        return cleaned_data

    def __init__(self, *args, **kwargs):
        ret = super().__init__(*args, **kwargs)
        return ret

    class Meta:
        model = models.Trip
        fields = ('commute_mode', 'distance', 'direction', 'user_attendance', 'date')
        widgets = {
            'user_attendance': forms.HiddenInput(),
            'direction': HiddenInput(),
            'date': HiddenInput(),
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
