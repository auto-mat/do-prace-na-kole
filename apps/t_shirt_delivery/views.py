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

import datetime

from braces.views import LoginRequiredMixin

from django.core import serializers
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import UpdateView

from dpnk import exceptions
from dpnk.models import UserAttendance, Payment
from dpnk.views import RegistrationViewMixin

from .forms import TShirtUpdateForm
from .models import DeliveryBatchDeadline, TShirtSize


class TShirtDeliveryView(RegistrationViewMixin, LoginRequiredMixin, TemplateView):
    template_name = "registration/tshirt_delivery.html"
    title = _("Vaše triko je již na cestě")
    registration_phase = "zmenit_triko"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            batch_created = (
                self.user_attendance.package_shipped().team_package.box.delivery_batch.created
            )
            context["batch_created"] = batch_created
            batch_delivery = DeliveryBatchDeadline.objects.previous(
                batch_created, campaign=self.user_attendance.campaign
            ).delivery_to
            if datetime.datetime.now() <= batch_delivery:
                context["batch_delivery"] = batch_delivery.date()
        except DeliveryBatchDeadline.DoesNotExist:
            pass
        return context


class ChangeTShirtView(RegistrationViewMixin, LoginRequiredMixin, UpdateView):
    template_name = "registration/change_tshirt.html"
    form_class = TShirtUpdateForm
    model = UserAttendance
    success_message = _("Uložili jsme si Vaší velikost")
    next_url = "typ_platby"
    prev_url = "zmenit_tym"
    registration_phase = "zmenit_triko"

    def get_title(self, *args, **kwargs):
        if self.user_attendance.tshirt_complete():
            return _("Změňte velikost a typ soutěžního trička")
        else:
            return _("Vyberte velikost a typ soutěžního trička")

    def get_object(self):
        return {
            "userprofile": self.user_attendance.userprofile,
            "userattendance": self.user_attendance,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context["next_batch"] = DeliveryBatchDeadline.objects.forthcoming(
                campaign=self.user_attendance.campaign
            )
        except DeliveryBatchDeadline.DoesNotExist:
            pass

        tshirt_query = TShirtSize.objects.filter(
            campaign=self.user_attendance.campaign, available=True
        ).exclude(t_shirt_preview=None)

        context["all_tshirts"] = serializers.serialize("json", tshirt_query)
        context["actual_t_shirt"] = ""
        context["none_t_shirt"] = ""
        context["campaign_t_shirt_year"] = self.user_attendance.campaign.year
        if self.user_attendance.t_shirt_size:
            context["actual_t_shirt"] = self.user_attendance.t_shirt_size.name
            t_shirts = TShirtSize.objects.filter(
                campaign=self.user_attendance.campaign,
            )
            if t_shirts:
                none_t_shirt = t_shirts.first()
                if self.user_attendance.t_shirt_size.name == none_t_shirt.name:
                    context["none_t_shirt"] = none_t_shirt.name

        tshirts_urls = {}
        for t in tshirt_query:
            try:
                t_year, t_name = t.name.split("-", 1)
                if t_year not in tshirts_urls:
                    tshirts_urls.update({t_year: t.t_shirt_preview.url})
            except ValueError:
                pass
        context["tshirts_urls"] = tshirts_urls

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
                            _("přidejte k týmu"),
                        ),
                    ),
                    self.template_name,
                    title=_("Buďte týmovým hráčem!"),
                    error_level="warning",
                )
            if request.user_attendance.package_shipped():
                raise NotImplementedError(
                    "This should never be reached - it should be already treated in view function"
                )

            if not request.user_attendance.campaign.has_any_tshirt:
                if request.user_attendance.has_admission_fee():
                    return redirect(reverse("typ_platby"))
                else:
                    return redirect(reverse("dpnk_registration_complete"))
        return self.testing_passthrough(request, *args, **kwargs)

    def testing_passthrough(self, request, *args, **kwargs):
        if (
            request.session.get("source")
            in settings.TESTING_FAST_REGISTRATION_PASSTRHOUGH_SOURCES
        ):
            request.user_attendance.t_shirt_size = (
                request.user_attendance.campaign.tshirtsize_set.first()
            )
            import dpnk.models

            Payment(
                user_attendance=request.user_attendance,
                amount=0,
                pay_type="fe",
                status=dpnk.models.Status.DONE,
            ).save()
            request.user_attendance.save()
            return redirect(reverse("profil"))
        return super().dispatch(request, *args, **kwargs)


def tshirt_view(request, *args, **kwargs):
    if request.user_attendance and request.user_attendance.package_shipped():
        return TShirtDeliveryView.as_view()(request, *args, **kwargs)
    return ChangeTShirtView.as_view()(request, *args, **kwargs)
