# -*- coding: utf-8 -*-
# Author: Hynek Hanke <hynek.hanke@auto-mat.cz>
#
# Copyright (C) 2012 o.s. Auto*Mat
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


# Django imports
from django import forms, http
from django.shortcuts import render_to_response
# Registration imports
import registration.forms, registration.signals
# Model imports
from models import UserProfile, Team

class RegistrationFormDPNK(registration.forms.RegistrationForm):
    firstname = forms.CharField(
        label="Jméno",
        max_length=30)
    surname = forms.CharField(
        label="Příjmení",
        max_length=30)
    team = forms.ModelChoiceField(
        label="Tým",
        queryset=Team.objects.all())
    team_password = forms.CharField(
        label="Heslo týmu",
        max_length=20)
    sex = forms.ChoiceField(
        label="Pohlaví",
        choices=UserProfile.GENDER)
    language = forms.ChoiceField(
        label="Jazyk",
        choices=UserProfile.LANGUAGE)
    # -- Contacts
    telephone = forms.CharField(
        label="Telefon",
        max_length=30)
    competition_city = forms.ChoiceField(
        label="Soutěžní město",
        choices=UserProfile.COMPETITION_CITY)

    def __init__(self, *args, **kwargs):
        super(RegistrationFormDPNK, self).__init__(*args, **kwargs)
        self.fields.keyOrder = [
            'firstname',
            'surname',
            'team',
            'team_password',
            'sex',
            'competition_city',
            'language',
            'email',
            'telephone',
            'username',
            'password1',
            'password2'
            ]

    def clean_team_password(self):
        data = self.cleaned_data['team_password']
        if data != 'tajemstvi':
            raise forms.ValidationError("Nesprávné heslo týmu")
        return data

def create_profile(user, request, **kwargs):
    from dpnk.models import UserProfile
    UserProfile(user = user,
                team = Team.objects.get(id=request.POST['team']),
                **{c:request.POST[c] for c in ('sex', 'competition_city', 'language', 'telephone',
                                               'firstname', 'surname')}
                ).save()
registration.signals.user_registered.connect(create_profile)

class RegisterTeamForm(forms.ModelForm):

    class Meta:
        model = Team
        fields = ('name', 'company')

def register_team(request):
    if request.method == 'POST':
        form = RegisterTeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.password = 'tajemstvi' # TODO
            form.save()
            return render_to_response('registration/team_password.html', {
                    'team_password': team.password
                    })
    else:
        form = RegisterTeamForm()
    return render_to_response('registration/register_team.html', {
            'form': form,
            })

def payment(request):
    if request.method == 'POST':
        form = RegisterTeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.password = 'tajemstvi' # TODO
            form.save()
            return render_to_response('registration/team_password.html', {
                    'team_password': team.password
                    })
    else:
        form = RegisterTeamForm()
    return render_to_response('registration/register_team.html', {
            'form': form,
            })

