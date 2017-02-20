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
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView

from .admin_forms import DispatchForm
from .models import SubsidiaryBox, TeamPackage


class DispatchView(FormView):
    success_url = reverse_lazy('dispatch')
    template_name = "dispatch.html"
    form_class = DispatchForm

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            dispatch_id = form.cleaned_data.get("dispatch_id")
            package_class = {
                'T': TeamPackage,
                'S': SubsidiaryBox,
            }[dispatch_id[0]]
            package = package_class.objects.get(id=int(dispatch_id[1:]))
            if package.dispatched:
                messages.warning(
                    self.request,
                    _("Balíček/krabice byl v minulosti již zařazen k sestavení: %s") % package,
                )
            else:
                package.dispatched = True
                package.save()
                messages.success(
                    self.request,
                    _("Balíček/krabice zařazen jako sestavený: %s") % package,
                )
        except ObjectDoesNotExist:
            messages.warning(
                self.request,
                _("Balíček/krabice nebyl nalezen."),
            )
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data['title'] = _("Zařadit balíky k sestavení")
        return context_data
