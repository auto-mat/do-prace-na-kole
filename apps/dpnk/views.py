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
import time
from http.client import HTTPSConnection
from urllib.parse import urlencode
import hashlib
import codecs
from . import results
import json
import collections
# Django imports
from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator, classonlymethod
from django.views.decorators.gzip import gzip_page
from .decorators import must_be_approved_for_team, must_be_competitor, must_have_team, user_attendance_has, request_condition, must_be_in_phase, must_be_owner
from django.contrib.auth.decorators import login_required as login_required_simple
from django.db.models import Sum, Q
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat
from django.utils.safestring import mark_safe
from django.views.decorators.cache import cache_page, never_cache, cache_control
from django.views.generic.edit import FormView, UpdateView, CreateView
from django.views.generic.base import TemplateView
from class_based_auth_views.views import LoginView
# Registration imports
from registration.backends.simple.views import RegistrationView as SimpleRegistrationView
# Model imports
from .models import UserProfile, Trip, Answer, Question, Team, Payment, Subsidiary, Company, Competition, City, UserAttendance, Campaign
from . import forms
from .forms import (
    RegistrationFormDPNK,
    RegistrationAccessFormDPNK,
    RegisterSubsidiaryForm,
    RegisterCompanyForm,
    RegisterTeamForm,
    ProfileUpdateForm,
    InviteForm,
    TeamAdminForm,
    PaymentTypeForm,
    ChangeTeamForm,
    TrackUpdateForm,
    )
from django.conf import settings
from django.http import HttpResponse
# Local imports
from . import util
from . import draw
from dpnk.email import (
    approval_request_mail,
    register_mail,
    team_membership_approval_mail,
    team_membership_denial_mail,
    team_created_mail,
    invitation_mail,
    invitation_register_mail)
from django.db import transaction

from extra_views import ModelFormSetView
from unidecode import unidecode
from django.shortcuts import redirect
from django.core.urlresolvers import reverse, reverse_lazy
from .string_lazy import mark_safe_lazy, format_lazy
import logging
from . import models
import tempfile
import shutil
logger = logging.getLogger(__name__)


