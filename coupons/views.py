# -*- coding: utf-8 -*-
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
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

# Standard library imports


import logging

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView

from dpnk.views import RegistrationViewMixin

from . import forms

logger = logging.getLogger(__name__)


class DiscountCouponView(RegistrationViewMixin, FormView):
    template_name = 'base_generic_registration_form.html'
    form_class = forms.DiscountCouponForm
    success_url = reverse_lazy('typ_platby')
    next_url = 'typ_platby'
    prev_url = 'typ_platby'
    registration_phase = 'typ_platby'
    title = _("Uplatnit slevový voucher")

    def get_success_url(self):
        if self.discount_coupon.discount == 100:
            return reverse_lazy('profil')
        else:
            return self.success_url

    def form_valid(self, form):
        self.discount_coupon = form.cleaned_data['discount_coupon']
        self.user_attendance.discount_coupon = self.discount_coupon
        self.user_attendance.save()
        ret_val = super().form_valid(form)
        return ret_val
