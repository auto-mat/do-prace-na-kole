# -*- coding: utf-8 -*-
from smart_selects.form_fields import ChainedModelChoiceField, GroupedModelSelect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django import forms, http
# Registration imports
import registration.forms
import models
from models import UserProfile, Company, Subsidiary, Team, UserAttendance
from django.db.models import Q
from dpnk.widgets import SelectOrCreate, SelectChainedOrCreate
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError

def team_full(data):
    if len(UserAttendance.objects.filter(Q(approved_for_team='approved') | Q(approved_for_team='undecided'), team=data, userprofile__user__is_active=True)) >= 5:
        raise forms.ValidationError(_(u"Tento tým již má pět členů a je tedy plný"))

class RegisterCompanyForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    class Meta:
        model = Company
        fields = ('name', )
    
class AdressForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    address_psc = forms.CharField(
        label =_(u"PSČ"),
        help_text=_(u"Např.: 130 00"),
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

    class Meta:
        model = Subsidiary
        fields = ('city', 'address_recipient', 'address_street', 'address_street_number', 'address_psc', 'address_city')

class RegisterSubsidiaryForm(AdressForm):
    pass

class RegisterTeamForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    class Meta:
        model = Team
        fields = ('name',)


class ChangeTeamForm(forms.ModelForm):
    company = forms.ModelChoiceField(
        label=_(u"Firma"),
        queryset=Company.objects.all(),
        widget=SelectOrCreate(RegisterCompanyForm, prefix="company", new_description = _(u"Společnost v seznamu není, chci založit novou")),
        required=True)
    subsidiary = ChainedModelChoiceField(
        chain_field = "company",
        app_name = "dpnk",
        model_name = "Subsidiary",
        model_field = "company",
        show_all = False,
        auto_choose = True,
        label="Pobočka",
        widget=SelectChainedOrCreate(RegisterSubsidiaryForm, prefix="subsidiary", new_description = _(u"Pobočka v seznamu není, chci založit novou"), 
            chain_field = "company",
            app_name = "dpnk",
            model_name = "Subsidiary",
            model_field = "company",
            show_all = False,
            auto_choose = True,
        ),
        queryset=Subsidiary.objects.all(),
        required=True)
    team = ChainedModelChoiceField(
        chain_field = "subsidiary",
        app_name = "dpnk",
        model_name = "Team",
        model_field = "subsidiary",
        show_all = False,
        auto_choose = False,
        widget=SelectChainedOrCreate(RegisterTeamForm, prefix="team", new_description = _(u"Tým v seznamu není, chci si založit nový"),
            chain_field = "subsidiary",
            app_name = "dpnk",
            model_name = "Team",
            model_field = "subsidiary",
            show_all = False,
            auto_choose = False,
        ),
        label="Tým",
        queryset=Team.objects.all(),
        required=True)

    def clean_team(self):
        data = self.cleaned_data['team']
        if not data:
            return self.instance.team
        if type(data) != RegisterTeamForm:
            if data != self.instance.team:
                team_full(data)
        return data

    def __init__(self, request=None, *args, **kwargs):
        initial = kwargs.get('initial', {})
        instance = kwargs.get('instance', {})
        if instance:
            initial['team'] = instance.team
            initial['subsidiary'] = instance.team.subsidiary
            initial['company'] = instance.team.subsidiary.company

        if request:
            if request.GET.get('team', None):
                initial['team'] = request.GET['team']

        kwargs['initial']=initial

        super(ChangeTeamForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = [
            'company',
            'subsidiary',
            'team',
            ]

        #if user_attendance.team:
        #    self.fields["team"].queryset = Team.objects.filter(subsidiary__company=user_attendance.team.subsidiary.company)

        #if not user_attendance.team or (models.is_team_coordinator(user_attendance) and UserAttendance.objects.filter(team=user_attendance.team, userprofile__user__is_active=True).count()>1):
        #    del self.fields['team']
        #    self.can_change_team = False

    class Meta:
        model = UserAttendance
        fields = ('team',)


class RegistrationFormDPNK(registration.forms.RegistrationFormUniqueEmail):
    required_css_class = 'required'
    
    language = forms.ChoiceField(
        label=_(u"Jazyk komunikace"),
        choices = UserProfile.LANGUAGE,
        )
    first_name = forms.CharField(
        label=_(u"Jméno"),
        max_length=30,
        required=True)
    last_name = forms.CharField(
        label=_(u"Příjmení"),
        max_length=30,
        required=True)


    def __init__(self, request=None, *args, **kwargs):
        if request:
            initial = kwargs.get('initial', {})
            if request.GET.get('team', None):
                initial['team'] = request.GET['team']
            kwargs['initial']=initial

        super(RegistrationFormDPNK, self).__init__(*args, **kwargs)
        self.fields.keyOrder = [
            'language',
            'first_name',
            'last_name',
            'email',
            'username',
            'password1',
            'password2'
            ]

        self.fields['email'].help_text=_(u"Pro informace v průběhu kampaně, k zaslání zapomenutého loginu")

    def clean_team(self):
        data = self.cleaned_data['team']
        team_full(data)
        return data

    class Meta:
        model = UserProfile

class InviteForm(forms.Form):
    required_css_class = 'required'
    error_css_class = 'error'

    email1 = forms.EmailField(
        label=_(u"Email kolegy 1"),
        required=False)

    email2 = forms.EmailField(
        label=_(u"Email kolegy 2"),
        required=False)

    email3 = forms.EmailField(
        label=_(u"Email kolegy 3"),
        required=False)

    email4 = forms.EmailField(
        label=_(u"Email kolegy 4"),
        required=False)

class TeamAdminForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    class Meta:
        model = Team
        fields = ('name',)

class PaymentTypeForm(forms.Form):
    CHOICES=[('pay', _(u"Účastnický poplatek si platím sám.")),
             ('company', _(u"Účastnický poplatek za mě zaplatí zaměstnavatel, mám to domluvené.")),
             ('member', _(u"Jsem členem klubu přátel Auto*mat nebo se jím hodlám stát."))
             ]

    payment_type = forms.ChoiceField(
            label=_(u"Typ platby"),
            choices=CHOICES,
            widget=forms.RadioSelect(),
            )


class TShirtUpdateForm(forms.ModelForm):
    t_shirt_size = forms.ChoiceField(
        choices = UserAttendance.TSHIRTSIZE_USER,
        label=_(u"Velikost trička"),
        )
    telephone = forms.CharField(
        label="Telefon",
        help_text="Pro kurýra, který Vám přiveze soutěžní triko, pro HelpDesk",
        max_length=30)

    def save(self, *args, **kwargs):
        ret_val = super(TShirtUpdateForm, self).save(*args, **kwargs)
        self.instance.userprofile.telephone = self.cleaned_data.get('telephone')
        self.instance.userprofile.save()
        return ret_val

    def __init__(self, *args, **kwargs):
        ret_val = super(TShirtUpdateForm, self).__init__(*args, **kwargs)
        self.fields['telephone'].initial = self.instance.userprofile.telephone
        return ret_val


    class Meta:
        model = UserAttendance
        fields = ('t_shirt_size', 'telephone', )


class ProfileUpdateForm(forms.ModelForm):
    language = forms.ChoiceField(
        label=_(u"Jazyk komunikace"),
        choices = UserProfile.LANGUAGE,
        )
    first_name = forms.CharField(
        label="Jméno",
        max_length=30,
        required=True)
    last_name = forms.CharField(
        label="Příjmení",
        max_length=30,
        required=True)

    email = forms.EmailField(
        help_text=_(u"Pro informace v průběhu kampaně, k zaslání zapomenutého loginu"),
        required=False)

    def save(self, *args, **kwargs):
        ret_val = super(ProfileUpdateForm, self).save(*args, **kwargs)
        self.instance.userprofile.language = self.cleaned_data.get('language')
        self.instance.userprofile.save()
        self.instance.userprofile.user.email = self.cleaned_data.get('email')
        self.instance.userprofile.user.first_name = self.cleaned_data.get('first_name')
        self.instance.userprofile.user.last_name = self.cleaned_data.get('last_name')
        self.instance.userprofile.user.save()
        return ret_val

    def clean_email(self):
        """
        Validate that the email is not already in use.
        """
        if User.objects.filter(email__iexact=self.cleaned_data['email']).exclude(pk=self.instance.userprofile.user.pk).exists():
            raise forms.ValidationError(_("Tento email již je v našem systému zanesen."))
        else:
            return self.cleaned_data['email']

    def __init__(self, *args, **kwargs):
        ret_val = super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        user_attendance = kwargs['instance']
        self.fields['language'].initial = self.instance.userprofile.language
        self.fields['email'].initial = self.instance.userprofile.user.email
        self.fields['first_name'].initial = self.instance.userprofile.user.first_name
        self.fields['last_name'].initial = self.instance.userprofile.user.last_name
        return ret_val

    class Meta:
        model = UserAttendance
        fields = ( 'language', 'first_name', 'last_name', 'email', 'distance')
