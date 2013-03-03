# -*- coding: utf-8 -*-
from smart_selects.form_fields import ChainedModelChoiceField, GroupedModelSelect
from django.contrib.auth.forms import AuthenticationForm
from django import forms, http
# Registration imports
import registration.forms
from models import UserProfile, Company, Subsidiary, Team

class ProfileUpdateForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ('firstname', 'surname', 'telephone')
    

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
        queryset=Team.objects.all(),
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
        if len(UserProfile.objects.filter(team=data, active=True)) >= 5:
            raise forms.ValidationError("Tento tým již má pět členů a je tedy plný")
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
    #required_css_class = 'required'
    error_css_class = 'error'

    class Meta:
        model = Company
        fields = ('name', )
    
class RegisterSubsidiaryForm(forms.ModelForm):
    #required_css_class = 'required'
    error_css_class = 'error'

    class Meta:
        model = Subsidiary
        fields = ('street', 'street_number', 'recipient', 'district', 'PSC', 'city')
