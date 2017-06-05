# -*- coding: utf-8 -*-
# Author: Hynek Hanke <hynek.hanke@auto-mat.cz>
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
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

# Standard library imports


import codecs
import collections
import hashlib
import json
import logging
import math
import shutil
import tempfile
import time

from http.client import HTTPSConnection

from urllib.parse import urlencode

# Django imports
from class_based_auth_views.views import LoginView

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required as login_required_simple
from django.contrib.gis.db.models.functions import Length
from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import transaction
from django.db.models import Case, Count, F, FloatField, IntegerField, Q, Sum, When
from django.db.models.functions import Coalesce
from django.forms.models import BaseModelFormSet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.shortcuts import redirect
from django.utils.decorators import classonlymethod, method_decorator
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import cache_control, cache_page, never_cache
from django.views.decorators.gzip import gzip_page
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, FormView, UpdateView

from extra_views import ModelFormSetView

from registration.backends.simple.views import RegistrationView as SimpleRegistrationView

from unidecode import unidecode
# Local imports
from . import draw
from . import forms
from . import models
from . import results
from . import util
from .decorators import must_be_approved_for_team, must_be_competitor, must_be_in_phase, must_be_owner, must_have_team, request_condition, user_attendance_has
from .email import (
    approval_request_mail,
    invitation_mail,
    invitation_register_mail,
    register_mail,
    team_created_mail,
    team_membership_approval_mail,
    team_membership_denial_mail,
)
from .forms import (
    ChangeTeamForm,
    InviteForm,
    PaymentTypeForm,
    ProfileUpdateForm,
    RegisterCompanyForm,
    RegisterSubsidiaryForm,
    RegisterTeamForm,
    RegistrationAccessFormDPNK,
    RegistrationFormDPNK,
    TeamAdminForm,
    TrackUpdateForm,
)
from .models import Answer, Campaign, City, Company, Competition, Payment, Question, Subsidiary, Team, Trip, UserAttendance, UserProfile
from .string_lazy import format_lazy, mark_safe_lazy

logger = logging.getLogger(__name__)


class TitleViewMixin(object):
    @classonlymethod
    def as_view(self, *args, **kwargs):
        if 'title' in kwargs:
            self.title = kwargs.get('title')
        return super(TitleViewMixin, self).as_view(*args, **kwargs)

    def get_title(self, *args, **kwargs):
        return self.title

    def dispatch(self, request, *args, **kwargs):
        try:
            if hasattr(self.request, 'user_attendance') and self.request.user_attendance:
                self.campaign = self.request.user_attendance.campaign
            else:
                self.campaign = Campaign.objects.get(slug=request.subdomain)
        except Campaign.DoesNotExist:
            self.campaign = None
        return super().dispatch(request, *args, **kwargs)

    def get_opening_message(self, *args, **kwargs):
        if hasattr(self, "opening_message"):
            return self.opening_message
        else:
            return ""

    def get_context_data(self, *args, **kwargs):
        context_data = super(TitleViewMixin, self).get_context_data(*args, **kwargs)
        context_data['title'] = self.get_title(*args, **kwargs)
        context_data['opening_message'] = self.get_opening_message(*args, **kwargs)
        return context_data


class DPNKLoginView(TitleViewMixin, LoginView):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['campaign'] = self.campaign
        return kwargs

    def get_title(self, *args, **kwargs):
        return _("Přihlášení do soutěže %s" % self.campaign)

    def get_initial(self):
        initial_email = self.kwargs.get('initial_email')
        if initial_email:
            return {'username': self.kwargs['initial_email']}
        else:
            return {}

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect(reverse('profil'))
        else:
            return super().get(request, *args, **kwargs)


class UserAttendanceViewMixin(object):
    @method_decorator(login_required_simple)
    @must_be_competitor
    def dispatch(self, request, *args, **kwargs):
        self.user_attendance = kwargs['user_attendance']
        return super(UserAttendanceViewMixin, self).dispatch(request, *args, **kwargs)

    def get_object(self):
        if hasattr(self, 'user_attendance'):
            return self.user_attendance


class RegistrationMessagesMixin(UserAttendanceViewMixin):
    def get(self, request, *args, **kwargs):  # noqa
        ret_val = super(RegistrationMessagesMixin, self).get(request, *args, **kwargs)

        if self.registration_phase in ('registration_uncomplete', 'profile_view'):
            if self.user_attendance.approved_for_team == 'approved' and \
                    self.user_attendance.team and \
                    self.user_attendance.team.unapproved_member_count and \
                    self.user_attendance.team.unapproved_member_count > 0:
                messages.warning(
                    request,
                    mark_safe(_(u'Ve vašem týmu jsou neschválení členové, prosíme, <a href="%s">posuďte jejich členství</a>.') % reverse('team_members')),
                )
            elif self.user_attendance.is_libero():
                # TODO: get WP slug for city
                messages.warning(
                    request,
                    format_html(
                        _(
                            'Jste sám/sama v týmu, znamená to že budete moci soutěžit pouze v kategoriích určených pro jednotlivce!'
                            ' <ul><li><a href="{invite_url}">Pozvěte</a> své kolegy do vašeho týmu, pokud jste tak již učinil/a, '
                            'vyčkejte na potvrzující e-mail a schvalte jejich členství v týmu.</li>'
                            '<li>Můžete se pokusit <a href="{join_team_url}">přidat se k jinému týmu</a>.</li>'
                            '<li>Pokud nemůžete sehnat spolupracovníky, '
                            ' <a href="https://www.dopracenakole.cz/locations/{city}/seznamka" target="_blank">najděte si cykloparťáka</a>.</li></ul>'
                        ),
                        invite_url=reverse('pozvanky'),
                        join_team_url=reverse('zmenit_tym'),
                        city=self.user_attendance.team.subsidiary.city.slug,
                    ),
                )
            if not self.user_attendance.track and not self.user_attendance.distance:
                messages.info(
                    request,
                    mark_safe(
                        _('Nemáte vyplněnou vaši typickou trasu ani vzdálenost do práce.'
                          ' Na základě této trasy se v průběhu soutěže předvyplní vaše denní trasa a vzdálenost vaší cesty.'
                          ' Vaše vyplněná trasa se objeví na '
                          '<a target="_blank" href="https://mapa.prahounakole.cz/?layers=_Wgt">cyklistické dopravní heatmapě</a>'
                          ' a pomůže při plánování cyklistické infrastruktury ve vašem městě.<br>'
                          ' <a href="%s">Vyplnit typickou trasu</a>') % reverse('upravit_trasu'),
                    ),
                )

        if self.registration_phase == 'registration_uncomplete':
            if self.user_attendance.team:
                if self.user_attendance.approved_for_team == 'undecided':
                    messages.warning(
                        request,
                        format_html(
                            _(
                                "Vaši kolegové v týmu {team} ještě musí potvrdit vaše členství."
                                " Pokud to trvá podezřele dlouho, můžete zkusit"
                                " <a href='{address}'>znovu požádat o ověření členství</a>."),
                            team=self.user_attendance.team.name, address=reverse("zaslat_zadost_clenstvi"),
                        ),
                    )
                elif self.user_attendance.approved_for_team == 'denied':
                    messages.error(
                        request,
                        mark_safe(_(u'Vaše členství v týmu bylo bohužel zamítnuto, budete si muset <a href="%s">zvolit jiný tým</a>') % reverse('zmenit_tym')),
                    )

            if not self.user_attendance.payment_waiting():
                messages.info(
                    request,
                    format_html(
                        _('Vaše platba typu {payment_type} ještě nebyla vyřízena. '
                          'Počkejte prosím na její schválení. '
                          'Pokud schválení není možné, můžete <a href="{url}">zadat jiný typ platby</a>.'),
                        payment_type=self.user_attendance.payment_type_string(), url=reverse('typ_platby'),
                    ),
                )

        if self.registration_phase == 'profile_view':
            if self.user_attendance.has_unanswered_questionnaires:
                competitions = format_html_join(
                    ", ",
                    "<a href='{}'>{}</a>",
                    ((
                        reverse_lazy("questionnaire", kwargs={"questionnaire_slug": q.slug}),
                        q.name
                    ) for q in self.user_attendance.unanswered_questionnaires().all()),
                )
                messages.info(request, format_html(_(u'Nezapomeňte vyplnit odpovědi v následujících soutěžích: {}!'), competitions))

        company_admin = self.user_attendance.related_company_admin
        if company_admin and company_admin.company_admin_approved == 'undecided':
            messages.warning(request, _(u'Vaše žádost o funkci koordinátora organizace čeká na vyřízení.'))
        if company_admin and company_admin.company_admin_approved == 'denied':
            messages.error(request, _(u'Vaše žádost o funkci koordinátora organizace byla zamítnuta.'))
        return ret_val


