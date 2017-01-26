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


from django.contrib.auth.decorators import login_required as login_required_simple
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import UpdateView

from dpnk.decorators import user_attendance_has
from dpnk.models import UserAttendance
from dpnk.views import RegistrationViewMixin

from .forms import TShirtUpdateForm


class ChangeTShirtView(RegistrationViewMixin, UpdateView):
    template_name = 'registration/change_tshirt.html'
    form_class = TShirtUpdateForm
    model = UserAttendance
    success_message = _(u"Velikost trička úspěšně nastavena")
    next_url = 'typ_platby'
    prev_url = 'zmenit_tym'
    registration_phase = "zmenit_triko"
    title = _(u"Upravit velikost trička")

    def get_object(self):
        return self.user_attendance

    @method_decorator(login_required_simple)
    @user_attendance_has(lambda ua: not ua.team_complete(), _(u"Velikost trička nemůžete měnit, dokud nemáte zvolený tým."))
    @user_attendance_has(lambda ua: ua.package_shipped(), _(u"Vaše tričko již je na cestě k vám, už se na něj můžete těšit."))
    def dispatch(self, request, *args, **kwargs):
        if kwargs["user_attendance"].campaign.has_any_tshirt:
            return super().dispatch(request, *args, **kwargs)
        else:
            if kwargs["user_attendance"].has_admission_fee():
                return redirect(reverse('typ_platby'))
            else:
                return redirect(reverse('profil'))
