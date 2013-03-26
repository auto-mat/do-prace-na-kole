# -*- coding: utf-8 -*-
from smart_selects.form_fields import ChainedModelChoiceField, GroupedModelSelect
from django.contrib.auth.forms import AuthenticationForm
from django import forms, http
# Registration imports
import registration.forms
from models import UserProfile, Company, Subsidiary, Team
from django.db.models import Q
from dpnk.widgets import SelectOrCreate, SelectChainedOrCreate
from django.utils.translation import gettext as _

def team_full(data):
    if len(UserProfile.objects.filter(Q(approved_for_team='approved') | Q(approved_for_team='undecided'), team=data, user__is_active=True)) >= 5:
        raise forms.ValidationError(_("Tento tým již má pět členů a je tedy plný"))

class RegisterCompanyForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    class Meta:
        model = Company
        fields = ('name', )
    
class RegisterSubsidiaryForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    class Meta:
        model = Subsidiary
        fields = ('address_street', 'address_street_number', 'address_recipient', 'address_district', 'address_psc', 'address_city', 'city')


class RegisterTeamForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    class Meta:
        model = Team
        fields = ('name',)

class RegistrationFormDPNK(registration.forms.RegistrationForm):
    required_css_class = 'required'
    
    language = forms.ChoiceField(
        label=_("Jazyk komunikace"),
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
    company = forms.ModelChoiceField(
        label="Firma",
        queryset=Company.objects.all(),
        widget=SelectOrCreate(RegisterCompanyForm, prefix="company", new_description = _("Společnost v seznamu není, chci založit novou")),
        required=True)
    subsidiary = ChainedModelChoiceField(
        chain_field = "company",
        app_name = "dpnk",
        model_name = "Subsidiary",
        model_field = "company",
        show_all = False,
        auto_choose = True,
        label="Pobočka",
        widget=SelectChainedOrCreate(RegisterSubsidiaryForm, prefix="subsidiary", new_description = _("Pobočka v seznamu není, chci založit novou"), 
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
        widget=SelectChainedOrCreate(RegisterTeamForm, prefix="team", new_description = _("Tým v seznamu není, chci si založit nový"),
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
    distance = forms.IntegerField(
        label=_("Průměrná ujetá vzdálenost z domova do práce (v km)"),
        required=True)
    t_shirt_size = forms.ChoiceField(
        label=_("Velikost trička"),
        choices = [['','-----'],] + UserProfile.TSHIRTSIZE,
        help_text=_('Velikost trička můžete vybírat z <a href="http://www.stanleystella.com/#collection">katalogu</a>'),
        )

    # -- Contacts
    telephone = forms.CharField(
        label="Telefon",
        max_length=30)

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
            'company',
            'subsidiary',
            'team',
            'distance',
            't_shirt_size',
            'email',
            'telephone',
            'username',
            'password1',
            'password2'
            ]

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
        label=_("Email kolegy 1"),
        required=False)

    email2 = forms.EmailField(
        label=_("Email kolegy 2"),
        required=False)

    email3 = forms.EmailField(
        label=_("Email kolegy 3"),
        required=False)

    email4 = forms.EmailField(
        label=_("Email kolegy 4"),
        required=False)

class TeamAdminForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    class Meta:
        model = Team
        fields = ('name',)

class PaymentTypeForm(forms.Form):
    CHOICES=[('pay', _("Účastnický poplatek si platím sám.")),
             ('company', _("Účastnický poplatek za mě zaplatí zaměstnavatel, mám to domluvené.")),
             ('member', _("Jsem členem klubu přátel Auto*mat nebo se jím hodlám stát."))
             ]

    payment_type = forms.ChoiceField(
            label=_("Typ platby"),
            choices=CHOICES,
            widget=forms.RadioSelect(),
            )

class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Jméno",
        max_length=30,
        required=True)
    last_name = forms.CharField(
        label="Příjmení",
        max_length=30,
        required=True)
    team = forms.ModelChoiceField(
        label="Tým",
        queryset= [],
        widget=SelectOrCreate(RegisterTeamForm, prefix="team", new_description = _("Chci si založit nový tým, ve kterém budu koordinátorem")),
        empty_label=None,
        required=True)

    email = forms.EmailField(
        required=False)

    def save(self, *args, **kwargs):
        ret_val = super(ProfileUpdateForm, self).save(*args, **kwargs)
        self.instance.user.email = self.cleaned_data.get('email')
        self.instance.user.first_name = self.cleaned_data.get('first_name')
        self.instance.user.last_name = self.cleaned_data.get('last_name')
        self.instance.user.save()
        return ret_val

    def clean_team(self):
        data = self.cleaned_data['team']
        if type(data) != RegisterTeamForm:
            if data != self.instance.team:
                team_full(data)
        return data

    def __init__(self, *args, **kwargs):
        ret_val = super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        userprofile = kwargs['instance']
        self.fields["team"].queryset = Team.objects.filter(subsidiary__company=userprofile.team.subsidiary.company)

        self.fields['email'].initial = self.instance.user.email
        self.fields['first_name'].initial = self.instance.user.first_name
        self.fields['last_name'].initial = self.instance.user.last_name

        if userprofile.team.coordinator == userprofile and UserProfile.objects.filter(team=userprofile.team, user__is_active=True).count()>1:
            del self.fields['team']
        return ret_val

    class Meta:
        model = UserProfile
        fields = ( 'language', 'first_name', 'last_name', 'telephone', 'email', 'team',)