class RegistrationViewMixin(RegistrationMessagesMixin, TitleViewMixin, UserAttendanceViewMixin):
    template_name = 'base_generic_registration_form.html'

    def get_context_data(self, *args, **kwargs):
        context_data = super(RegistrationViewMixin, self).get_context_data(*args, **kwargs)
        context_data['registration_phase'] = self.registration_phase
        return context_data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self, 'prev_url'):
            kwargs['prev_url'] = self.prev_url
        return kwargs

    def get_success_url(self):
        if 'next' in self.request.POST:
            return reverse(self.next_url)
        elif 'submit' in self.request.POST:
            return reverse(self.success_url)
        else:
            return reverse(self.prev_url)


class ChangeTeamView(RegistrationViewMixin, FormView):
    form_class = ChangeTeamForm
    template_name = 'registration/change_team.html'
    next_url = 'zmenit_triko'
    prev_url = 'upravit_profil'
    title = _(u'Vybrat/změnit tým')
    registration_phase = "zmenit_tym"

    def get_context_data(self, *args, **kwargs):
        context_data = super(ChangeTeamView, self).get_context_data(*args, **kwargs)
        context_data['campaign_slug'] = self.user_attendance.campaign.slug
        return context_data

    @method_decorator(login_required_simple)
    @user_attendance_has(
        lambda ua: ua.approved_for_team == 'approved' and ua.team and ua.team.member_count == 1 and ua.team.unapproved_member_count > 0,
        _(u"Nemůžete opustit tým, ve kterém jsou samí neschválení členové. Napřed někoho schvalte a pak změňte tým."))
    @must_be_competitor
    def dispatch(self, request, *args, **kwargs):
        return super(ChangeTeamView, self).dispatch(request, *args, **kwargs)

    def get_previous_team(self):
        previous_user_attendance = self.user_attendance.previous_user_attendance()
        if previous_user_attendance and previous_user_attendance.team:
            try:
                return Team.objects.get(
                    name=previous_user_attendance.team.name,
                    campaign=self.user_attendance.campaign,
                )
            except Team.DoesNotExist:
                return previous_user_attendance.team.name

    def post(self, request, *args, **kwargs):  # noqa
        create_company = False
        create_subsidiary = False
        create_team = False

        form = self.form_class(request, data=request.POST, files=request.FILES, instance=self.user_attendance, prev_url=self.prev_url)

        form_company = RegisterCompanyForm(request.POST, prefix="company")
        form_subsidiary = RegisterSubsidiaryForm(request.POST, prefix="subsidiary", campaign=self.user_attendance.campaign)
        form_team = RegisterTeamForm(request.POST, prefix="team", initial={"campaign": self.user_attendance.campaign})
        create_team = 'id_team_selected' in request.POST
        if create_team:
            create_subsidiary = 'id_subsidiary_selected' in request.POST
        if create_team and create_subsidiary:
            create_company = 'id_company_selected' in request.POST
        company_valid = True
        subsidiary_valid = True
        team_valid = True

        if create_company:
            company_valid = form_company.is_valid()
            form.fields['company'].required = False
        else:
            form_company = RegisterCompanyForm(prefix="company")
            form.fields['company'].required = True

        if create_subsidiary:
            subsidiary_valid = form_subsidiary.is_valid()
            form.fields['subsidiary'].required = False
        else:
            form_subsidiary = RegisterSubsidiaryForm(prefix="subsidiary", campaign=self.user_attendance.campaign)
            form.fields['subsidiary'].required = True

        if create_team:
            team_valid = form_team.is_valid()
            form.fields['team'].required = False
        else:
            form_team = RegisterTeamForm(prefix="team", initial={"campaign": self.user_attendance.campaign, 'name': self.get_previous_team()})
            form.fields['team'].required = True

        form_valid = form.is_valid()

        if form_valid and company_valid and subsidiary_valid and team_valid:
            company = None
            subsidiary = None
            team = None

            if create_company:
                company = form_company.save()
                messages.add_message(request, messages.SUCCESS, _(u"Organizace %s úspěšně vytvořena.") % company, fail_silently=True)
            else:
                company_id = form.data['company_1'] if 'company_1' in form.data else form.data['company']
                company = Company.objects.get(id=company_id)

            if create_subsidiary:
                subsidiary = form_subsidiary.save(commit=False)
                subsidiary.company = company
                form_subsidiary.save()
                messages.add_message(request, messages.SUCCESS, _(u"Pobočka %s úspěšně vytvořena.") % subsidiary, fail_silently=True)
            else:
                subsidiary = Subsidiary.objects.get(id=form.data['subsidiary'])

            if create_team:
                team = form_team.save(commit=False)
                team.subsidiary = subsidiary
                team.campaign = self.user_attendance.campaign
                form_team.save()
                messages.add_message(request, messages.SUCCESS, _(u"Tým %s úspěšně vytvořen.") % team.name, fail_silently=True)
            else:
                team = form.cleaned_data['team']

            if create_team:
                team = form_team.save(commit=False)

                self.user_attendance.team = team
                self.user_attendance.approved_for_team = 'approved'

                form_team.save()

                self.user_attendance.team = team
                request.session['invite_success_url'] = self.get_success_url()
                self.next_url = "pozvanky"
                self.prev_url = "pozvanky"

                team_created_mail(self.user_attendance)

            form.save()

            if self.user_attendance.approved_for_team != 'approved':
                approval_request_mail(self.user_attendance)

            return redirect(self.get_success_url())
        form.fields['company'].widget.underlying_form = form_company
        form.fields['company'].widget.create = create_company

        form.fields['subsidiary'].widget.underlying_form = form_subsidiary
        form.fields['subsidiary'].widget.create = create_subsidiary

        form.fields['team'].widget.underlying_form = form_team
        form.fields['team'].widget.create = create_team

        context_data = self.get_context_data()
        context_data['form'] = form
        return render(request, self.template_name, context_data)

    def get(self, request, *args, **kwargs):
        super(ChangeTeamView, self).get(request, *args, **kwargs)
        previous_team = self.get_previous_team()
        initial = {}
        if isinstance(previous_team, Team):
            initial = {'team': previous_team}
        form = self.form_class(request, instance=self.user_attendance, prev_url=self.prev_url, initial=initial)
        form_company = RegisterCompanyForm(prefix="company")
        form_subsidiary = RegisterSubsidiaryForm(prefix="subsidiary", campaign=self.user_attendance.campaign)
        form_team = RegisterTeamForm(prefix="team", initial={"campaign": self.user_attendance.campaign, 'name': self.get_previous_team()})

        form.fields['company'].widget.underlying_form = form_company
        form.fields['subsidiary'].widget.underlying_form = form_subsidiary
        form.fields['team'].widget.underlying_form = form_team

        context_data = self.get_context_data()
        context_data['form'] = form
        return render(request, self.template_name, context_data)


