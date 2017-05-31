# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2017 o.s. Auto*Mat
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
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _


IDENTIFIER_REGEXP = r'^[TS][0-9]+$'


class DispatchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        super().__init__(*args, **kwargs)
        self.helper.add_input(Submit('submit', _('Balík/krabice s tímto číslem byl sestaven')))
        self.fields['dispatch_id'].widget.attrs['autofocus'] = True

    dispatch_id = forms.CharField(
        validators=[
            RegexValidator(
                regex=IDENTIFIER_REGEXP,
                message='Číslo balíku/krabice je v nesprávném formátu',
            ),
        ],
    )