class TitleViewMixin(object):
    @classonlymethod
    def as_view(self, *args, **kwargs):
        if 'title' in kwargs:
            self.title = kwargs.get('title')
        return super(TitleViewMixin, self).as_view(*args, **kwargs)

    def get_title(self, *args, **kwargs):
        return self.title

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
    title = "Přihlášení soutežících Do práce na kole"

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
            if self.user_attendance.team and self.user_attendance.team.unapproved_member_count and self.user_attendance.team.unapproved_member_count > 0:
                messages.warning(request, mark_safe(_(u'Ve vašem týmu jsou neschválení členové, prosíme, <a href="%s">posuďte jejich členství</a>.') % reverse('team_members')))
            elif self.user_attendance.is_libero():
                # TODO: get WP slug for city
                messages.warning(request, mark_safe(
                    _(u'Jste sám/sama v týmu, znamená to že budete moci soutěžit pouze v kategoriích určených pro jednotlivce!'
                      u' <ul><li><a href="%(invite_url)s">Pozvěte</a> své kolegy do vašeho týmu, pokud jste tak již učinil/a, '
                      u'vyčkejte na potvrzující email a schvalte jejich členství v týmu.</li>'
                      u'<li>Můžete se pokusit <a href="%(join_team_url)s">přidat se k jinému týmu</a>.</li>'
                      u'<li>Pokud nemůžete sehnat spolupracovníky, '
                      u' <a href="http://www.dopracenakole.cz/locations/%(city)s/seznamka" target="_blank">najděte si cykloparťáka</a>.</li></ul>')
                    % {
                        'invite_url':
                        reverse('pozvanky'), 'join_team_url': reverse('zmenit_tym'), 'city': self.user_attendance.team.subsidiary.city.slug}))

        if self.registration_phase == 'registration_uncomplete':
            if self.user_attendance.team:
                if self.user_attendance.approved_for_team == 'undecided':
                    messages.warning(request, mark_safe(
                        _(
                            u"Vaši kolegové musí v týmu %(team)s ještě musí potvrdit vaše členství."
                            u" Pokud to trvá podezřele dlouho, můžete zkusit"
                            u" <a href='%(address)s'>znovu požádat o ověření členství</a>.") %
                        {'team': self.user_attendance.team.name, 'address': reverse("zaslat_zadost_clenstvi")}))
                elif self.user_attendance.approved_for_team == 'denied':
                    messages.error(request, mark_safe(_(u'Vaše členství v týmu bylo bohužel zamítnuto, budete si muset <a href="%s">zvolit jiný tým</a>') % reverse('zmenit_tym')))

            if not self.user_attendance.track and not self.user_attendance.distance:
                messages.info(request, mark_safe(
                    _(u'Nemáte vyplněnou vaši typickou trasu ani vzdálenost do práce.'
                      u' Na základě této trasy se v průběhu soutěže předvyplní vaše denní trasa a vzdálenost vaší cesty.'
                      u' Vaše vyplněná trasa se objeví na <a target="_blank" href="http://mapa.prahounakole.cz/?layers=_Wgt">cyklistické dopravní heatmapě</a>'
                      u' a pomůže při plánování cyklistické infrastruktury ve vašem městě.</br>'
                      u' <a href="%s">Vyplnit typickou trasu</a>') % reverse('upravit_trasu')))

            if self.user_attendance.payment_status not in ('done', 'none',):
                messages.info(request, mark_safe(
                    _('Vaše platba typu %(payment_type)s ještě nebyla vyřízena. '
                      'Počkejte prosím na její schválení. '
                      'Pokud schválení není možné, můžete <a href="%(url)s">zadat jiný typ platby</a>.') %
                    {'payment_type': self.user_attendance.payment_type_string(), 'url': reverse('typ_platby')}))

        if self.registration_phase == 'profile_view':
            if self.user_attendance.has_unanswered_questionnaires:
                competitions = ", ".join([
                    "<a href='%(url)s'>%(name)s</a>" %
                    {"url": reverse_lazy("questionnaire", kwargs={"questionnaire_slug": q.slug}), "name": q.name} for q in self.user_attendance.unanswered_questionnaires().all()])
                messages.info(request, mark_safe(_(u'Nezapomeňte vyplnit odpovědi v následujících soutěžích: %s!') % competitions))

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
    @must_be_competitor
    # @user_attendance_has(lambda ua: ua.entered_competition(), _(u"Po vstupu do soutěže nemůžete měnit tým."))
    def dispatch(self, request, *args, **kwargs):
        return super(ChangeTeamView, self).dispatch(request, *args, **kwargs)

    def get_previous_team_name(self):
        previous_user_attendance = self.user_attendance.previous_user_attendance()
        if previous_user_attendance and previous_user_attendance.team:
            return previous_user_attendance.team.name

    def post(self, request, *args, **kwargs):  # noqa
        create_company = False
        create_subsidiary = False
        create_team = False

        form = self.form_class(request, data=request.POST, files=request.FILES, instance=self.user_attendance)

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
            form_team = RegisterTeamForm(prefix="team", initial={"campaign": self.user_attendance.campaign, 'name': self.get_previous_team_name()})
            form.fields['team'].required = True
        old_team = self.user_attendance.team

        form_valid = form.is_valid()

        if form_valid and company_valid and subsidiary_valid and team_valid:
            team_changed = form.cleaned_data and 'team' in form.cleaned_data and old_team != form.cleaned_data['team']

            company = None
            subsidiary = None
            team = None

            if create_company:
                company = form_company.save()
                messages.add_message(request, messages.SUCCESS, _(u"Organizace %s úspěšně vytvořena.") % company, fail_silently=True)
            else:
                company = Company.objects.get(id=form.data['company'])

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

            if team_changed and not create_team:
                self.user_attendance.approved_for_team = 'undecided'
                approval_request_mail(self.user_attendance)

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
        form = self.form_class(request, instance=self.user_attendance)
        form_company = RegisterCompanyForm(prefix="company")
        form_subsidiary = RegisterSubsidiaryForm(prefix="subsidiary", campaign=self.user_attendance.campaign)
        form_team = RegisterTeamForm(prefix="team", initial={"campaign": self.user_attendance.campaign, 'name': self.get_previous_team_name()})

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


