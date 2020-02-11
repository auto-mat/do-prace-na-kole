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
from braces.views import StaffuserRequiredMixin

from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView

from .admin_forms import DispatchForm
from .models import SubsidiaryBox, TeamPackage


class DispatchView(StaffuserRequiredMixin, FormView):
    raise_exception = True
    success_url = reverse_lazy('dispatch')
    template_name = "dispatch.html"
    form_class = DispatchForm

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        try:
            dispatch_id = form.cleaned_data.get("dispatch_id")
            package_class = {
                'T': TeamPackage,
                'S': SubsidiaryBox,
            }[dispatch_id[0]]
            package = package_class.objects.get(id=int(dispatch_id[1:]))
            if package.dispatched:
                context['package_message'] = _("Balíček/krabice byl v minulosti již zařazen k sestavení: %s") % package
                context['package_message_color'] = "orange"
            else:
                if isinstance(package, SubsidiaryBox) and not package.all_packages_dispatched():
                    context['package_message'] = format_html(
                        _(
                            "Tato krabice obsahuje balíčky, které ještě nebyli zařazeny k sestavení: "
                            "<a href='{}?box__id__exact={}&amp;dispatched__exact=0'>"
                            "zobrazit seznam nesestavených balíčků"
                            "</a>"
                        ),
                        reverse('admin:t_shirt_delivery_teampackage_changelist'),
                        package.pk,
                    )
                    context['package_message_color'] = "red"
                else:
                    package.dispatched = True
                    package.save()
                    context['package_message'] = _("Balíček/krabice zařazen jako sestavený: %s") % package
                    context['package_message_color'] = "green"

            if package_class == TeamPackage:
                context['box'] = package.box
            elif package_class == SubsidiaryBox:
                context['box'] = package
        except ObjectDoesNotExist:
            context['package_message'] = _("Balíček/krabice nebyl nalezen.")
            context['package_message_color'] = "red"
        return self.render_to_response(context)

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data['title'] = _("Zařadit balíky k sestavení")
        return context_data
