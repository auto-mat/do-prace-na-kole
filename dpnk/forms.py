# -*- coding: utf-8 -*-
from smart_selects.form_fields import ChainedModelChoiceField, GroupedModelSelect
from django.contrib.auth.forms import AuthenticationForm
from django import forms, http
# Registration imports
import registration.forms
from models import UserProfile, Company, Subsidiary, Team
from django.db.models import Q
from dpnk.widgets import SelectOrCreate

def team_full(data):
    if len(UserProfile.objects.filter(Q(approved_for_team='approved') | Q(approved_for_team='undecided'), team=data, active=True)) >= 5:
        raise forms.ValidationError("Tento tým již má pět členů a je tedy plný")

class RegistrationFormDPNK(registration.forms.RegistrationForm):
    required_css_class = 'required'
    
    firstname = forms.CharField(
        label="Jméno",
        max_length=30,
        required=True)
    surname = forms.CharField(
        label="Příjmení",
        max_length=30,
        required=True)
    company = forms.ModelChoiceField(
        label="Firma",
        queryset=Company.objects.all(),
        required=True)
    subsidiary = ChainedModelChoiceField(
        chain_field = "company",
        app_name = "dpnk",
        model_name = "Subsidiary",
        model_field = "company",
        show_all = False,
        auto_choose = True,
        label="Pobočka",
        queryset=Subsidiary.objects.all(),
        required=True)
    team = ChainedModelChoiceField(
        chain_field = "subsidiary",
        app_name = "dpnk",
        model_name = "Team",
        model_field = "subsidiary",
        show_all = False,
        auto_choose = True,
        label="Tým",
        queryset=Team.objects.all(),
        required=True)
    distance = forms.IntegerField(
        label="Vzdálenost z domova do práce vzdušnou čarou (v km)",
        required=True)
    t_shirt_size = forms.ChoiceField(
        label="Velikost trička",
        choices = UserProfile.TSHIRTSIZE,
        initial = "L",
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
            'firstname',
            'surname',
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

class AutoRegistrationFormDPNK(RegistrationFormDPNK):
    pass

class RegisterTeamForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    class Meta:
        model = Team
        fields = ('name',)

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

class InviteForm(forms.Form):
    required_css_class = 'required'
    error_css_class = 'error'

    email1 = forms.EmailField(
        label="Kolega 1",
        required=False)

    email2 = forms.EmailField(
        label="Kolega 2",
        required=False)

    email3 = forms.EmailField(
        label="Kolega 3",
        required=False)

    email4 = forms.EmailField(
        label="Kolega 4",
        required=False)

class TeamAdminForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    class Meta:
        model = Team
        fields = ('name',)

class TeamUserAdminForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    class Meta:
        model = UserProfile
        fields = ('firstname', 'surname', 'approved_for_team',)
        readonly_fields = ('firstname', 'surname',)
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['firstname', 'surname',]
        else:
            return []

class PaymentTypeForm(forms.Form):
    CHOICES=[('pay',u'Účastnický poplatek si platím sám.'),
             ('company',u'Účastnický poplatek za mě zaplatí zaměstnavatel, mám to domluvené.'),
             ('member',u'Jsem členem klubu přátel Auto*mat nebo se jím hodlám stát.')
             ]

    payment_type = forms.ChoiceField(
            label='Typ platby',
            choices=CHOICES,
            widget=forms.RadioSelect(),
            )


class ProfileUpdateForm(forms.ModelForm):
    team = forms.ModelChoiceField(
        label="Tým",
        queryset= [],
        widget=SelectOrCreate(RegisterTeamForm, new_description = u"Chci si založit nový tým, ve kterém budu koordinátorem"),
        empty_label=None,
        required=True)

    def clean_team(self):
        data = self.cleaned_data['team']
        if type(data) != RegisterTeamForm:
            if data != self.instance.team:
                team_full(data)
        return data

    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        userprofile = kwargs['instance']
        self.fields["team"].queryset = Team.objects.filter(subsidiary__company=userprofile.team.subsidiary.company)

    class Meta:
        model = UserProfile
        fields = ('firstname', 'surname', 'telephone', 't_shirt_size', 'team')
