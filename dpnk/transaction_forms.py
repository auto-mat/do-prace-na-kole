# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2016 o.s. Auto*Mat
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

from . import models


class PaymentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'] = forms.ChoiceField(choices=models.STATUS)

    class Meta:
        model = models.Payment
        fields = "__all__"


class PackageTransactionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'] = forms.ChoiceField(choices=models.STATUS)

    class Meta:
        model = models.PackageTransaction
        fields = "__all__"


class CommonTransactionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'] = forms.ChoiceField(choices=models.CommonTransaction.STATUS)

    class Meta:
        model = models.CommonTransaction
        fields = "__all__"


class UserActionTransactionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'] = forms.ChoiceField(choices=models.STATUS)

    class Meta:
        model = models.UserActionTransaction
        fields = "__all__"
