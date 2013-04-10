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
from models import UserProfile
from django.utils.translation import gettext as _

class SelectUsersPayForm(forms.Form):
    paing_for = forms.ModelMultipleChoiceField(
        [], 
        label=_(u"Soutěžící, za které bude zaplaceno"),
        help_text=_(u"<div class='text-info'>Tip: Použijte ctrl nebo shift pro výběr více položek nebo jejich rozsahu.</div>"),
        widget=forms.SelectMultiple(attrs={'size':'40'}),
    )

    def __init__(self, company, *args, **kwargs):
        ret_val = super(SelectUsersPayForm, self).__init__(*args, **kwargs)
        self.fields['paing_for'].queryset = UserProfile.objects.filter(team__subsidiary__company = company, user__is_active=True)
        choices = [(userprofile.pk, userprofile) for userprofile in UserProfile.objects.filter(team__subsidiary__company = company, user__is_active=True).all() 
            if userprofile.payment_type() == 'fc' and userprofile.payment_status() != 'done']
        self.fields['paing_for'].choices = choices