class RegistrationAccessView(TitleViewMixin, FormView):
    title = "Registrace soutěžících Do práce na kole"
    template_name = 'base_generic_form.html'
    form_class = RegistrationAccessFormDPNK

    def dispatch(self, request, *args, **kwargs):
        return super(RegistrationAccessView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect(reverse('profil'))
        else:
            return super(RegistrationAccessView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        email = form.cleaned_data['email']
        user_exists = models.User.objects.filter(email=email).exists()
        if not user_exists:
            user_exists = models.User.objects.filter(username=email).exists()
        if user_exists:
            return redirect(reverse('login', kwargs={'initial_email': email}))
        else:
            return redirect(reverse('registrace', kwargs={'initial_email': email}))


class RegistrationView(TitleViewMixin, SimpleRegistrationView):
    title = "Registrace soutěžících Do práce na kole"
    template_name = 'base_generic_form.html'
    form_class = RegistrationFormDPNK
    model = UserProfile
    success_url = 'upravit_profil'

    @must_be_in_phase("registration")
    def dispatch(self, request, *args, **kwargs):
        return super(RegistrationView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {'email': self.kwargs.get('initial_email', '')}

    def register(self, registration_form):
        new_user = super(RegistrationView, self).register(registration_form)
        userprofile = UserProfile.objects.create(user=new_user)

        invitation_token = self.kwargs.get('token', None)
        try:
            team = Team.objects.get(invitation_token=invitation_token)
            if team.is_full():
                messages.error(self.request, _('Tým do kterého jste byli pozváni je již plný, budete si muset vybrat nebo vytvořit jiný tým.'))
                team = None
        except Team.DoesNotExist:
            team = None
        campaign = Campaign.objects.get(slug=self.request.subdomain)
        user_attendance = UserAttendance.objects.create(
            userprofile=userprofile,
            campaign=campaign,
            team=team,
        )
        if team:
            approve_for_team(self.request, user_attendance, "", True, False)

        register_mail(user_attendance)
        return new_user


class ConfirmTeamInvitationView(RegistrationViewMixin, FormView):
    template_name = 'registration/team_invitation.html'
    form_class = forms.ConfirmTeamInvitationForm
    success_url = reverse_lazy('zmenit_tym')
    registration_phase = 'zmenit_tym'
    title = _(u"Pozvánka do týmu")

    def get_context_data(self, **kwargs):
        context = super(ConfirmTeamInvitationView, self).get_context_data(**kwargs)
        context['old_team'] = self.user_attendance.team
        context['new_team'] = self.new_team

        if self.new_team.is_full():
            return {
                'fullpage_error_message': _('Tým do kterého jste byli pozváni je již plný, budete si muset vybrat nebo vytvořit jiný tým.'),
                'title': _("Tým je plný"),
            }
        if self.user_attendance.payment_status == 'done' and self.user_attendance.team and self.user_attendance.team.subsidiary != self.new_team.subsidiary:
            return {
                'fullpage_error_message': _(u"Již máte zaplaceno, nemůžete měnit tým mimo svoji pobočku."),
                'title': _("Účastnický poplatek již zaplacen"),
            }

        if self.user_attendance.campaign != self.new_team.campaign:
            return {
                'fullpage_error_message': _(u"Přihlašujete se do týmu ze špatné kampaně (pravděpodobně z minulého roku)."),
                'title': _("Chyba přihlášení"),
            }
        return context

    def get_success_url(self):
        return self.success_url

    def form_valid(self, form):
        if form.cleaned_data['question']:
            self.user_attendance.team = self.new_team
            self.user_attendance.save()
            approve_for_team(self.request, self.user_attendance, "", True, False)
        return super(ConfirmTeamInvitationView, self).form_valid(form)

    @method_decorator(login_required_simple)
    @must_be_competitor
    @request_condition(lambda r, a, k: Team.objects.filter(invitation_token=k['token']).count() != 1, _(u"Tým nenalezen"), _("Tým nenalezen."))
    def dispatch(self, request, *args, **kwargs):
        initial_email = kwargs['initial_email']
        if request.user.email != initial_email:
            logout(request)
            messages.add_message(
                self.request,
                messages.WARNING,
                _("Pozvánka je určena jinému uživateli, než je aktuálně přihlášen. Přihlašte se jako uživatel %s." % initial_email),
            )
            return redirect("%s?next=%s" % (reverse("login", kwargs={"initial_email": initial_email}), request.get_full_path()))
        invitation_token = self.kwargs['token']
        self.new_team = Team.objects.get(invitation_token=invitation_token)
        return super(ConfirmTeamInvitationView, self).dispatch(request, *args, **kwargs)


class PaymentTypeView(RegistrationViewMixin, FormView):
    template_name = 'registration/payment_type.html'
    title = _(u"Platba")
    registration_phase = "typ_platby"
    next_url = "profil"
    prev_url = "zmenit_triko"

    @method_decorator(login_required_simple)
    @must_have_team
    @must_be_in_phase("payment")
    @user_attendance_has(
        lambda ua: ua.payment_status == 'done',
        mark_safe_lazy(format_lazy(_("Již máte účastnický poplatek zaplacen. Pokračujte na <a href='{addr}'>zadávání jízd</a>."), addr=reverse_lazy("profil"))))
    @user_attendance_has(
        lambda ua: ua.payment_status == 'no_admission',
        mark_safe_lazy(format_lazy(_("Účastnický poplatek se neplatí. Pokračujte na <a href='{addr}'>zadávání jízd</a>."), addr=reverse_lazy("profil"))))
    @user_attendance_has(
        lambda ua: not ua.t_shirt_size,
        _("Před tím, než zaplatíte účastnický poplatek, musíte mít vybrané triko"))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PaymentTypeView, self).get_context_data(**kwargs)
        profile = self.user_attendance.userprofile
        context['user_attendance'] = self.user_attendance
        context['firstname'] = profile.user.first_name  # firstname
        context['surname'] = profile.user.last_name  # surname
        context['email'] = profile.user.email  # email
        context['amount'] = self.user_attendance.admission_fee()
        context['beneficiary_amount'] = self.user_attendance.beneficiary_admission_fee()
        context['prev_url'] = self.prev_url
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user_attendance'] = self.user_attendance
        return kwargs

    def get_form(self, form_class=PaymentTypeForm):
        form = super(PaymentTypeView, self).get_form(form_class)
        form.user_attendance = self.user_attendance
        return form

    def form_valid(self, form):
        payment_type = form.cleaned_data['payment_type']

        if payment_type == 'company':
            company_admin_email_string = mark_safe(
                ", ".join(
                    [
                        format_html(
                            "<a href='mailto:{email}'>{email}</a>",
                            email=a.userprofile.user.email,
                        ) for a in self.user_attendance.get_asociated_company_admin()
                    ]
                ),
            )
        elif payment_type == 'coupon':
            return redirect(reverse('discount_coupon'))
        else:
            company_admin_email_string = ""
        payment_choices = {
            'member_wannabe': {'type': 'amw', 'message': _("Vaše členství v klubu přátel ještě bude muset být schváleno."), 'amount': 0},
            'company': {
                'type': 'fc',
                'message': format_html(
                    _("Platbu ještě musí schválit koordinátor vaší organizace {email}"),
                    email=company_admin_email_string,
                ),
                'amount': self.user_attendance.company_admission_fee(),
            },
        }

        if payment_type in ('pay', 'pay_beneficiary'):
            logger.error(
                "Wrong payment type",
                extra={'request': self.request, 'payment_type': payment_type},
            )
            return HttpResponse(
                _(u"Pokud jste se dostali sem, tak to může být způsobené tím, že používáte zastaralý prohlížeč nebo máte vypnutý JavaScript."),
                status=500,
            )
        else:
            payment_choice = payment_choices[payment_type]
            if payment_choice:
                Payment(user_attendance=self.user_attendance, amount=payment_choice['amount'], pay_type=payment_choice['type'], status=models.Status.NEW).save()
                messages.add_message(self.request, messages.WARNING, payment_choice['message'], fail_silently=True)
                logger.info('Inserting payment', extra={'payment_type': payment_type, 'username': self.user_attendance.userprofile.user.username})

        return super(PaymentTypeView, self).form_valid(form)


class PaymentView(UserAttendanceViewMixin, TemplateView):
    beneficiary = False
    template_name = 'registration/payment.html'

    @method_decorator(login_required_simple)
    @must_have_team
    def dispatch(self, request, *args, **kwargs):
        return super(PaymentView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PaymentView, self).get_context_data(**kwargs)

        if self.user_attendance.payment_status == 'no_admission':
            return redirect(reverse('profil'))
        uid = self.request.user.id
        order_id = '%s-1' % uid
        session_id = "%sJ%d" % (order_id, int(time.time()))
        # Save new payment record
        if self.beneficiary:
            amount = self.user_attendance.beneficiary_admission_fee()
        else:
            amount = self.user_attendance.admission_fee()
        p = Payment(
            session_id=session_id,
            user_attendance=self.user_attendance,
            order_id=order_id,
            amount=amount,
            status=models.Status.NEW,
            description="Ucastnicky poplatek Do prace na kole",
        )
        p.save()
        logger.info(
            u'Inserting payment with uid: %s, order_id: %s, session_id: %s, userprofile: %s (%s), status: %s' % (
                uid,
                order_id,
                session_id,
                self.user_attendance,
                self.user_attendance.userprofile.user.username,
                p.status,
            ),
        )
        # Render form
        profile = self.user_attendance.userprofile
        firstname = unidecode(profile.user.first_name)  # firstname
        lastname = unidecode(profile.user.last_name)  # surname
        email = profile.user.email  # email
        amount_hal = int(amount * 100)  # v halerich
        description = "Ucastnicky poplatek Do prace na kole"
        client_ip = util.get_client_ip(self.request)
        timestamp = str(int(time.time()))
        language_code = self.user_attendance.userprofile.language

        context['firstname'] = firstname
        context['surname'] = lastname
        context['email'] = email
        context['amount'] = amount
        context['amount_hal'] = amount_hal
        context['description'] = description
        context['order_id'] = order_id
        context['client_ip'] = client_ip
        context['language_code'] = language_code
        context['session_id'] = session_id
        context['ts'] = timestamp
        context['sig'] = make_sig((
            settings.PAYU_POS_ID,
            session_id,
            settings.PAYU_POS_AUTH_KEY,
            str(amount_hal),
            description,
            order_id,
            firstname,
            lastname,
            email,
            language_code,
            client_ip,
            timestamp))
        return context


class BeneficiaryPaymentView(PaymentView):
    beneficiary = True


class PaymentResult(UserAttendanceViewMixin, TemplateView):
    registration_phase = 'typ_platby'
    template_name = 'registration/payment_result.html'

    @method_decorator(login_required_simple)
    def dispatch(self, request, *args, **kwargs):
        return super(PaymentResult, self).dispatch(request, *args, **kwargs)

    @transaction.atomic
    def get_context_data(self, success, trans_id, session_id, pay_type, error=None, user_attendance=None):
        context_data = super(PaymentResult, self).get_context_data()
        logger.info(
            u'Payment result: success: %s, trans_id: %s, session_id: %s, pay_type: %s, error: %s, user: %s (%s)' %
            (
                success,
                trans_id,
                session_id,
                pay_type,
                error,
                user_attendance,
                user_attendance.userprofile.user.username,
            ),
        )

        if session_id and session_id != "":
            p = Payment.objects.select_for_update().get(session_id=session_id)
            if p.status not in Payment.done_statuses:
                if success:
                    p.status = models.Status.COMMENCED
                else:
                    p.status = models.Status.REJECTED
            if not p.trans_id:
                p.trans_id = trans_id
            if not p.pay_type:
                p.pay_type = pay_type
            if not p.error:
                p.error = error
            p.save()

        context_data['pay_type'] = pay_type
        context_data['success'] = success

        if success:
            context_data['title'] = _("Platba úspěšná")
            context_data['payment_message'] = _(
                "Vaše platba byla úspěšně zadána. "
                "Až platbu obdržíme, dáme vám vědět na e-mail. "
                "Tím bude vaše registrace úspěšně dokončena.",
            )
        else:
            context_data['title'] = _("Platba neúspěšná")
            logger.warning(
                'Payment unsuccessful',
                extra={
                    'success': success,
                    'pay_type': pay_type,
                    'trans_id': trans_id,
                    'session_id': session_id,
                    'user': user_attendance.userprofile.user,
                    'request': self.request,
                },
            )
            context_data['payment_message'] = _(u"Vaše platba se nezdařila. Po přihlášení do svého profilu můžete zadat novou platbu.")
        context_data['registration_phase'] = self.registration_phase
        return context_data


def make_sig(values):
    key1 = settings.PAYU_KEY_1
    hashed_string = bytes("".join(values + (key1,)), "utf-8")
    return hashlib.md5(hashed_string).hexdigest()


def check_sig(sig, values):
    key2 = settings.PAYU_KEY_2
    hashed_string = bytes("".join(values + (key2,)), "utf-8")
    expected_sig = hashlib.md5(hashed_string).hexdigest()
    if sig != expected_sig:
        raise ValueError("Zamítnuto")


@transaction.atomic
def payment_status(request):
    # Read notification parameters
    pos_id = request.POST['pos_id']
    session_id = request.POST['session_id']
    ts = request.POST['ts']
    sig = request.POST['sig']
    logger.info('Payment status - pos_id: %s, session_id: %s, ts: %s, sig: %s' % (pos_id, session_id, ts, sig))
    check_sig(sig, (pos_id, session_id, ts))
    # Determine the status of transaction based on the notification
    c = HTTPSConnection("secure.payu.com")
    timestamp = str(int(time.time()))
    c.request(
        "POST",
        "/paygw/UTF/Payment/get/txt/",
        urlencode((
            ('pos_id', pos_id),
            ('session_id', session_id),
            ('ts', timestamp),
            ('sig', make_sig((pos_id, session_id, timestamp)))
        )),
        {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": "text/plain",
        },
    )
    raw_response = codecs.decode(c.getresponse().read(), "utf-8")
    r = {}
    for i in [i.split(':', 1) for i in raw_response.split('\n') if i != '']:
        r[i[0]] = i[1].strip()
    check_sig(
        r['trans_sig'],
        (
            r['trans_pos_id'],
            r['trans_session_id'],
            r['trans_order_id'],
            r['trans_status'],
            r['trans_amount'],
            r['trans_desc'],
            r['trans_ts'],
        ),
    )
    amount = math.floor(int(r['trans_amount']) / 100)
    # Update the corresponding payment
    # TODO: use update_or_create in Django 1.7
    p, created = Payment.objects.select_for_update().get_or_create(
        session_id=r['trans_session_id'],
        defaults={
            'order_id': r['trans_order_id'],
            'amount': amount,
            'description': r['trans_desc'],
        },
    )

    if p.amount != amount:
        logger.error(
            'Payment amount doesn\'t match',
            extra={
                'pay_type': p.pay_type,
                'status': p.status,
                'payment_response': r,
                'expected_amount': p.amount,
                'request': request,
            },
        )
        return HttpResponse("Bad amount", status=400)
    p.pay_type = r['trans_pay_type']
    p.status = r['trans_status']
    if r['trans_recv'] != '':
        p.realized = r['trans_recv']
    p.save()

    logger.info('Payment status: pay_type: %s, status: %s, payment response: %s' % (p.pay_type, p.status, r))

    # Return positive error code as per PayU protocol
    return HttpResponse("OK")


class RidesFormSet(BaseModelFormSet):
    def total_form_count(self):
        form_count = super().total_form_count()
        if hasattr(self, 'forms_max_number'):
            return min(self.forms_max_number, form_count)
        return form_count


class RidesView(TitleViewMixin, RegistrationMessagesMixin, SuccessMessageMixin, ModelFormSetView):
    model = Trip
    form_class = forms.TripForm
    formset_class = RidesFormSet
    fields = ('commute_mode', 'distance', 'direction', 'user_attendance', 'date')
    extra = 0
    uncreated_trips = []
    success_message = _(u"Tabulka jízd úspěšně změněna")
    title = _("Jízdy")

    @method_decorator(never_cache)
    @method_decorator(cache_control(max_age=0, no_cache=True, no_store=True))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def has_allow_adding_rides(self):
        if not hasattr(self, 'allow_adding_rides'):  # cache result
            self.allow_adding_rides = models.CityInCampaign.objects.get(
                city=self.user_attendance.team.subsidiary.city,
                campaign=self.user_attendance.campaign,
            ).allow_adding_rides
        return self.allow_adding_rides

    def get_queryset(self):
        if self.has_allow_adding_rides():
            self.trips, self.uncreated_trips = self.user_attendance.get_active_trips()
            return self.trips.select_related('gpxfile')
        else:
            return models.Trip.objects.none()

    def get_initial(self):
        distance = self.user_attendance.get_distance(request=self.request)
        no_work = models.CommuteMode.objects.get(slug='no_work')
        by_other_vehicle = models.CommuteMode.objects.get(slug='by_other_vehicle')
        return [
            {
                'distance': distance,
                'date': trip[0],
                'direction': trip[1],
                'user_attendance': self.user_attendance,
                'commute_mode': by_other_vehicle if util.working_day(trip[0]) else no_work,
            } for trip in self.uncreated_trips
        ]

    def get_factory_kwargs(self):
        kwargs = super().get_factory_kwargs()
        kwargs['extra'] = len(self.uncreated_trips)
        return kwargs

    def post(self, request, *args, **kwargs):
        ret_val = super().post(request, args, kwargs)
        # TODO: use Celery for this
        results.recalculate_result_competitor(self.user_attendance)
        return ret_val

    def construct_formset(self):
        formset = super().construct_formset()
        formset.forms = [form for form in formset.forms if ('direction' in form.initial)]
        formset.forms_max_number = len(formset.forms)

        formset.forms = sorted(formset.forms, key=lambda form: form.initial['direction'] or form.instance.direction, reverse=True)
        formset.forms = sorted(formset.forms, key=lambda form: form.initial['date'] or form.instance.date, reverse=True)

        # This is hack, to get commute mode queryset cached:
        qs = models.CommuteMode.objects.all()
        cache = [p for p in qs]

        class CacheQuerysetAll(object):
            def __iter__(self):
                return iter(cache)

            def _prefetch_related_lookups(self):
                return False
        qs.all = CacheQuerysetAll
        for form in formset.forms:
            form.fields['commute_mode'].queryset = qs
        return formset

    title = _(u'Moje jízdy')
    registration_phase = 'profile_view'
    template_name = 'registration/competition_profile.html'

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        city_slug = self.user_attendance.team.subsidiary.city.get_wp_slug()
        campaign = self.user_attendance.campaign
        context_data['questionnaire_answer'] = models.Answer.objects.filter(
            Q(attachment__icontains=".jpg") | Q(attachment__icontains=".jpeg") |
            Q(attachment__icontains=".png") | Q(attachment__icontains=".gif") |
            Q(attachment__icontains=".bmp") | Q(attachment__icontains=".tiff"),
            question__competition__city=None,
            question__competition__competition_type="questionnaire",
            question__competition__campaign=campaign,
            attachment__isnull=False,
        ).exclude(
            attachment='',
        ).select_related('question__competition').order_by('?')
        context_data['city_slug'] = city_slug
        context_data['map_city_slug'] = 'mapa' if city_slug == 'praha' else city_slug
        context_data['competition_phase'] = campaign.phase("competition")
        context_data['commute_modes'] = models.CommuteMode.objects.all()
        return context_data

    def get(self, request, *args, **kwargs):
        reason = self.user_attendance.entered_competition_reason()
        if reason is True:
            return super().get(request, *args, **kwargs)
        else:
            redirect_view = {
                'tshirt_uncomplete': 'zmenit_triko',
                'team_uncomplete': 'zmenit_tym',
                'payment_uncomplete': 'typ_platby',
                'profile_uncomplete': 'upravit_profil',
                'team_waiting': 'registration_uncomplete',
                'payment_waiting': 'registration_uncomplete',
                'track_uncomplete': 'registration_uncomplete',
            }
            return redirect(reverse(redirect_view[reason]))


class RidesDetailsView(TitleViewMixin, RegistrationMessagesMixin, TemplateView):
    title = _("Podrobný přehled jízd")
    template_name = 'registration/rides_details.html'
    registration_phase = 'profile_view'

    def get_context_data(self, *args, **kwargs):
        trips, uncreated_trips = self.user_attendance.get_all_trips(util.today())
        uncreated_trips = [
            (
                trip[0],
                models.Trip.DIRECTIONS_DICT[trip[1]],
                _("Jinak") if util.working_day(trip[0]) else _("Žádná cesta"),
            ) for trip in uncreated_trips
        ]
        trips = list(trips) + uncreated_trips
        trips = sorted(trips, key=lambda trip: trip.direction if type(trip) == Trip else trip[1], reverse=True)
        trips = sorted(trips, key=lambda trip: trip.date if type(trip) == Trip else trip[0])
        days = list(util.days(self.user_attendance.campaign.phase("competition"), util.today()))

        context_data = super().get_context_data(*args, **kwargs)
        context_data['trips'] = trips
        context_data['other_gpx_files'] = models.GpxFile.objects.filter(user_attendance=self.user_attendance).exclude(trip__date__in=days)
        return context_data


class RegistrationUncompleteForm(TitleViewMixin, RegistrationMessagesMixin, TemplateView):
    template_name = 'base_generic_form.html'
    title = _('Stav registrace')
    opening_message = _("Před tím, než budete moct zadávat jízdy, bude ještě nutné vyřešit pár věcí:")
    registration_phase = 'registration_uncomplete'

    def get(self, request, *args, **kwargs):
        reason = self.user_attendance.entered_competition_reason()
        if reason is True:
            return redirect(reverse('profil'))
        else:
            return super().get(request, *args, **kwargs)


class UserAttendanceView(TitleViewMixin, UserAttendanceViewMixin, TemplateView):
    pass


class PackageView(RegistrationViewMixin, TemplateView):
    template_name = "registration/package.html"
    title = _(u"Sledování balíčku")
    registration_phase = "zmenit_tym"


class ApplicationView(RegistrationViewMixin, TemplateView):
    template_name = "registration/applications.html"
    title = _("Aplikace")
    registration_phase = "application"


class OtherTeamMembers(UserAttendanceViewMixin, TitleViewMixin, TemplateView):
    template_name = 'registration/team_members.html'
    title = _(u"Výsledky členů týmu")

    @method_decorator(login_required_simple)
    @must_be_competitor
    @must_be_approved_for_team
    @method_decorator(never_cache)
    @method_decorator(cache_control(max_age=0, no_cache=True, no_store=True))
    def dispatch(self, request, *args, **kwargs):
        return super(OtherTeamMembers, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context_data = super(OtherTeamMembers, self).get_context_data(*args, **kwargs)
        team_members = []
        if self.user_attendance.team:
            team_members = self.user_attendance.team.all_members().annotate(length=Length('track'))
            team_members = team_members.select_related('userprofile__user', 'team__subsidiary__city', 'team__subsidiary__company', 'campaign')
        context_data['team_members'] = team_members
        context_data['registration_phase'] = "other_team_members"
        return context_data

    # This is here for NewRelic to distinguish from TemplateView.get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CompetitionsRulesView(TitleViewMixin, TemplateView):
    title_base = _("Pravidla soutěží")

    def get_title(self, *args, **kwargs):
        city = get_object_or_404(City, slug=kwargs['city_slug'])
        return "%s - %s" % (self.title_base, city)

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        city_slug = kwargs['city_slug']
        competitions = Competition.objects.filter(
            Q(city__slug=city_slug) | Q(city__isnull=True, company=None),
            campaign__slug=self.request.subdomain,
            is_public=True,
        )
        context_data['competitions'] = competitions
        context_data['city_slug'] = city_slug
        context_data['campaign_slug'] = self.request.subdomain
        return context_data


class AdmissionsView(UserAttendanceViewMixin, TitleViewMixin, TemplateView):
    title = _(u"Výsledky soutěží")
    success_url = reverse_lazy("competitions")
    competition_types = None

    @method_decorator(login_required_simple)
    @must_be_competitor
    @method_decorator(never_cache)
    @method_decorator(cache_control(max_age=0, no_cache=True, no_store=True))
    def dispatch(self, request, *args, **kwargs):
        return super(AdmissionsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context_data = super(AdmissionsView, self).get_context_data(*args, **kwargs)
        competitions = self.user_attendance.get_competitions(competition_types=self.competition_types)
        for competition in competitions:
            competition.competitor_can_admit = competition.can_admit(self.user_attendance)
        context_data['competitions'] = competitions
        context_data['registration_phase'] = "competitions"
        return context_data

    # This is here for NewRelic to distinguish from TemplateView.get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CompetitionsView(AdmissionsView):
    title = _("Výsledky pravidelnostních a výkonnostních soutěží")
    competition_types = ('length', 'frequency')
    template_name = "registration/competitions.html"


class QuestionareCompetitionsView(AdmissionsView):
    title = _("Výsledky dotazníkových soutěží a soutěží na kreativitu")
    competition_types = ('questionnaire',)
    template_name = "registration/competitions.html"


class CompetitionResultsView(TitleViewMixin, TemplateView):
    template_name = 'registration/competition_results.html'
    title = _("Výsledky soutěže")

    def dispatch(self, request, *args, **kwargs):
        return super(CompetitionResultsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context_data = super(CompetitionResultsView, self).get_context_data(*args, **kwargs)
        competition_slug = kwargs.get('competition_slug')

        try:
            context_data['competition'] = Competition.objects.get(slug=competition_slug)
        except Competition.DoesNotExist:
            logger.exception('Unknown competition', extra={'slug': competition_slug, 'request': self.request})
            return {
                'fullpage_error_message': mark_safe(
                    _(
                        'Tuto soutěž v systému nemáme. Pokud si myslíte, že by zde měly být výsledky nějaké soutěže, napište prosím na '
                        '<a href="mailto:kontakt@dopracenakole.cz?subject=Neexistující soutěž">kontakt@dopracenakole.cz</a>'
                    ),
                ),
                'title': _("Není vybraný tým"),
            }
        return context_data

    # This is here for NewRelic to distinguish from TemplateView.get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UpdateProfileView(RegistrationViewMixin, UpdateView):
    template_name = 'submenu_personal.html'
    form_class = ProfileUpdateForm
    model = UserProfile
    success_message = _(u"Osobní údaje úspěšně upraveny")
    next_url = "zmenit_tym"
    registration_phase = "upravit_profil"
    title = _(u"Osobní údaje")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['campaign'] = self.user_attendance.campaign
        return kwargs

    def get_object(self):
        return self.user_attendance.userprofile


class UpdateTrackView(RegistrationViewMixin, UpdateView):
    template_name = 'registration/change_track.html'
    form_class = TrackUpdateForm
    model = UserAttendance
    success_message = _(u"Trasa/vzdálenost úspěšně upravena")
    success_url = 'profil'
    registration_phase = "upravit_profil"
    title = _("Upravit typickou trasu")

    def get_object(self):
        return self.user_attendance


def handle_uploaded_file(source, username):
    logger.info("Saving file", extra={'username': username, 'filename': source.name})
    fd, filepath = tempfile.mkstemp(suffix=u"_%s&%s" % (username, unidecode(source.name).replace(" ", "_")), dir=settings.MEDIA_ROOT + u"/questionaire")
    with open(filepath, 'wb') as dest:
        shutil.copyfileobj(source, dest)
    return u"questionaire/" + filepath.rsplit("/", 1)[1]


class QuestionnaireView(TitleViewMixin, TemplateView):
    template_name = 'registration/questionaire.html'
    success_url = reverse_lazy('questionnaire_competitions')
    title = _(u"Vyplňte odpovědi")
    form_class = forms.AnswerForm

    @method_decorator(login_required_simple)
    @must_be_competitor
    def dispatch(self, request, *args, **kwargs):
        questionaire_slug = kwargs['questionnaire_slug']
        self.user_attendance = kwargs['user_attendance']
        self.userprofile = request.user.userprofile
        try:
            self.competition = Competition.objects.get(slug=questionaire_slug)
        except Competition.DoesNotExist:
            logger.exception('Unknown questionaire', extra={'slug': questionaire_slug, 'request': request})
            return HttpResponse(
                _(
                    '<div class="text-danger">Tento dotazník v systému nemáme.'
                    ' Pokud si myslíte, že by zde mělo jít vyplnit dotazník, napište prosím na'
                    ' <a href="mailto:kontakt@dopracenakole.cz?subject=Neexistující dotazník">kontakt@dopracenakole.cz</a></div>'
                ),
                status=401,
            )
        self.show_points = self.competition.has_finished() or self.userprofile.user.is_superuser
        self.is_actual = self.competition.is_actual()
        self.questions = Question.objects.filter(competition=self.competition).order_by('order')

        for question in self.questions:
            try:
                answer = question.answer_set.get(user_attendance=self.user_attendance)
                question.points_given = answer.points_given
                question.comment_given = answer.comment_given
            except Answer.DoesNotExist:
                answer = Answer(question=question, user_attendance=self.user_attendance)
            question.form = self.form_class(
                instance=answer,
                question=question,
                prefix="question-%s" % question.pk,
                show_points=self.show_points,
                is_actual=self.is_actual,
            )
        return super(QuestionnaireView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        if not self.is_actual:
            return HttpResponse(string_concat("<div class='text-warning'>", _(u"Soutěž již nelze vyplňovat"), "</div>"))

        invalid_count = 0
        for question in self.questions:
            if not question.with_answer():
                continue

            try:
                answer = question.answer_set.get(user_attendance=self.user_attendance)
                question.points_given = answer.points_given
            except Answer.DoesNotExist:
                answer = Answer(question=question, user_attendance=self.user_attendance)
            question.points_given = answer.points_given
            question.form = self.form_class(
                request.POST,
                files=request.FILES,
                instance=answer,
                question=question,
                prefix="question-%s" % question.pk,
                show_points=self.show_points,
                is_actual=self.is_actual,
            )
            if not question.form.is_valid():
                invalid_count += 1

        if invalid_count == 0:
            for question in self.questions:
                if not question.with_answer():
                    continue
                question.form.save()
            self.competition.make_admission(self.user_attendance)
            messages.add_message(request, messages.SUCCESS, _("Odpovědi byly úspěšně zadány"))
            return redirect(self.success_url)
        context_data = self.get_context_data()
        context_data['invalid_count'] = invalid_count
        return render(request, self.template_name, context_data)

    def get_context_data(self, *args, **kwargs):
        context_data = super(QuestionnaireView, self).get_context_data(*args, **kwargs)

        context_data.update({
            'questions': self.questions,
            'questionaire': self.competition,
            'show_submit': self.is_actual and not self.competition.without_admission,
            'show_points': self.show_points,
        })
        return context_data


class QuestionnaireAnswersAllView(TitleViewMixin, TemplateView):
    template_name = 'registration/questionnaire_answers_all.html'
    title = _(u"Výsledky všech soutěží")

    def get_context_data(self, *args, **kwargs):
        context_data = super(QuestionnaireAnswersAllView, self).get_context_data(*args, **kwargs)

        competition_slug = kwargs.get('competition_slug')
        competition = Competition.objects.get(slug=competition_slug)
        if not competition.public_answers and not self.request.user.is_superuser and self.request.user.userprofile.competition_edition_allowed(competition):
            context_data['fullpage_error_message'] = _(u"Tato soutěž nemá povolené prohlížení odpovědí.")
            context_data['title'] = _(u"Odpovědi nejsou dostupné")
            return context_data

        competitors = competition.get_results()
        competitors = competitors.select_related('user_attendance__team__subsidiary__city', 'user_attendance__userprofile__user')

        for competitor in competitors:
            competitor.answers = Answer.objects.filter(
                user_attendance__in=competitor.user_attendances(),
                question__competition__slug=competition_slug,
            ).select_related('question')
        context_data['show_points'] = competition.has_finished() or (self.request.user.is_authenticated() and self.request.user.userprofile.user.is_superuser)
        context_data['competitors'] = competitors
        context_data['competition'] = competition
        return context_data


@staff_member_required
def questions(request):
    questions = Question.objects.all()
    if not request.user.is_superuser:
        questions = questions.filter(competition__city__in=request.user.userprofile.administrated_cities.all())
    questions = questions.filter(competition__campaign__slug=request.subdomain)
    questions = questions.order_by('-competition__campaign', 'competition__slug', 'order')
    questions = questions.distinct()
    questions = questions.select_related('competition__campaign', 'choice_type')
    questions = questions.prefetch_related('answer_set', 'competition__city')
    return render(
        request,
        'admin/questions.html',
        {
            'title': _("Otázky v dotaznících"),
            'questions': questions,
        },
    )


@staff_member_required
def questionnaire_results(
        request,
        competition_slug=None,):
    competition = Competition.objects.get(slug=competition_slug)
    if not request.user.is_superuser and request.user.userprofile.competition_edition_allowed(competition):
        return HttpResponse(string_concat("<div class='text-warning'>", _(u"Soutěž je vypsána ve městě, pro které nemáte oprávnění."), "</div>"))

    competitors = competition.get_results()
    return render(
        request,
        'admin/questionnaire_results.html',
        {
            'competition_slug': competition_slug,
            'competitors': competitors,
            'competition': competition,
            'title': _("Výsledky odpovědí na dotazník"),
        },
    )


@staff_member_required
def questionnaire_answers(
        request,
        competition_slug=None,):
    competition = Competition.objects.get(slug=competition_slug)
    if not request.user.is_superuser and request.user.userprofile.competition_edition_allowed(competition):
        return HttpResponse(string_concat("<div class='text-warning'>", _(u"Soutěž je vypsána ve městě, pro které nemáte oprávnění."), "</div>"))

    try:
        competitor_result = competition.get_results().get(pk=request.GET['uid'])
    except models.CompetitionResult.DoesNotExist:
        return HttpResponse(_(u'<div class="text-danger">Nesprávně zadaný soutěžící.</div>'), status=401)
    answers = Answer.objects.filter(
        user_attendance__in=competitor_result.user_attendances(),
        question__competition__slug=competition_slug,
    )
    total_points = competitor_result.result
    return render(
        request,
        'admin/questionnaire_answers.html',
        {
            'answers': answers,
            'competitor': competitor_result,
            'media': settings.MEDIA_URL,
            'title': _("Odpovědi na dotazník"),
            'total_points': total_points,
        },
    )


@staff_member_required  # noqa
def answers(request):
    question_id = request.GET['question']
    question = Question.objects.get(id=question_id)
    if not request.user.is_superuser and request.user.userprofile.competition_edition_allowed(question.competition):
        return HttpResponse(string_concat("<div class='text-warning'>", _(u"Otázka je položená ve městě, pro které nemáte oprávnění."), "</div>"), status=401)

    if request.method == 'POST':
        points = [(k.split('-')[1], v) for k, v in request.POST.items() if k.startswith('points-')]
        for p in points:
            if not p[1] in ('', 'None', None):
                answer = Answer.objects.get(id=p[0])
                try:
                    answer.points_given = float(p[1].replace(",", "."))
                except ValueError:
                    answer.points_given = None

                answer.save()

    answers = Answer.objects.filter(question_id=question_id).order_by('-points_given')
    answers = answers.select_related('user_attendance__team__subsidiary__city', 'user_attendance__userprofile__user')
    answers = answers.prefetch_related('choices')
    total_respondents = answers.count()
    count = {c: {} for c in City.objects.all()}
    count_all = {}
    respondents = {c: 0 for c in City.objects.all()}
    choice_names = {}

    for a in answers:
        a.city = a.user_attendance.team.subsidiary.city if a.user_attendance and a.user_attendance.team else None

    if question.question_type in ('choice', 'multiple-choice'):
        for a in answers:
            if a.city:
                respondents[a.city] += 1
                for c in a.choices.all():
                    try:
                        count[a.city][c.id] += 1
                    except KeyError:
                        count[a.city][c.id] = 1
                        choice_names[c.id] = c.text
                    try:
                        count_all[c.id] += 1
                    except KeyError:
                        count_all[c.id] = 1

    stat = {c: [] for c in City.objects.all()}
    stat['Celkem'] = []
    for city, city_count in count.items():
        for k, v in city_count.items():
            stat[city].append((choice_names[k], v, float(v) / respondents[city] * 100))
    for k, v in count_all.items():
        stat['Celkem'].append((choice_names[k], v, float(v) / total_respondents * 100))

    def get_percentage(r):
        return r[2]
    for k in stat.keys():
        stat[k].sort(key=get_percentage, reverse=True)

    return render(
        request,
        'admin/answers.html',
        {
            'question': question,
            'answers': answers,
            'stat': stat,
            'total_respondents': total_respondents,
            'media': settings.MEDIA_URL,
            'title': _("Odpověd na dotazník"),
            'choice_names': choice_names,
        },
    )


def approve_for_team(request, user_attendance, reason="", approve=False, deny=False):
    if deny:
        if not reason:
            messages.add_message(
                request,
                messages.ERROR,
                _(u"Při zamítnutí člena týmu musíte vyplnit zprávu."),
                extra_tags="user_attendance_%s" % user_attendance.pk,
                fail_silently=True,
            )
            return
        user_attendance.approved_for_team = 'denied'
        user_attendance.save()
        team_membership_denial_mail(user_attendance, request.user, reason)
        messages.add_message(
            request,
            messages.SUCCESS,
            _(u"Členství uživatele %s ve vašem týmu bylo zamítnuto" % user_attendance),
            extra_tags="user_attendance_%s" % user_attendance.pk,
            fail_silently=True,
        )
        return
    elif approve:
        if user_attendance.campaign.too_much_members(user_attendance.team.members().count() + 1):
            messages.add_message(
                request,
                messages.ERROR,
                _(u"Tým je již plný, další člen již nemůže být potvrzen."),
                extra_tags="user_attendance_%s" % user_attendance.pk,
                fail_silently=True,
            )
            return
        user_attendance.approved_for_team = 'approved'
        user_attendance.save()
        team_membership_approval_mail(user_attendance)
        messages.add_message(
            request,
            messages.SUCCESS,
            _(u"Členství uživatele %(user)s v týmu %(team)s bylo odsouhlaseno.") %
            {"user": user_attendance, "team": user_attendance.team.name},
            extra_tags="user_attendance_%s" % user_attendance.pk,
            fail_silently=True,
        )
        return


class TeamApprovalRequest(TitleViewMixin, UserAttendanceViewMixin, TemplateView):
    template_name = 'registration/request_team_approval.html'
    title = _(u"Znovu odeslat žádost o členství")
    registration_phase = "zmenit_tym"

    @method_decorator(login_required_simple)
    @must_be_competitor
    def dispatch(self, request, *args, **kwargs):
        approval_request_mail(request.user_attendance)
        return super(TeamApprovalRequest, self).dispatch(request, *args, **kwargs)


class InviteView(UserAttendanceViewMixin, TitleViewMixin, FormView):
    template_name = "submenu_team.html"
    form_class = InviteForm
    title = _(u'Pozvětě své kolegy do týmu')
    registration_phase = "zmenit_tym"
    success_url = reverse_lazy('pozvanky')

    def get_context_data(self, *args, **kwargs):
        context_data = super(InviteView, self).get_context_data(*args, **kwargs)
        context_data['registration_phase'] = self.registration_phase
        return context_data

    @method_decorator(login_required_simple)
    @must_be_approved_for_team
    @must_be_competitor
    def dispatch(self, request, *args, **kwargs):
        return super(InviteView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        emails = [form.cleaned_data['email1'], form.cleaned_data['email2'], form.cleaned_data['email3'], form.cleaned_data['email4']]

        for email in emails:
            if email:
                try:
                    invited_user = models.User.objects.get(is_active=True, email=email)

                    invited_user_attendance, created = UserAttendance.objects.get_or_create(
                        userprofile=invited_user.userprofile,
                        campaign=self.user_attendance.campaign,
                    )

                    if invited_user_attendance.team == self.user_attendance.team:
                        approve_for_team(self.request, invited_user_attendance, "", True, False)
                        messages.add_message(
                            self.request,
                            messages.SUCCESS,
                            _(u"Uživatel %(user)s byl přijat do vašeho týmu.") % {"user": invited_user_attendance, "email": email},
                            fail_silently=True,
                        )
                    else:
                        invitation_register_mail(self.user_attendance, invited_user_attendance)
                        messages.add_message(
                            self.request,
                            messages.SUCCESS,
                            _(u"Odeslána pozvánka uživateli %(user)s na e-mail %(email)s") % {"user": invited_user_attendance, "email": email},
                            fail_silently=True,
                        )
                except models.User.DoesNotExist:
                    invitation_mail(self.user_attendance, email)
                    messages.add_message(self.request, messages.SUCCESS, _(u"Odeslána pozvánka na e-mail %s") % email, fail_silently=True)

        invite_success_url = self.request.session.get('invite_success_url')
        self.request.session['invite_success_url'] = None
        return redirect(invite_success_url or self.success_url)


class UpdateTeam(TitleViewMixin, UserAttendanceViewMixin, SuccessMessageMixin, UpdateView):
    template_name = 'submenu_team.html'
    form_class = TeamAdminForm
    success_url = reverse_lazy('edit_team')
    title = _(u"Upravit název týmu")
    registration_phase = 'zmenit_tym'
    success_message = _(u"Název týmu úspěšně změněn na %(name)s")

    def get_context_data(self, *args, **kwargs):
        context_data = super(UpdateTeam, self).get_context_data(*args, **kwargs)
        context_data['registration_phase'] = self.registration_phase
        return context_data

    @method_decorator(login_required_simple)
    @must_be_competitor
    @must_be_approved_for_team
    def dispatch(self, request, *args, **kwargs):
        return super(UpdateTeam, self).dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.user_attendance.team


class TeamMembers(TitleViewMixin, UserAttendanceViewMixin, TemplateView):
    template_name = 'registration/team_admin_members.html'
    registration_phase = "zmenit_tym"
    title = _("Schvalování členů týmu")

    @method_decorator(login_required_simple)
    @method_decorator(never_cache)
    @must_be_approved_for_team
    def dispatch(self, request, *args, **kwargs):
        return super(TeamMembers, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if 'approve' in request.POST:
            approve_id = None
            try:
                action, approve_id = request.POST['approve'].split('-')
            except ValueError:
                logger.exception(u'Can\'t split POST approve parameter', extra={'request': request})
                messages.add_message(request, messages.ERROR, _(u"Nastala chyba při přijímání uživatele, patrně používáte zastaralý internetový prohlížeč."))

            if approve_id:
                approved_user = UserAttendance.objects.get(id=approve_id)
                userprofile = approved_user.userprofile
                if approved_user.approved_for_team not in ('undecided', 'denied') or \
                   not userprofile.user.is_active or approved_user.team != self.user_attendance.team:
                    logger.error(
                        'Approving user with wrong parameters.',
                        extra={
                            'request': request,
                            'user': userprofile.user,
                            'username': userprofile.user.username,
                            'approval': approved_user.approved_for_team,
                            'team': approved_user.team,
                            'active': userprofile.user.is_active,
                        },
                    )
                    messages.add_message(
                        request,
                        messages.ERROR,
                        _("Tento uživatel již byl přijat do týmu. Pravděpodobně jste dvakrát odeslali formulář."),
                        extra_tags="user_attendance_%s" % approved_user.pk,
                        fail_silently=True,
                    )
                else:
                    approve_for_team(request, approved_user, request.POST.get('reason-' + str(approved_user.id), ''), action == 'approve', action == 'deny')
        return render(request, self.template_name, self.get_context_data())

    def get_context_data(self, *args, **kwargs):
        context_data = super(TeamMembers, self).get_context_data(*args, **kwargs)
        team = self.user_attendance.team
        if not team:
            return {
                'fullpage_error_message': _(u"Další členové vašeho týmu se zobrazí, jakmile budete mít vybraný tým"),
                'title': _("Není vybraný tým"),
            }

        unapproved_users = []
        for self.user_attendance in UserAttendance.objects.filter(team=team, userprofile__user__is_active=True):
            userprofile = self.user_attendance.userprofile
            unapproved_users.append([
                ('state', None, self.user_attendance.approved_for_team),
                ('id', None, str(self.user_attendance.id)),
                ('class', None, self.user_attendance.payment_class()),
                ('name', _(u"Jméno"), str(userprofile)),
                ('email', _(u"E-mail"), userprofile.user.email),
                ('payment_description', _(u"Platba"), self.user_attendance.get_payment_status_display()),
                ('telephone', _(u"Telefon"), userprofile.telephone),
                ('state_name', _(u"Stav"), str(self.user_attendance.get_approved_for_team_display())),
            ])
        context_data['unapproved_users'] = unapproved_users
        context_data['registration_phase'] = self.registration_phase
        return context_data


def distance_all_modes(trips):
    return trips.filter(commute_mode__slug__in=('bicycle', 'by_foot')).aggregate(
        distance__sum=Coalesce(Sum("distance"), 0.0),
        count__sum=Coalesce(Count("id"), 0),
        count_bicycle=Sum(
            Case(
                When(commute_mode__slug='bicycle', then=1),
                output_field=IntegerField(),
                default=0,
            ),
        ),
        distance_bicycle=Sum(
            Case(
                When(commute_mode__slug='bicycle', then=F('distance')),
                output_field=FloatField(),
                default=0,
            ),
        ),
        count_foot=Sum(
            Case(
                When(commute_mode__slug='by_foot', then=1),
                output_field=IntegerField(),
                default=0,
            ),
        ),
        distance_foot=Sum(
            Case(
                When(commute_mode__slug='by_foot', then=F('distance')),
                output_field=FloatField(),
                default=0,
            ),
        ),
    )


def distance(trips):
    return distance_all_modes(trips)['distance__sum'] or 0


def total_distance(campaign):
    return distance_all_modes(Trip.objects.filter(user_attendance__campaign=campaign))


def period_distance(campaign, day_from, day_to):
    return distance_all_modes(Trip.objects.filter(user_attendance__campaign=campaign, date__gte=day_from, date__lte=day_to))


def trips(trips):
    return trips.count()


@cache_page(60 * 60)
def statistics(
    request,
    template='registration/statistics.html',
):
    campaign_slug = request.subdomain
    campaign = Campaign.objects.get(slug=campaign_slug)
    distances = total_distance(campaign)
    distances_today = period_distance(campaign, util.today(), util.today())
    variables = {}
    variables['ujeta-vzdalenost'] = distances['distance__sum'] or 0
    variables['usetrene-emise-co2'] = util.get_emissions(distances['distance__sum'] or 0)['co2']
    variables['ujeta-vzdalenost-kolo'] = distances['distance_bicycle']
    variables['ujeta-vzdalenost-pesky'] = distances['distance_foot']
    variables['ujeta-vzdalenost-dnes'] = distances_today['distance__sum']
    variables['pocet-cest'] = distances['count__sum'] or 0
    variables['pocet-cest-pesky'] = distances['count_foot']
    variables['pocet-cest-kolo'] = distances['count_bicycle']
    variables['pocet-cest-dnes'] = distances_today['count__sum']
    variables['pocet-zaplacenych'] = UserAttendance.objects.filter(
        Q(campaign=campaign) &
        Q(userprofile__user__is_active=True) &
        Q(transactions__status__in=models.Payment.done_statuses),
    ).exclude(Q(transactions__payment__pay_type__in=models.Payment.NOT_PAYING_TYPES)).distinct().count()
    variables['pocet-prihlasenych'] = UserAttendance.objects.filter(campaign=campaign, userprofile__user__is_active=True).distinct().count()
    variables['pocet-soutezicich'] = UserAttendance.objects.filter(
        Q(campaign=campaign) &
        Q(userprofile__user__is_active=True) &
        Q(transactions__status__in=models.Payment.done_statuses),
    ).distinct().count()
    variables['pocet-spolecnosti'] = Company.objects.filter(Q(subsidiaries__teams__campaign=campaign)).distinct().count()
    variables['pocet-pobocek'] = Subsidiary.objects.filter(Q(teams__campaign=campaign)).distinct().count()

    data = json.dumps(variables)
    return HttpResponse(data)


@cache_page(60 * 60)
def daily_chart(
        request,
        template='registration/daily-chart.html',):
    campaign_slug = request.subdomain
    campaign = Campaign.objects.get(slug=campaign_slug)
    values = [period_distance(campaign, day, day)['distance__sum'] or 0 for day in util.days(campaign.phase('competition'))]
    return render(
        request,
        template,
        {
            'values': values,
            'days': reversed(list(util.days(campaign.phase('competition')))),
            'max_value': max(values),
        },
    )


@cache_page(60 * 60)
def daily_distance_extra_json(
        request,):
    campaign_slug = request.subdomain
    campaign = Campaign.objects.get(slug=campaign_slug)
    values = collections.OrderedDict()
    for day in util.days(campaign.phase('competition')):
        distances = period_distance(campaign, day, day)
        emissions_co2 = util.get_emissions(distances['distance__sum'] or 0)['co2']
        values[str(day)] = {
            'distance': distances['distance__sum'] or 0,
            'distance_bicycle': distances['distance_bicycle'] or 0,
            'distance_foot': distances['distance_foot'] or 0,
            'emissions_co2': emissions_co2,
        }
    data = json.dumps(values)
    return HttpResponse(data)


class CompetitorCountView(TitleViewMixin, TemplateView):
    template_name = 'registration/competitor_count.html'
    title = _("Počty soutěžících")

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        campaign_slug = self.request.subdomain
        context_data['campaign_slug'] = campaign_slug
        context_data['cities'] =\
            City.objects.\
            filter(subsidiary__teams__users__payment_status='done', subsidiary__teams__users__campaign__slug=campaign_slug).\
            annotate(competitor_count=Count('subsidiary__teams__users')).\
            order_by('-competitor_count')
        context_data['without_city'] =\
            UserAttendance.objects.\
            filter(payment_status='done', campaign__slug=campaign_slug, team=None)
        context_data['total'] =\
            UserAttendance.objects.\
            filter(payment_status='done', campaign__slug=campaign_slug)
        return context_data


class BikeRepairView(TitleViewMixin, CreateView):
    template_name = 'base_generic_form.html'
    form_class = forms.BikeRepairForm
    success_url = 'bike_repair'
    success_message = _(u"%(user_attendance)s je nováček a právě si zažádal o opravu kola")
    model = models.CommonTransaction
    title = _("Cykloservis")

    def get_initial(self):
        campaign = Campaign.objects.get(slug=self.request.subdomain)
        return {
            'campaign': campaign,
        }

    def form_valid(self, form):
        super(BikeRepairView, self).form_valid(form)
        return redirect(reverse(self.success_url))


class DrawResultsView(TitleViewMixin, TemplateView):
    template_name = 'admin/draw.html'
    title = _("Losování")

    def get_context_data(self, city_slug=None, *args, **kwargs):
        context_data = super(DrawResultsView, self).get_context_data(*args, **kwargs)
        competition_slug = kwargs.get('competition_slug')
        context_data['results'] = draw.draw(competition_slug)
        return context_data


class CombinedTracksKMLView(TemplateView):
    template_name = "gis/tracks.kml"

    @method_decorator(gzip_page)
    @method_decorator(never_cache)              # don't cache KML in browsers
    @method_decorator(cache_page(24 * 60 * 60))  # cache in memcached for 24h
    def dispatch(self, request, *args, **kwargs):
        return super(CombinedTracksKMLView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, city_slug=None, *args, **kwargs):
        context_data = super(CombinedTracksKMLView, self).get_context_data(*args, **kwargs)
        filter_params = {}
        if city_slug:
            filter_params['team__subsidiary__city__slug'] = city_slug
        user_attendances = models.UserAttendance.objects.filter(campaign__slug=self.request.subdomain, **filter_params).kml()
        context_data['user_attendances'] = user_attendances
        return context_data


class UpdateGpxFileView(TitleViewMixin, UserAttendanceViewMixin, SuccessMessageMixin, UpdateView):
    form_class = forms.GpxFileForm
    model = models.GpxFile
    template_name = "registration/gpx_file.html"
    success_url = reverse_lazy("profil")
    title = _(u"Zadat trasu")

    def get_initial(self):
        return {'user_attendance': self.user_attendance}

    def get_object(self, queryset=None):
        return get_object_or_404(models.GpxFile, id=self.kwargs['id'])

    @must_be_owner
    def dispatch(self, request, *args, **kwargs):
        return super(UpdateGpxFileView, self).dispatch(request, *args, **kwargs)


class CreateGpxFileView(TitleViewMixin, UserAttendanceViewMixin, SuccessMessageMixin, CreateView):
    form_class = forms.GpxFileForm
    model = models.GpxFile
    template_name = "registration/gpx_file.html"
    success_url = reverse_lazy("profil")
    title = _(u"Zadat trasu")

    def get_initial(self):
        if self.user_attendance.track:
            track = self.user_attendance.track
        else:
            track = None

        return {
            'user_attendance': self.user_attendance,
            'direction': self.kwargs['direction'],
            'trip_date': self.kwargs['date'],
            'track': track,
        }

    @must_be_owner
    def dispatch(self, request, *args, **kwargs):
        return super(CreateGpxFileView, self).dispatch(request, *args, **kwargs)
