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


from braces.views import LoginRequiredMixin

from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import UpdateView

from dpnk import exceptions
from dpnk.models import UserAttendance
from dpnk.views import RegistrationViewMixin

from .forms import TShirtUpdateForm
from .models import DeliveryBatchDeadline


class ChangeTShirtView(RegistrationViewMixin, LoginRequiredMixin, UpdateView):
    template_name = 'registration/change_tshirt.html'
    form_class = TShirtUpdateForm
    model = UserAttendance
    success_message = _(u"Velikost trička úspěšně nastavena")
    next_url = 'typ_platby'
    prev_url = 'zmenit_tym'
    registration_phase = "zmenit_triko"

    def get_title(self, *args, **kwargs):
        if self.user_attendance.tshirt_complete():
            return _('Změňte velikost soutěžního trička')
        else:
            return _('Vyberte velikost soutěžního trička')

    def get_object(self):
        return {
            'userprofile': self.user_attendance.userprofile,
            'userattendance': self.user_attendance,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['next_batch'] = DeliveryBatchDeadline.objects.forthcoming(campaign=self.user_attendance.campaign)
        except DeliveryBatchDeadline.DoesNotExist:
            pass
        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user_attendance:
            if not request.user_attendance.team_complete():
                raise exceptions.TemplatePermissionDenied(
                    format_html(
                        _("Nejdříve se {join_team} a pak si vyberte tričko."),
                        join_team=format_html(
                            "<a href='{}'>{}</a>",
                            reverse("zmenit_tym"),
                            _('přidejte k týmu'),
                        ),
                    ),
                    self.template_name,
                    title=_("Buďte týmovým hráčem!"),
                    error_level="warning",
                )
            if request.user_attendance.package_shipped():
                raise exceptions.TemplatePermissionDenied(
                    _("Vaše tričko již je na cestě k Vám, už se na něj můžete těšit."),
                    self.template_name,
                    title=_("Hurá!"),
                    error_level="success",
                )

            if not request.user_attendance.campaign.has_any_tshirt:
                if request.user_attendance.has_admission_fee():
                    return redirect(reverse('typ_platby'))
                else:
                    return redirect(reverse('profil'))
        return super().dispatch(request, *args, **kwargs)