class ConfirmDeliveryView(UpdateView):
    template_name = 'base_generic_form.html'
    form_class = forms.ConfirmDeliveryForm
    success_url = 'profil'

    def form_valid(self, form):
        super(ConfirmDeliveryView, self).form_valid(form)
        return redirect(reverse(self.success_url))

    def get_object(self):
        return self.user_attendance.package_shipped()

    @user_attendance_has(lambda ua: not ua.t_shirt_size.ship, _(u"Startovní balíček se neodesílá, pokud nechcete žádné tričko."))
    @user_attendance_has(lambda ua: not ua.package_shipped(), _(u"Startovní balíček ještě nebyl odeslán"))
    @user_attendance_has(lambda ua: ua.package_delivered(), _(u"Doručení startovního balíčku potvrzeno"))
    @must_be_competitor
    def dispatch(self, request, *args, **kwargs):
        return super(ConfirmDeliveryView, self).dispatch(request, *args, **kwargs)


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

        if self.user_attendance.payment_status == 'done' and self.user_attendance.team.subsidiary != self.new_team.subsidiary:
            return {'fullpage_error_message': _(u"Již máte zaplaceno, nemůžete měnit tým mimo svoji pobočku.")}

        if self.user_attendance.campaign != self.new_team.campaign:
            return {'fullpage_error_message': _(u"Přihlašujete se do týmu ze špatné kampaně (pravděpodobně z minulého roku).")}
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
    @request_condition(lambda r, a, k: Team.objects.filter(invitation_token=k['token']).count() != 1, _(u"Tým nenalezen."))
    @request_condition(lambda r, a, k: r.user.email != k['initial_email'], _(u"Pozvánka je určena jinému uživateli, než je aktuálně přihlášen."))
    def dispatch(self, request, *args, **kwargs):
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
        mark_safe_lazy(format_lazy(_(u"Již máte startovné zaplaceno. Pokračujte na <a href='{addr}'>zadávání jízd</a>."), addr=reverse_lazy("profil"))))
    @user_attendance_has(
        lambda ua: ua.payment_status == 'no_admission',
        mark_safe_lazy(format_lazy(_(u"Startovné se neplatí. Pokračujte na <a href='{addr}'>zadávání jízd</a>."), addr=reverse_lazy("profil"))))
    @user_attendance_has(
        lambda ua: not ua.t_shirt_size,
        _("Před tím, než zaplatíte startovné, musíte mít vybrané triko"))
    def dispatch(self, request, *args, **kwargs):
        dispatch = super(PaymentTypeView, self).dispatch(request, *args, **kwargs)
        return dispatch

    def get_context_data(self, **kwargs):
        context = super(PaymentTypeView, self).get_context_data(**kwargs)
        profile = self.user_attendance.userprofile
        context['user_attendance'] = self.user_attendance
        context['firstname'] = profile.user.first_name  # firstname
        context['surname'] = profile.user.last_name  # surname
        context['email'] = profile.user.email  # email
        context['amount'] = self.user_attendance.admission_fee()
        context['beneficiary_amount'] = self.user_attendance.beneficiary_admission_fee()
        context['aklub_url'] = settings.AKLUB_URL
        return context

    def get_form(self, form_class=PaymentTypeForm):
        form = super(PaymentTypeView, self).get_form(form_class)
        form.user_attendance = self.user_attendance
        return form

    def form_valid(self, form):
        payment_type = form.cleaned_data['payment_type']

        if payment_type == 'company':
            company_admin_email_string = ", ".join(["<a href='mailto:%(email)s'>%(email)s</a>" % {
                'email': a.user.email} for a in self.user_attendance.get_asociated_company_admin()])
        else:
            company_admin_email_string = ""
        payment_choices = {
            'member': {'type': 'am', 'message': _(u"Vaše členství v klubu přátel ještě bude muset být schváleno"), 'amount': 0},
            'member_wannabe': {'type': 'amw', 'message': _(u"Vaše členství v klubu přátel ještě bude muset být schváleno"), 'amount': 0},
            'free': {'type': 'fe', 'message': _(u"Váš nárok na startovné zdarma bude muset být ještě ověřen"), 'amount': 0},
            'company': {'type': 'fc', 'message': mark_safe(_(u"Platbu ještě musí schválit koordinátor vaší organizace %(email)s" % {
                "email": company_admin_email_string})), 'amount': self.user_attendance.company_admission_fee()},
        }

        if payment_type in ('pay', 'pay_beneficiary'):
            logger.error(u'Pay payment type, request: %s' % (self.request))
            return HttpResponse(_(u"Pokud jste se dostali sem, tak to může být způsobené tím, že používáte zastaralý prohlížeč nebo máte vypnutý JavaScript."), status=500)
        else:
            payment_choice = payment_choices[payment_type]
            if payment_choice:
                Payment(user_attendance=self.user_attendance, amount=payment_choice['amount'], pay_type=payment_choice['type'], status=models.Status.NEW).save()
                messages.add_message(self.request, messages.WARNING, payment_choice['message'], fail_silently=True)
                logger.info('Inserting %s payment for %s' % (payment_type, self.user_attendance))

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
        p = Payment(session_id=session_id,
                    user_attendance=self.user_attendance,
                    order_id=order_id,
                    amount=amount,
                    status=models.Status.NEW,
                    description="Ucastnicky poplatek Do prace na kole")
        p.save()
        logger.info(
            u'Inserting payment with uid: %s, order_id: %s, session_id: %s, userprofile: %s (%s), status: %s' %
            (uid, order_id, session_id, self.user_attendance, self.user_attendance.userprofile.user.username, p.status))
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
    title = "Stav platby"
    template_name = 'registration/payment_result.html'

    @method_decorator(login_required_simple)
    def dispatch(self, request, *args, **kwargs):
        return super(PaymentResult, self).dispatch(request, *args, **kwargs)

    @transaction.atomic
    def get_context_data(self, success, trans_id, session_id, pay_type, error=None, user_attendance=None):
        context_data = super(PaymentResult, self).get_context_data()
        logger.info(
            u'Payment result: success: %s, trans_id: %s, session_id: %s, pay_type: %s, error: %s, user: %s (%s)' %
            (success, trans_id, session_id, pay_type, error, user_attendance, user_attendance.userprofile.user.username))

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
            context_data['payment_message'] = _(u"Vaše platba byla úspěšně zadána. Až platbu obdržíme, dáme vám vědět.")
        else:
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
    c.request("POST", "/paygw/UTF/Payment/get/txt/",
              urlencode((
                  ('pos_id', pos_id),
                  ('session_id', session_id),
                  ('ts', timestamp),
                  ('sig', make_sig((pos_id, session_id, timestamp)))
              )),
              {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"})
    raw_response = codecs.decode(c.getresponse().read(), "utf-8")
    r = {}
    for i in [i.split(':', 1) for i in raw_response.split('\n') if i != '']:
        r[i[0]] = i[1].strip()
    check_sig(r['trans_sig'], (r['trans_pos_id'], r['trans_session_id'], r['trans_order_id'],
                               r['trans_status'], r['trans_amount'], r['trans_desc'],
                               r['trans_ts']))
    amount = int(r['trans_amount']) / 100
    # Update the corresponding payment
    # TODO: use update_or_create in Django 1.7
    p, created = Payment.objects.select_for_update().get_or_create(
        session_id=r['trans_session_id'],
        defaults={
            'order_id': r['trans_order_id'],
            'amount': amount,
            'description': r['trans_desc'],
        })

    if p.amount != amount:
        logger.error(
            'Payment amount doesn\'t match: pay_type: %s, status: %s, payment response: %s, expected amount: %s' %
            (p.pay_type, p.status, r, p.amount))
        return HttpResponse("Bad amount", status=400)
    p.pay_type = r['trans_pay_type']
    p.status = r['trans_status']
    if r['trans_recv'] != '':
        p.realized = r['trans_recv']
    p.save()

    logger.info('Payment status: pay_type: %s, status: %s, payment response: %s' % (p.pay_type, p.status, r))

    # Return positive error code as per PayU protocol
    return HttpResponse("OK")


class RidesView(RegistrationMessagesMixin, SuccessMessageMixin, ModelFormSetView):
    model = Trip
    form_class = forms.TripForm
    fields = ('commute_mode', 'distance', 'direction', 'user_attendance', 'date')
    extra = 0
    uncreated_trips = []
    success_message = _(u"Tabulka jízd úspěšně změněna")

    @method_decorator(never_cache)
    @method_decorator(cache_control(max_age=0, no_cache=True, no_store=True))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        allow_adding_rides = models.CityInCampaign.objects.get(city=self.user_attendance.team.subsidiary.city, campaign=self.user_attendance.campaign).allow_adding_rides
        if allow_adding_rides:
            self.trips, self.uncreated_trips = self.user_attendance.get_active_trips()
            return self.trips.select_related('gpxfile')
        else:
            return models.CityInCampaign.objects.none()

    def get_initial(self):
        distance = self.user_attendance.get_distance()
        return [{'distance': distance, 'date': trip[0], 'direction': trip[1], 'user_attendance': self.user_attendance} for trip in self.uncreated_trips]

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
        ret_val = super().construct_formset()
        ret_val.forms = sorted(ret_val.forms, key=lambda form: form.initial['direction'] or form.instance.direction, reverse=True)
        ret_val.forms = sorted(ret_val.forms, key=lambda form: form.initial['date'] or form.instance.date)
        return ret_val

    title = _(u'Moje jízdy')
    registration_phase = 'profile_view'
    template_name = 'registration/competition_profile.html'

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        city_slug = self.user_attendance.team.subsidiary.city.slug
        context_data['city_slug'] = city_slug
        context_data['map_city_slug'] = 'mapa' if city_slug == 'praha' else city_slug
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


class RegistrationUncompleteForm(TitleViewMixin, RegistrationMessagesMixin, TemplateView):
    template_name = 'base_generic_form.html'
    title = _(u'Registrace není kompletní')
    opening_message = mark_safe(_("Děkujeme za vaší registraci.<br/>Před tím, než budete moct zadávat jízdy, bude ještě nutné vyřešit pár věcí:"))
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
            team_members = self.user_attendance.team.all_members().select_related('userprofile__user', 'team__subsidiary__city', 'team__subsidiary__company', 'campaign')
        context_data['team_members'] = team_members
        context_data['registration_phase'] = "other_team_members"
        return context_data


class CompetitionsView(TitleViewMixin, TemplateView):
    def get_title(self, *args, **kwargs):
        city = City.objects.get(slug=kwargs['city_slug'])
        return _(u"Pravidla soutěží - %s" % city)

    def get_context_data(self, *args, **kwargs):
        context_data = super(CompetitionsView, self).get_context_data(*args, **kwargs)
        competitions = Competition.objects.filter(Q(city__slug=kwargs['city_slug']) | Q(city__isnull=True, company=None), campaign__slug=self.request.subdomain)
        context_data['competitions'] = competitions
        return context_data


class AdmissionsView(UserAttendanceViewMixin, TitleViewMixin, TemplateView):
    title = _(u"Výsledky soutěží")
    success_url = reverse_lazy("competitions")

    @method_decorator(login_required_simple)
    @must_be_competitor
    @method_decorator(never_cache)
    @method_decorator(cache_control(max_age=0, no_cache=True, no_store=True))
    def dispatch(self, request, *args, **kwargs):
        return super(AdmissionsView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if 'admission_competition_id' in request.POST and request.POST['admission_competition_id']:
            competition = Competition.objects.get(id=request.POST['admission_competition_id'])
            competition.make_admission(self.user_attendance, True)
        if 'cancellation_competition_id' in request.POST and request.POST['cancellation_competition_id']:
            competition = Competition.objects.get(id=request.POST['cancellation_competition_id'])
            competition.make_admission(self.user_attendance, False)
        return redirect(self.success_url)

    def get_context_data(self, *args, **kwargs):
        context_data = super(AdmissionsView, self).get_context_data(*args, **kwargs)
        competitions = self.user_attendance.get_competitions()
        for competition in competitions:
            competition.competitor_has_admission = competition.has_admission(self.user_attendance)
            competition.competitor_can_admit = competition.can_admit(self.user_attendance)
        context_data['competitions'] = competitions
        context_data['registration_phase'] = "competitions"
        return context_data


class CompetitionResultsView(TemplateView):
    template_name = 'registration/competition_results.html'

    @method_decorator(cache_page(60))
    def dispatch(self, request, *args, **kwargs):
        return super(CompetitionResultsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context_data = super(CompetitionResultsView, self).get_context_data(*args, **kwargs)
        competition_slug = kwargs.get('competition_slug')
        limit = kwargs.get('limit')

        if limit == '':
            limit = None

        try:
            competition = Competition.objects.get(slug=competition_slug)
        except Competition.DoesNotExist:
            logger.exception('Unknown competition slug %s, request: %s' % (competition_slug, self.request))
            return HttpResponse(_(u'<div class="text-error">Tuto soutěž v systému nemáme.'
                                  u' Pokud si myslíte, že by zde měly být výsledky nějaké soutěže, napište prosím na'
                                  u' <a href="mailto:kontakt@dopracenakole.cz?subject=Neexistující soutěž">kontakt@dopracenakole.cz</a></div>'), status=401)

        results = competition.get_results()
        if competition.competitor_type == 'single_user' or competition.competitor_type == 'libero':
            results = results.select_related('user_attendance__userprofile__user', 'user_attendance__team__subsidiary__company', 'user_attendance__team__subsidiary__city')
        elif competition.competitor_type == 'team':
            results = results.select_related('team__subsidiary__company', 'team__subsidiary__company', 'team__subsidiary__city')
        elif competition.competitor_type == 'company':
            results = results.select_related('company')

        context_data['competition'] = competition
        context_data['results'] = results[:limit]
        return context_data


class UpdateProfileView(RegistrationViewMixin, UpdateView):
    template_name = 'submenu_personal.html'
    form_class = ProfileUpdateForm
    model = UserProfile
    success_message = _(u"Osobní údaje úspěšně upraveny")
    next_url = "zmenit_tym"
    registration_phase = "upravit_profil"
    title = _(u"Osobní údaje")

    def get_object(self):
        return self.request.user.userprofile


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


class ChangeTShirtView(RegistrationViewMixin, UpdateView):
    template_name = 'registration/change_tshirt.html'
    form_class = forms.TShirtUpdateForm
    model = UserAttendance
    success_message = _(u"Velikost trička úspěšně nastavena")
    next_url = 'typ_platby'
    prev_url = 'zmenit_tym'
    registration_phase = "zmenit_triko"
    title = _(u"Upravit velikost trička")

    def get_object(self):
        return self.user_attendance

    @method_decorator(login_required_simple)
    @user_attendance_has(lambda ua: ua.package_shipped(), _(u"Velikost trika nemůžete měnit, již bylo zařazeno do zpracování"))
    def dispatch(self, request, *args, **kwargs):
        return super(ChangeTShirtView, self).dispatch(request, *args, **kwargs)


def handle_uploaded_file(source, username):
    logger.info("Saving file: username: %s, filename: %s" % (username, source.name))
    fd, filepath = tempfile.mkstemp(suffix=u"_%s&%s" % (username, unidecode(source.name).replace(" ", "_")), dir=settings.MEDIA_ROOT + u"/questionaire")
    with open(filepath, 'wb') as dest:
        shutil.copyfileobj(source, dest)
    return u"questionaire/" + filepath.rsplit("/", 1)[1]


class QuestionnaireView(TitleViewMixin, TemplateView):
    template_name = 'registration/questionaire.html'
    success_url = reverse_lazy('competitions')
    title = _(u"Vyplňte odpovědi")
    form_class = forms.AnswerForm

    @method_decorator(login_required_simple)
    @must_be_competitor
    def dispatch(self, request, *args, **kwargs):
        questionaire_slug = kwargs['questionnaire_slug']
        self.user_attendance = kwargs['user_attendance']
        self.questionnaire = models.Competition.objects.get(slug=questionaire_slug)
        self.userprofile = request.user.userprofile
        try:
            self.competition = Competition.objects.get(slug=questionaire_slug)
        except Competition.DoesNotExist:
            logger.exception('Unknown questionaire slug %s, request: %s' % (questionaire_slug, request))
            return HttpResponse(_(u'<div class="text-error">Tento dotazník v systému nemáme.'
                                  u' Pokud si myslíte, že by zde mělo jít vyplnit dotazník, napište prosím na'
                                  u' <a href="mailto:kontakt@dopracenakole.cz?subject=Neexistující dotazník">kontakt@dopracenakole.cz</a></div>'), status=401)
        self.show_points = self.competition.has_finished() or self.userprofile.user.is_superuser
        self.is_actual = self.competition.is_actual()
        self.questions = Question.objects.filter(competition=self.competition).order_by('order')
        return super(QuestionnaireView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        for question in self.questions:
            try:
                answer = question.answer_set.get(user_attendance=self.user_attendance)
                question.points_given = answer.points_given
            except Answer.DoesNotExist:
                answer = Answer(question=question, user_attendance=self.user_attendance)
            question.form = self.form_class(instance=answer, question=question, prefix="question-%s" % question.pk, show_points=self.show_points, is_actual=self.is_actual)
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        if not self.is_actual:
            return HttpResponse(string_concat("<div class='text-warning'>", _(u"Soutěž již nelze vyplňovat"), "</div>"))

        valid = True
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
                is_actual=self.is_actual)
            if not question.form.is_valid():
                valid = False

        if valid:
            for question in self.questions:
                if not question.with_answer():
                    continue
                question.form.save()
            self.competition.make_admission(self.user_attendance)
            return redirect(self.success_url)
        return render(request, self.template_name, self.get_context_data())

    def get_context_data(self, *args, **kwargs):
        context_data = super(QuestionnaireView, self).get_context_data(*args, **kwargs)

        context_data.update({
            'questions': self.questions,
            'questionaire': self.questionnaire,
            'show_submit': self.is_actual and not self.questionnaire.without_admission,
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
            return context_data

        competitors = competition.get_results()

        for competitor in competitors:
            competitor.answers = Answer.objects.filter(
                user_attendance__in=competitor.user_attendances(),
                question__competition__slug=competition_slug)
        context_data['competitors'] = competitors
        context_data['competition'] = competition
        return context_data


@staff_member_required
def questions(request):
    filter_query = Q()
    if not request.user.is_superuser:
        filter_query = Q(competition__city__in=request.user.userprofile.administrated_cities.all())
    questions = Question.objects.filter(filter_query).order_by('-competition__campaign', 'competition__slug', 'order').distinct()
    return render(
        request,
        'admin/questions.html',
        {
            'questions': questions
        })


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
        })


@staff_member_required
def questionnaire_answers(
        request,
        competition_slug=None,):
    competition = Competition.objects.get(slug=competition_slug)
    if not request.user.is_superuser and request.user.userprofile.competition_edition_allowed(competition):
        return HttpResponse(string_concat("<div class='text-warning'>", _(u"Soutěž je vypsána ve městě, pro které nemáte oprávnění."), "</div>"))

    try:
        competitor_result = competition.get_results().get(pk=request.GET['uid'])
    except:
        return HttpResponse(_(u'<div class="text-error">Nesprávně zadaný soutěžící.</div>'), status=401)
    answers = Answer.objects.filter(
        user_attendance__in=competitor_result.user_attendances(),
        question__competition__slug=competition_slug)
    total_points = competitor_result.result
    return render(
        request,
        'admin/questionnaire_answers.html',
        {
            'answers': answers,
            'competitor': competitor_result,
            'media': settings.MEDIA_URL,
            'total_points': total_points
        })


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
                answer.points_given = int(p[1])
                answer.save()

    answers = Answer.objects.filter(question_id=question_id).order_by('-points_given')
    total_respondents = answers.count()
    count = dict((c, {}) for c in City.objects.all())
    count_all = {}
    respondents = dict((c, 0) for c in City.objects.all())
    choice_names = {}

    for a in answers:
        a.city = a.user_attendance.team.subsidiary.city if a.user_attendance.team else None

    if question.type in ('choice', 'multiple-choice'):
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

    stat = dict((c, []) for c in City.objects.all())
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
            'choice_names': choice_names
        })


def approve_for_team(request, user_attendance, reason="", approve=False, deny=False):
    if deny:
        if not reason:
            messages.add_message(
                request,
                messages.ERROR,
                _(u"Při zamítnutí člena týmu musíte vyplnit zprávu."),
                extra_tags="user_attendance_%s" % user_attendance.pk,
                fail_silently=True)
            return
        user_attendance.approved_for_team = 'denied'
        user_attendance.save()
        team_membership_denial_mail(user_attendance, request.user, reason)
        messages.add_message(
            request,
            messages.SUCCESS,
            _(u"Členství uživatele %s ve vašem týmu bylo zamítnuto" % user_attendance),
            extra_tags="user_attendance_%s" % user_attendance.pk,
            fail_silently=True)
        return
    elif approve:
        if len(user_attendance.team.members()) >= settings.MAX_TEAM_MEMBERS:
            messages.add_message(
                request,
                messages.ERROR,
                _(u"Tým je již plný, další člen již nemůže být potvrzen."),
                extra_tags="user_attendance_%s" % user_attendance.pk,
                fail_silently=True)
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
            fail_silently=True)
        return


class TeamApprovalRequest(UserAttendanceViewMixin, TemplateView):
    template_name = 'registration/request_team_approval.html'
    title = _(u"Znovu odeslat žádost o členství")
    registration_phase = "zmenit_tym"

    @method_decorator(login_required_simple)
    @must_be_competitor
    def dispatch(self, request, *args, **kwargs):
        return super(TeamApprovalRequest, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        approval_request_mail(self.user_attendance)
        return super(TeamApprovalRequest, self).form_valid(form)


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
                            fail_silently=True)
                    else:
                        invitation_register_mail(self.user_attendance, invited_user_attendance)
                        messages.add_message(
                            self.request,
                            messages.SUCCESS,
                            _(u"Odeslána pozvánka uživateli %(user)s na email %(email)s") % {"user": invited_user_attendance, "email": email},
                            fail_silently=True)
                except models.User.DoesNotExist:
                    invitation_mail(self.user_attendance, email)
                    messages.add_message(self.request, messages.SUCCESS, _(u"Odeslána pozvánka na email %s") % email, fail_silently=True)

        invite_success_url = self.request.session.get('invite_success_url')
        self.request.session['invite_success_url'] = None
        return redirect(invite_success_url or self.success_url)


class UpdateTeam(UserAttendanceViewMixin, SuccessMessageMixin, UpdateView):
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
    # @user_attendance_has(lambda ua: ua.entered_competition(), _(u"Po vstupu do soutěže již nemůžete měnit parametry týmu."))
    def dispatch(self, request, *args, **kwargs):
        return super(UpdateTeam, self).dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.user_attendance.team


class TeamMembers(UserAttendanceViewMixin, TemplateView):
    template_name = 'registration/team_admin_members.html'
    registration_phase = "zmenit_tym"

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
                logger.error(u'Can\'t split POST approve parameter: %s' % (request))
                messages.add_message(request, messages.ERROR, mark_safe(_(u"Nastala chyba při přijímání uživatele, patrně používáte zastaralý internetový prohlížeč.")))

            if approve_id:
                approved_user = UserAttendance.objects.get(id=approve_id)
                userprofile = approved_user.userprofile
                if approved_user.approved_for_team not in ('undecided', 'denied') or not userprofile.user.is_active or approved_user.team != self.user_attendance.team:
                    logger.error(
                        u'Approving user with wrong parameters. User: %s (%s), approval: %s, team: %s, active: %s' %
                        (userprofile.user, userprofile.user.username, approved_user.approved_for_team, approved_user.team, userprofile.user.is_active))
                    messages.add_message(
                        request,
                        messages.ERROR,
                        mark_safe(_(
                            u"Tento uživatel již byl přijat do týmu. Pravděpodobně jste dvakrát odeslali formulář."
                        )),
                        extra_tags="user_attendance_%s" % approved_user.pk,
                        fail_silently=True)
                else:
                    approve_for_team(request, approved_user, request.POST.get('reason-' + str(approved_user.id), ''), action == 'approve', action == 'deny')
        return render(request, self.template_name, self.get_context_data())

    def get_context_data(self, *args, **kwargs):
        context_data = super(TeamMembers, self).get_context_data(*args, **kwargs)
        team = self.user_attendance.team
        if not team:
            return {'fullpage_error_message': _(u"Další členové vašeho týmu se zobrazí, jakmile budete mít vybraný tým")}

        unapproved_users = []
        for self.user_attendance in UserAttendance.objects.filter(team=team, userprofile__user__is_active=True):
            userprofile = self.user_attendance.userprofile
            unapproved_users.append([
                ('state', None, self.user_attendance.approved_for_team),
                ('id', None, str(self.user_attendance.id)),
                ('name', _(u"Jméno"), str(userprofile)),
                ('email', _(u"Email"), userprofile.user.email),
                ('payment_description', _(u"Platba"), self.user_attendance.get_payment_status_display()),
                ('telephone', _(u"Telefon"), userprofile.telephone),
                ('state_name', _(u"Stav"), str(self.user_attendance.get_approved_for_team_display())),
            ])
        context_data['unapproved_users'] = unapproved_users
        context_data['registration_phase'] = self.registration_phase
        return context_data


def distance(trips):
    return trips.filter(commute_mode__in=('bicycle', 'by_foot')).aggregate(Sum("distance"))['distance__sum'] or 0


def total_distance(campaign):
    return distance(Trip.objects.filter(user_attendance__campaign=campaign))


def period_distance(campaign, day_from, day_to):
    return distance(Trip.objects.filter(user_attendance__campaign=campaign, date__gte=day_from, date__lte=day_to))


def trips(trips):
    return trips.count()


def total_trips(campaign):
    return trips(Trip.objects.filter(user_attendance__campaign=campaign))


def period_trips(campaign, day_from, day_to):
    return trips(Trip.objects.filter(user_attendance__campaign=campaign, date__gte=day_from, date__lte=day_to))


@cache_page(60)  # noqa
def statistics(
        request,
        variable,
        template='registration/statistics.html'):
    campaign_slug = request.subdomain
    campaign = Campaign.objects.get(slug=campaign_slug)
    result = None
    if variable == 'ujeta-vzdalenost':
        result = total_distance(campaign)
    elif variable == 'ujeta-vzdalenost-dnes':
        result = period_distance(campaign, util.today(), util.today())
    elif variable == 'pocet-cest':
        result = total_trips(campaign)
    elif variable == 'pocet-cest-dnes':
        result = period_trips(campaign, util.today(), util.today())
    elif variable == 'pocet-zaplacenych':
        result = UserAttendance.objects.filter(
            Q(campaign=campaign) &
            Q(userprofile__user__is_active=True) &
            Q(transactions__status__in=models.Payment.done_statuses)
        ).exclude(Q(transactions__payment__pay_type__in=models.Payment.NOT_PAYING_TYPES)).distinct().count()
    elif variable == 'pocet-prihlasenych':
        result = UserAttendance.objects.filter(campaign=campaign, userprofile__user__is_active=True).distinct().count()
    elif variable == 'pocet-soutezicich':
        result = UserAttendance.objects.filter(
            Q(campaign=campaign) &
            Q(userprofile__user__is_active=True) &
            (Q(transactions__status__in=models.Payment.done_statuses) | Q(campaign__admission_fee=0))
        ).distinct().count()
    elif variable == 'pocet-spolecnosti':
        result = Company.objects.filter(Q(subsidiaries__teams__campaign=campaign)).distinct().count()
    elif variable == 'pocet-pobocek':
        result = Subsidiary.objects.filter(Q(teams__campaign=campaign)).distinct().count()

    if variable == 'pocet-soutezicich-firma':
        if request.user.is_authenticated() and util.is_competitor(request.user):
            result = UserAttendance.objects.filter(
                campaign=campaign,
                userprofile__user__is_active=True,
                approved_for_team='approved',
                team__subsidiary__company=models.get_company(campaign, request.user)
            ).count()
        else:
            result = "-"

    if result is None:
        return HttpResponse(_(u"Neznámá proměnná %s" % variable), status=403)

    return render(
        request,
        template,
        {
            'variable': result
        })


@cache_page(60)
def daily_chart(
        request,
        template='registration/daily-chart.html',):
    campaign_slug = request.subdomain
    campaign = Campaign.objects.get(slug=campaign_slug)
    values = [period_distance(campaign, day, day) for day in util.days(campaign)]
    return render(
        request,
        template,
        {
            'values': values,
            'days': reversed(util.days(campaign)),
            'max_value': max(values),
        })


@cache_page(60 * 60)
def daily_distance_json(
        request,):
    campaign_slug = request.subdomain
    campaign = Campaign.objects.get(slug=campaign_slug)
    values = collections.OrderedDict((str(day), period_distance(campaign, day, day)) for day in util.days(campaign))
    data = json.dumps(values)
    return HttpResponse(data)


class BikeRepairView(CreateView):
    template_name = 'base_generic_form.html'
    form_class = forms.BikeRepairForm
    success_url = 'bike_repair'
    success_message = _(u"%(user_attendance)s je nováček a právě si zažádal o opravu kola")
    model = models.CommonTransaction

    def get_initial(self):
        campaign = Campaign.objects.get(slug=self.request.subdomain)
        return {
            'campaign': campaign,
        }

    def form_valid(self, form):
        super(BikeRepairView, self).form_valid(form)
        return redirect(reverse(self.success_url))


class DrawResultsView(TemplateView):
    template_name = 'admin/draw.html'

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
