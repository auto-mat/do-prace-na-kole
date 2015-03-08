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
import httplib
import urllib
import hashlib
import datetime
import results
# Django imports
from django.shortcuts import render_to_response
from django.contrib import auth
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.decorators import method_decorator
from decorators import must_be_approved_for_team, must_be_competitor, must_have_team, user_attendance_has, request_condition
from django.contrib.auth.decorators import login_required as login_required_simple
from django.template import RequestContext
from django.db.models import Sum, Q
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat
from django.utils.safestring import mark_safe
from django.views.decorators.cache import cache_page, never_cache, cache_control
from django.views.generic.edit import FormView, UpdateView, CreateView
from django.views.generic.base import TemplateView
from class_based_auth_views.views import LoginView
# Registration imports
import registration.signals
import registration.backends
import registration.backends.simple
# Model imports
from models import UserProfile, Trip, Answer, Question, Team, Payment, Subsidiary, Company, Competition, Choice, City, UserAttendance, Campaign
import forms
from forms import RegistrationFormDPNK, RegistrationAccessFormDPNK, RegisterSubsidiaryForm, RegisterCompanyForm, RegisterTeamForm, ProfileUpdateForm, InviteForm, TeamAdminForm, PaymentTypeForm, ChangeTeamForm, TrackUpdateForm, WorkingScheduleForm
from django.conf import settings
from django.http import HttpResponse
from django import http
# Local imports
import util
import draw
from dpnk.email import approval_request_mail, register_mail, team_membership_approval_mail, team_membership_denial_mail, team_created_mail, invitation_mail, invitation_register_mail
from django.db import transaction

from wp_urls import wp_reverse
from unidecode import unidecode
from django.shortcuts import redirect
from django.core.urlresolvers import reverse, reverse_lazy
from string_lazy import mark_safe_lazy, format_lazy
import logging
import models
import tempfile
import shutil
import re
logger = logging.getLogger(__name__)


class DPNKLoginView(LoginView):
    def get_initial(self):
        initial_email = self.kwargs.get('initial_email')
        if initial_email:
            return {'username': self.kwargs['initial_email']}
        else:
            return {}


class UserAttendanceViewMixin(object):
    @method_decorator(login_required_simple)
    @must_be_competitor
    def dispatch(self, request, *args, **kwargs):
        self.url_name = request.resolver_match.url_name
        self.user_attendance = kwargs['user_attendance']
        return super(UserAttendanceViewMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context_data = super(UserAttendanceViewMixin , self).get_context_data(*args, **kwargs)
        return context_data

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super(UserAttendanceViewMixin , self).get_form_kwargs(*args, **kwargs)
        return form_kwargs

    def get_object(self):
        return self.user_attendance


class UserProfileRegistrationBackend(registration.backends.simple.SimpleBackend):
    def register(self, request, campaign, invitation_token, **cleaned_data):
        new_user = super(UserProfileRegistrationBackend, self).register(request, **cleaned_data)
        from dpnk.models import UserProfile

        new_user.save()

        userprofile = UserProfile(
            user=new_user,
            )
        userprofile.save()

        approve = False
        try:
            team = Team.objects.get(invitation_token=invitation_token)
            approve = True
        except Team.DoesNotExist:
            team = None
        user_attendance = UserAttendance(
            userprofile=userprofile,
            campaign=campaign,
            team=team,
            )
        user_attendance.save()
        if approve:
            approve_for_team(request, user_attendance, "", True, False)

        register_mail(user_attendance)
        return new_user


class RegistrationMessagesMixin(UserAttendanceViewMixin):
    def get(self, request, *args, **kwargs):
        ret_val = super(RegistrationMessagesMixin, self).get(request, *args, **kwargs)
        if self.user_attendance.team:
            if self.current_view not in ('upravit_profil',):
                if self.user_attendance.approved_for_team == 'undecided':
                    messages.warning(request, mark_safe(_(u"Vaše členství v týmu %(team)s čeká na vyřízení. Pokud to trvá příliš dlouho, můžete zkusit <a href='%(address)s'>znovu požádat o ověření členství</a>.") % {'team': self.user_attendance.team.name, 'address': reverse("zaslat_zadost_clenstvi")}))
                elif self.user_attendance.approved_for_team == 'denied':
                    messages.error(request, mark_safe(_(u'Vaše členství v týmu bylo bohužel zamítnuto, budete si muset <a href="%s">zvolit jiný tým</a>') % reverse('zmenit_tym')))
                elif len(self.user_attendance.team.unapproved_members()) > 0:
                    messages.warning(request, mark_safe(_(u'Ve vašem týmu jsou neschválení členové, prosíme, <a href="%s">posuďte jejich členství</a>.') % reverse('zmenit_tym')))
                if self.user_attendance.is_libero():
                    messages.warning(request, mark_safe(_(u'Jste sám v týmu, znamená to že budete moci soutěžit pouze v kategoriích určených pro jednotlivce! <ul><li><a href="%(invite_url)s">Pozvěte</a> své kolegy do vašeho týmu.</li><li>Můžete se pokusit <a href="%(join_team_url)s">přidat se k jinému týmu</a>.</li><li>Pokud nemůžete sehnat spolupracovníky, použijte seznamku.</li></ul>') % {'invite_url': reverse('pozvanky'), 'join_team_url': reverse('zmenit_tym')}))

        if self.user_attendance.payment_status() not in ('done', 'none',) and self.current_view not in ('typ_platby',):
            messages.info(request, mark_safe(_(u'Vaše platba typu %(payment_type)s ještě nebyla vyřízena. Můžete <a href="%(url)s">zadat novou platbu.</a>') % {'payment_type': self.user_attendance.payment_type_string(), 'url': reverse('platba')}))
        if self.current_view == 'working_schedule' and not self.user_attendance.entered_competition():
            messages.error(request, _(u'Před vstupem do soutěžního profilu musíte mít splněny všechny kroky registrace'))


        company_admin = self.user_attendance.is_company_admin()
        if company_admin and company_admin.company_admin_approved == 'undecided':
            messages.warning(request, _(u'Vaše žádost o funkci koordinátora společnosti čeká na vyřízení.'))
        if company_admin and company_admin.company_admin_approved == 'denied':
            messages.error(request, _(u'Vaše žádost o funkci koordinátora společnosti byla zamítnuta.'))
        return ret_val


class RegistrationViewMixin(RegistrationMessagesMixin, UserAttendanceViewMixin):
    template_name = 'base_generic_registration_form.html'

    def get_context_data(self, *args, **kwargs):
        context_data = super(RegistrationViewMixin, self).get_context_data(*args, **kwargs)
        context_data['title'] = self.title
        context_data['current_view'] = self.current_view
        context_data['user_attendance'] = self.user_attendance
        return context_data

    def get_success_url(self):
        if 'next' in self.request.POST:
            return reverse(self.next_url)
        else:
            return reverse(self.prev_url)


class ChangeTeamView(SuccessMessageMixin, RegistrationViewMixin, FormView):
    form_class = ChangeTeamForm
    template_name = 'registration/change_team.html'
    next_url = 'upravit_trasu'
    prev_url = 'upravit_profil'
    title = _(u'Změnit tým')
    current_view = "zmenit_tym"

    def get_context_data(self, *args, **kwargs):
        context_data = super(ChangeTeamView, self).get_context_data(*args, **kwargs)
        context_data['campaign_slug'] = self.user_attendance.campaign.slug
        return context_data

    @method_decorator(login_required_simple)
    @must_be_competitor
    #@user_attendance_has(lambda ua: ua.entered_competition(), _(u"Po vstupu do soutěže nemůžete měnit tým."))
    def dispatch(self, request, *args, **kwargs):
        return super(ChangeTeamView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        create_company = False
        create_subsidiary = False
        create_team = False

        form = self.form_class(data=request.POST, files=request.FILES, instance=self.user_attendance)

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
            form_team = RegisterTeamForm(prefix="team", initial={"campaign": self.user_attendance.campaign})
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
                messages.add_message(request, messages.SUCCESS, _(u"Společnost %s úspěšně vytvořena.") % company, fail_silently=True)
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

            messages.add_message(request, messages.SUCCESS, _(u"Údaje o týmu úspěšně nastaveny."), fail_silently=True)
            return redirect(self.get_success_url())
        form.fields['company'].widget.underlying_form = form_company
        form.fields['company'].widget.create = create_company

        form.fields['subsidiary'].widget.underlying_form = form_subsidiary
        form.fields['subsidiary'].widget.create = create_subsidiary

        form.fields['team'].widget.underlying_form = form_team
        form.fields['team'].widget.create = create_team

        context_data = self.get_context_data()
        context_data['form'] = form
        return render_to_response(self.template_name, context_data, context_instance=RequestContext(request))

    def get(self, request, *args, **kwargs):
        super(ChangeTeamView, self).get(request, *args, **kwargs)
        form = self.form_class(request, instance=self.user_attendance)
        form_company = RegisterCompanyForm(prefix="company")
        form_subsidiary = RegisterSubsidiaryForm(prefix="subsidiary", campaign=self.user_attendance.campaign)
        form_team = RegisterTeamForm(prefix="team", initial={"campaign": self.user_attendance.campaign})

        form.fields['company'].widget.underlying_form = form_company
        form.fields['subsidiary'].widget.underlying_form = form_subsidiary
        form.fields['team'].widget.underlying_form = form_team

        context_data = self.get_context_data()
        context_data['form'] = form
        return render_to_response(self.template_name, context_data, context_instance=RequestContext(request))


class RegistrationAccessView(FormView):
    template_name = 'base_generic_form.html'
    form_class = RegistrationAccessFormDPNK

    def form_valid(self, form):
        email = form.cleaned_data['email']
        campaign = Campaign.objects.get(slug=self.request.subdomain)
        user_exists = models.User.objects.filter(email=email).exists()
        if user_exists:
            return redirect(reverse('login', kwargs={'initial_email': email}))
        else:
            return redirect(reverse('registrace', kwargs={'initial_email': email}))


class RegistrationView(FormView):
    template_name = 'base_generic_form.html'
    form_class = RegistrationFormDPNK
    model = UserProfile
    success_url = 'upravit_profil'

    def get_initial(self):
        return {'email': self.kwargs.get('initial_email', '')}

    def form_valid(self, form, backend='dpnk.views.UserProfileRegistrationBackend'):
        campaign = Campaign.objects.get(slug=self.request.subdomain)
        super(RegistrationView, self).form_valid(form)
        backend = registration.backends.get_backend(backend)
        backend.register(self.request, campaign, self.kwargs.get('token', None), **form.cleaned_data)
        auth_user = auth.authenticate(
            username=self.request.POST['email'],
            password=self.request.POST['password1'])
        auth.login(self.request, auth_user)

        return redirect(reverse(self.success_url))


class ConfirmDeliveryView(UpdateView):
    template_name = 'base_generic_form.html'
    form_class = forms.ConfirmDeliveryForm
    success_url = 'profil'

    def form_valid(self, form):
        super(ConfirmDeliveryView, self).form_valid(form)
        return redirect(wp_reverse(self.success_url))

    def get_object(self):
        return self.user_attendance.package_shipped()

    @user_attendance_has(lambda ua: not ua.t_shirt_size.ship, _(u"Startovní balíček se neodesílá, pokud nechcete žádné tričko."))
    @user_attendance_has(lambda ua: not ua.package_shipped(), _(u"Startovní balíček ještě nebyl odeslán"))
    @user_attendance_has(lambda ua: ua.package_delivered(), _(u"Doručení startovního balíčku potvrzeno"))
    @must_be_competitor
    def dispatch(self, request, *args, **kwargs):
        return super(ConfirmDeliveryView, self).dispatch(request, *args, **kwargs)


class ConfirmTeamInvitationView(FormView):
    template_name = 'registration/team_invitation.html'
    form_class = forms.ConfirmTeamInvitationForm
    success_url = 'profil'

    def get_context_data(self, **kwargs):
        context = super(ConfirmTeamInvitationView, self).get_context_data(**kwargs)
        context['old_team'] = self.user_attendance.team
        context['new_team'] = self.new_team
        return context

    def form_valid(self, form):
        if form.cleaned_data['question']:
            self.user_attendance.team = self.new_team
            self.user_attendance.save()
            approve_for_team(self.request, self.user_attendance, "", True, False)
        return redirect(wp_reverse(self.success_url))

    @must_be_competitor
    @method_decorator(request_condition(lambda r, a, k: Team.objects.filter(invitation_token=k['token']).count() != 1, string_concat("<div class='text-warning'>", _(u"Tým nenalezen."), "</div>")))
    @method_decorator(request_condition(lambda r, a, k: r.user.email != k['initial_email'], string_concat("<div class='text-warning'>", _(u"Pozvánka je určena jinému uživateli, než je aktuálně přihlášen."), "</div>")))
    def dispatch(self, request, *args, **kwargs):
        self.user_attendance = kwargs['user_attendance']
        invitation_token = self.kwargs['token']
        self.new_team = Team.objects.get(invitation_token=invitation_token)

        if self.user_attendance.payment_status() == 'done' and self.user_attendance.team.subsidiary != self.new_team.subsidiary:
            return HttpResponse(_(u'<div class="text-error">Již máte zaplaceno, nemůžete měnit tým mimo svoji pobočku.</div>'), status=401)

        if self.user_attendance.campaign != self.new_team.campaign:
            return HttpResponse(_(u'<div class="text-error">Přihlašujete se do týmu ze špatné kampaně (pravděpodobně z minulého roku).</div>'), status=401)
        return super(ConfirmTeamInvitationView, self).dispatch(request, *args, **kwargs)


class PaymentTypeView(SuccessMessageMixin, RegistrationViewMixin, FormView):
    template_name = 'registration/payment_type.html'
    form_class = PaymentTypeForm
    title = _(u"Platba")
    current_view = "typ_platby"
    next_url = "working_schedule"
    prev_url = "upravit_triko"

    @method_decorator(login_required_simple)
    @must_have_team
    @user_attendance_has(lambda ua: ua.payment()['status'] == 'done', mark_safe_lazy(format_lazy(_(u"Již máte startovné zaplaceno. Pokračujte na <a href='{addr}'>pracovní rozvrh</a>."), addr=reverse_lazy("working_schedule"))))
    @user_attendance_has(lambda ua: ua.payment()['status'] == 'no_admission', mark_safe_lazy(format_lazy(_(u"Startovné se neplatí. Pokračujte na <a href='{addr}'>pracovní rozvrh</a>."), addr=reverse_lazy("working_schedule"))))
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
        context['aklub_url'] = settings.AKLUB_URL
        return context

    def get_form(self, form_class):
        form = super(PaymentTypeView, self).get_form(form_class)
        form.user_attendance = self.user_attendance
        return form

    def form_valid(self, form):
        payment_choices = {
            'member': {'type': 'am', 'message': _(u"Vaše členství v klubu přátel ještě bude muset být schváleno"), 'amount': 0},
            'member_wannabe': {'type': 'amw', 'message': _(u"Vaše členství v klubu přátel ještě bude muset být schváleno"), 'amount': 0},
            'free': {'type': 'fe', 'message': _(u"Váš nárok na startovné zdarma bude muset být ještě ověřen"), 'amount': 0},
            'company': {'type': 'fc', 'message': _(u"Platbu ještě musí schválit váš firemní koordinátor"), 'amount': self.user_attendance.company_admission_fee()},
            }
        payment_type = form.cleaned_data['payment_type']
        payment_choice = payment_choices[payment_type]

        if payment_type == 'pay':
            return redirect(reverse('platba'))
        elif payment_choice:
            Payment(user_attendance=self.user_attendance, amount=payment_choice['amount'], pay_type=payment_choice['type'], status=Payment.Status.NEW).save()
            messages.add_message(self.request, messages.WARNING, payment_choice['message'], fail_silently=True)
            logger.info('Inserting %s payment for %s' % (payment_type, self.user_attendance))

        return super(PaymentTypeView, self).form_valid(form)


@never_cache
@cache_control(max_age=0, no_cache=True, no_store=True)
def header_bar(request, campaign_slug):
    company_admin = None
    entered_competition = None
    campaign = Campaign.objects.get(slug=campaign_slug)
    if request.user.is_authenticated():
        company_admin = models.get_company_admin(request.user, campaign)
        try:
            entered_competition = models.UserAttendance.objects.get(campaign=campaign, userprofile__user=request.user).entered_competition
        except UserAttendance.DoesNotExist:
            entered_competition = None
    return render_to_response('registration/header_bar.html', {
        'is_authentificated': request.user.is_authenticated(),
        'company_admin': company_admin,
        'user': request.user,
        'entered_competition': entered_competition,
        'registration_phase_active': campaign.phase("registration").is_actual()
        }, context_instance=RequestContext(request))


class PaymentView(SuccessMessageMixin, RegistrationViewMixin, FormView):
    template_name = 'registration/payment.html'
    form_class = PaymentTypeForm
    title = _(u"Platba")
    current_view = "payment_type"
    next_url = "upravit_profil"
    prev_url = "upravit_triko"

    @must_have_team
    def dispatch(self, request, *args, **kwargs):
        return super(PaymentView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PaymentView, self).get_context_data(**kwargs)

        if self.user_attendance.payment()['status'] == 'no_admission':
            return redirect(wp_reverse('profil'))
        uid = self.request.user.id
        order_id = '%s-1' % uid
        session_id = "%sJ%d" % (order_id, int(time.time()))
        # Save new payment record
        p = Payment(session_id=session_id,
                    user_attendance=self.user_attendance,
                    order_id=order_id,
                    amount=self.user_attendance.admission_fee(),
                    status=Payment.Status.NEW,
                    description="Ucastnicky poplatek Do prace na kole")
        p.save()
        logger.info(u'Inserting payment with uid: %s, order_id: %s, session_id: %s, userprofile: %s (%s), status: %s' % (uid, order_id, session_id, self.user_attendance, self.user_attendance.userprofile.user.username, p.status))
        messages.add_message(self.request, messages.WARNING, _(u"Platba vytvořena, čeká se na její potvrzení"), fail_silently=True)
        # Render form
        profile = self.user_attendance.userprofile
        context['firstname'] = profile.user.first_name  # firstname
        context['surname'] = profile.user.last_name  # surname
        context['email'] = profile.user.email  # email
        context['amount'] = self.user_attendance.admission_fee()
        context['amount_hal'] = int(self.user_attendance.admission_fee() * 100)  # v halerich
        context['description'] = "Ucastnicky poplatek Do prace na kole"
        context['order_id'] = order_id
        context['client_ip'] = self.request.META['REMOTE_ADDR']
        context['session_id'] = session_id
        return context


class PaymentResult(RegistrationViewMixin, TemplateView):
    current_view = 'typ_platby'
    title = "Stav platby"
    template_name = 'registration/payment_result.html'

    @method_decorator(login_required_simple)
    def dispatch(self, request, *args, **kwargs):
        return super(PaymentResult, self).dispatch(request, *args, **kwargs)

    @transaction.atomic
    def get_context_data(self, success, trans_id, session_id, pay_type, error=None, user_attendance=None):
        context_data = super(PaymentResult, self).get_context_data()
        logger.info(u'Payment result: success: %s, trans_id: %s, session_id: %s, pay_type: %s, error: %s, user: %s (%s)' % (success, trans_id, session_id, pay_type, error, user_attendance, user_attendance.userprofile.user.username))

        if session_id and session_id != "":
            p = Payment.objects.select_for_update().get(session_id=session_id)
            if p.status not in Payment.done_statuses:
                if success:
                    p.status = Payment.Status.COMMENCED
                else:
                    p.status = Payment.Status.REJECTED
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
        return context_data


def make_sig(values):
    key1 = settings.PAYU_KEY_1
    return hashlib.md5("".join(values+(key1,))).hexdigest()


def check_sig(sig, values):
    key2 = settings.PAYU_KEY_2
    if sig != hashlib.md5("".join(values+(key2,))).hexdigest():
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
    c = httplib.HTTPSConnection("secure.payu.com")
    timestamp = str(int(time.time()))
    c.request("POST", "/paygw/UTF/Payment/get/txt/",
              urllib.urlencode({
                  'pos_id': pos_id,
                  'session_id': session_id,
                  'ts': timestamp,
                  'sig': make_sig((pos_id, session_id, timestamp))
                  }),
              {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"})
    raw_response = c.getresponse().read()
    r = {}
    for i in [i.split(':', 1) for i in raw_response.split('\n') if i != '']:
        r[i[0]] = i[1].strip()
    check_sig(r['trans_sig'], (r['trans_pos_id'], r['trans_session_id'], r['trans_order_id'],
                               r['trans_status'], r['trans_amount'], r['trans_desc'],
                               r['trans_ts']))
    # Update the corresponding payment
    # TODO: use update_or_create in Django 1.7
    p, created = Payment.objects.select_for_update().get_or_create(
        session_id=r['trans_session_id'],
        defaults={
            'order_id': r['trans_order_id'],
            'amount': int(r['trans_amount'])/100,
            'description': r['trans_desc'],
        })

    p.pay_type = r['trans_pay_type']
    p.status = r['trans_status']
    if r['trans_recv'] != '':
        p.realized = r['trans_recv']
    p.save()

    logger.info('Payment status: pay_type: %s, status: %s, payment response: %s' % (p.pay_type, p.status, r))

    # Return positive error code as per PayU protocol
    return http.HttpResponse("OK")


@login_required_simple
@must_be_competitor
def profile_access(request, user_attendance=None):
    if user_attendance.team:
        city_redirect = "/" + user_attendance.team.subsidiary.city.slug
    else:
        city_redirect = ""

    if user_attendance.team:
        city = user_attendance.team.subsidiary.city
    else:
        city = None

    return render_to_response('registration/profile_access.html', {
        'city': city,
        'city_redirect': city_redirect
        }, context_instance=RequestContext(request))


def trip_active_last7(day, today):
    return (
        (day <= today)
        and (day > today - datetime.timedelta(days=7))
        )


def trip_active_last_week(day, today):
    return (
            (day <= today)
        and (
            (
                day.isocalendar()[1] == today.isocalendar()[1])
            or
                (today.weekday() == 0 and day.isocalendar()[1]+1 == today.isocalendar()[1])
            )
        )

trip_active = trip_active_last7


class RidesView(UserAttendanceViewMixin, TemplateView):
    template_name='registration/rides.html'
    success_url="jizdy"

    @must_be_approved_for_team
    @user_attendance_has(lambda ua: not ua.entered_competition(), mark_safe_lazy(format_lazy(_(u"Vyplnit jízdy můžete až budete mít splněny všechny body <a href='{addr}'>registrace</a>."), addr=reverse_lazy("upravit_profil"))))
    @method_decorator(never_cache)
    @method_decorator(cache_control(max_age=0, no_cache=True, no_store=True))
    def dispatch(self, request, *args, **kwargs):
        return super(RidesView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        days = util.days(self.user_attendance.campaign)
        today = util.today()
        for day_m, date in enumerate(days):
            day = day_m + 1
            trip_to = request.POST.get('trip_to-' + str(day), 'off') == 'on'
            trip_from = request.POST.get('trip_from-' + str(day), 'off') == 'on'

            if not trip_active(date, today):
                continue
            trip, created = Trip.objects.get_or_create(
                user_attendance=self.user_attendance,
                date=date,
                defaults={
                    'trip_from': False,
                    'trip_to': False,
                },
            )

            trip.trip_to = trip_to
            trip.trip_from = trip_from
            trip.distance_to = max(min(float(request.POST.get('distance_to-' + str(day), 0)), 1000), 0)
            trip.distance_from = max(min(float(request.POST.get('distance_from-' + str(day), 0)), 1000), 0)
            logger.info(u'User %s filling in ride: day: %s, trip_from: %s, trip_to: %s, distance_from: %s, distance_to: %s, created: %s' % (
                request.user.username, trip.date, trip.trip_from, trip.trip_to, trip.distance_from, trip.distance_to, created))
            trip.dont_recalculate = True
            trip.save()

        results.recalculate_result_competitor(self.user_attendance)

        messages.add_message(request, messages.SUCCESS, _(u"Jízdy úspěšně vyplněny"), fail_silently=False)
        return render_to_response(self.template_name, self.get_context_data(), context_instance=RequestContext(request))

    def get_context_data(self, *args, **kwargs):
        days = util.days(self.user_attendance.campaign)
        today = util.today()
        trips = {}
        for t in Trip.objects.filter(user_attendance=self.user_attendance).select_related('user_attendance__campaign'):
            trips[t.date] = t
        calendar = []

        distance = 0
        trip_count = 0
        working_rides_count = 0
        default_distance = self.user_attendance.get_distance()
        for i, d in enumerate(days):
            if d in trips:
                working_rides_count += (1 if trips[d].is_working_ride_to else 0) + (1 if trips[d].is_working_ride_from else 0)
            cd = {}
            cd['day'] = d
            cd['trips_active'] = trip_active(d, today)
            if d in trips:
                cd['working_ride_to'] = trips[d].is_working_ride_to
                cd['working_ride_from'] = trips[d].is_working_ride_from
                cd['default_trip_to'] = trips[d].trip_to
                cd['default_trip_from'] = trips[d].trip_from
                cd['default_distance_to'] = default_distance if trips[d].distance_to is None else trips[d].distance_to
                cd['default_distance_from'] = default_distance if trips[d].distance_from is None else trips[d].distance_from
                trip_count += (1 if trips[d].is_working_ride_to and trips[d].trip_to else 0) + (1 if trips[d].is_working_ride_from and trips[d].trip_from else 0)
                if trips[d].trip_to and trips[d].distance_to:
                    distance += trips[d].distance_to_cutted()
                if trips[d].trip_from and trips[d].distance_from:
                    distance += trips[d].distance_from_cutted()
            else:
                cd['working_ride_to'] = False
                cd['working_ride_from'] = False
                cd['default_trip_to'] = False
                cd['default_trip_from'] = False
                cd['default_distance_to'] = default_distance
                cd['default_distance_from'] = default_distance
            cd['percentage'] = self.user_attendance.get_frequency_percentage(trip_count, working_rides_count)
            cd['percentage_str'] = "%.0f" % (cd['percentage'])
            cd['distance'] = distance
            calendar.append(cd)
        return {
            'calendar': calendar,
            'user_attendance': self.user_attendance,
            'minimum_percentage': self.user_attendance.campaign.minimum_percentage,
        }


@login_required_simple
@must_be_competitor
@never_cache
@cache_control(max_age=0, no_cache=True, no_store=True)
def profile(request, user_attendance=None, success_url='competition_profile'):
    if user_attendance.entered_competition():
        return redirect(wp_reverse(success_url))
    if request.POST and request.POST['enter_competition'] == 'true':
        user_action = models.UserActionTransaction(
            status=models.UserActionTransaction.Status.COMPETITION_START_CONFIRMED,
            user_attendance=user_attendance,
            realized=datetime.datetime.now(),
        )
        user_action.save()
        return redirect(wp_reverse(success_url))

    # Render profile
    payment_status = user_attendance.payment_status()
    if user_attendance.team:
        team_members_count = user_attendance.team.members().count()
    else:
        team_members_count = 0
    request.session['invite_success_url'] = 'profil'

    is_package_shipped = user_attendance.package_shipped() is not None
    is_package_delivered = user_attendance.package_delivered() is not None

    admissions_phase = user_attendance.campaign.phase("admissions")

    cant_enter_competition_reasons = {
        'no_personal_data': _(u"mít vyplněné osobní údaje"),  # Translators: Začít soutěžit bude moci až budete ...
        'no_team': _(u"mít vybraný tým"),  # Translators: Začít soutěžit bude moci až budete ...
        'not_approved_for_team': _(u"mít odsouhlasené členství v týmu"),  # Translators: Začít soutěžit bude moci až budete ...
        'unapproved_team_members': _(u"mít odsouhlasené všechny členy týmu"),  # Translators: Začít soutěžit bude moci až budete ...
        'not_enough_team_members': _(u"mít víc než jen jednoho člena týmu"),  # Translators: Začít soutěžit bude moci až budete ...
        'not_t_shirt': _(u"mít vyplněnou velikost trika"),  # Translators: Začít soutěžit bude moci až budete ...
        'not_paid': _(u"mít zaplaceno"),  # Translators: Začít soutěžit bude moci až budete ...
        True: 'can_enter',
    }
    cant_enter_competition_reason = cant_enter_competition_reasons[user_attendance.can_enter_competition()]

    try:
        competition_entry_phase = user_attendance.campaign.phase_set.get(type="compet_entry")
    except models.Phase.DoesNotExist:
        competition_entry_phase = None
    competition_entry_phase_is_active = competition_entry_phase and competition_entry_phase.is_actual()
    return render_to_response('registration/profile.html', {
        'active': user_attendance.userprofile.user.is_active,
        'superuser': request.user.is_superuser,
        'user': request.user,
        'profile': user_attendance,
        'team': user_attendance.team,
        'payment_status': payment_status,
        'payment_type': user_attendance.payment_type(),
        'team_members_count': team_members_count,
        'approved_for_team': user_attendance.approved_for_team,
        'is_package_shipped': is_package_shipped,
        'is_package_delivered': is_package_delivered,
        'admissions_phase': admissions_phase,
        'cant_enter_competition_reason': cant_enter_competition_reason,
        'competition_entry_active': competition_entry_phase_is_active,
        'campaign_slug': user_attendance.campaign.slug,
        }, context_instance=RequestContext(request))


class ProfileView(RegistrationViewMixin, TemplateView):
    title = 'Soutěžní profil'
    current_view = 'profile_view'
    template_name = 'registration/competition_profile.html'

    def get_context_data(self, *args, **kwargs):
        context_data = super(ProfileView, self).get_context_data(*args, **kwargs)
        import slumber
        api = slumber.API("http://www.cyklistesobe.cz/issues/")
        context_data['cyklistesobe'] = api.list.get(order="vote_count", count=1)
        return context_data


class UserAttendanceView(UserAttendanceViewMixin, TemplateView):
    pass

class PackageView(RegistrationViewMixin, TemplateView):
    template_name = "registration/package.html"
    title = _(u"Sledování balíčku")
    current_view = "zmenit_tym"


class OtherTeamMembers(UserAttendanceViewMixin, TemplateView):
    template_name='registration/team_members.html'

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
            team_members = self.user_attendance.team.all_members().select_related('userprofile__user', 'team__subsidiary__city', 'team__subsidiary__company', 'campaign', 'user_attendance')
        context_data['team_members'] = team_members
        context_data['current_view'] = "other_team_members"
        return context_data


class AdmissionsView(UserAttendanceViewMixin, TemplateView):
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
        if success_url is not None:
            return redirect(reverse(success_url))

    def get_context_data(self, *args, **kwargs):
        context_data = super(AdmissionsView, self).get_context_data(*args, **kwargs)
        competitions = self.user_attendance.get_competitions()
        for competition in competitions:
            competition.competitor_has_admission = competition.has_admission(self.user_attendance)
            competition.competitor_can_admit = competition.can_admit(self.user_attendance)
        context_data['competitions'] = competitions
        context_data['current_view'] = "competitions"
        return context_data


def competition_results(request, template, competition_slug, campaign_slug, limit=None):
    if limit == '':
        limit = None

    if request.user.is_anonymous():
        user_attendance = None
    else:
        user_attendance = request.user.userprofile.userattendance_set.get(campaign__slug=campaign_slug)

    try:
        competition = Competition.objects.get(slug=competition_slug)
    except Competition.DoesNotExist:
        logger.exception('Unknown competition slug %s, request: %s' % (competition_slug, request))
        return HttpResponse(_(u'<div class="text-error">Tuto soutěž v systému nemáme. Pokud si myslíte, že by zde měly být výsledky nějaké soutěže, napište prosím na <a href="mailto:kontakt@dopracenakole.net?subject=Neexistující soutěž">kontakt@dopracenakole.net</a></div>'), status=401)

    results = competition.get_results()
    if competition.competitor_type == 'single_user' or competition.competitor_type == 'libero':
        results = results.select_related('user_attendance__userprofile__user')
    elif competition.competitor_type == 'team':
        results = results.select_related('team__subsidiary__company')
    elif competition.competitor_type == 'company':
        results = results.select_related('company')

    return render_to_response(template, {
        'user_attendance': user_attendance,
        'competition': competition,
        'results': results[:limit]
        }, context_instance=RequestContext(request))


class UpdateProfileView(SuccessMessageMixin, RegistrationViewMixin, UpdateView):
    form_class = ProfileUpdateForm
    model = UserProfile
    success_message = _(u"Osobní údaje úspěšně upraveny")
    next_url = "zmenit_tym"
    current_view = "upravit_profil"
    title = _(u"Upravit profil")

    def get_object(self):
        return self.request.user.userprofile


class WorkingScheduleView(SuccessMessageMixin, RegistrationViewMixin, UpdateView):
    form_class = WorkingScheduleForm
    model = UserAttendance
    success_message = _(u"Pracovní kalendář úspěšně upraven")
    prev_url = 'typ_platby'
    next_url = 'profil'
    current_view = "working_schedule"
    title = _(u"Upravit pracovní kalendář")
    template_name = 'registration/working_schedule.html'

    def get_object(self):
        return self.user_attendance


class UpdateTrackView(SuccessMessageMixin, RegistrationViewMixin, UpdateView):
    template_name = 'registration/change_track.html'
    form_class = TrackUpdateForm
    model = UserAttendance
    success_message = _(u"Trasa/vzdálenost úspěšně upravena")
    next_url = 'zmenit_triko'
    prev_url = 'zmenit_tym'
    current_view = "upravit_trasu"
    title = _("Upravit trasu")

    def get_object(self):
        return self.user_attendance


class ChangeTShirtView(SuccessMessageMixin, RegistrationViewMixin, UpdateView):
    template_name = 'registration/change_tshirt.html'
    form_class = forms.TShirtUpdateForm
    model = UserAttendance
    success_message = _(u"Velikost trička úspěšně nastavena")
    next_url = 'typ_platby'
    prev_url = 'upravit_trasu'
    current_view = "zmenit_triko"
    title = _("Upravit velikost trika")

    def get_object(self):
        return self.user_attendance

    @method_decorator(login_required_simple)
    @user_attendance_has(lambda ua: ua.package_shipped(), _(u"Velikost trika nemůžete měnit, již bylo odesláno"))
    def dispatch(self, request, *args, **kwargs):
        return super(ChangeTShirtView, self).dispatch(request, *args, **kwargs)


def handle_uploaded_file(source, username):
    logger.info("Saving file: username: %s, filename: %s" % (username, source.name))
    fd, filepath = tempfile.mkstemp(suffix=u"_%s&%s" % (username, unidecode(source.name).replace(" ", "_")), dir=settings.MEDIA_ROOT + u"/questionaire")
    with open(filepath, 'wb') as dest:
        shutil.copyfileobj(source, dest)
    return u"questionaire/" + filepath.rsplit("/", 1)[1]


@login_required_simple
@must_be_competitor
def questionaire(
        request,
        questionaire_slug=None,
        template='registration/questionaire.html',
        user_attendance=None,
        success_url='profil',
        ):
    questionnaire = models.Competition.objects.get(slug=questionaire_slug)
    userprofile = request.user.get_profile()
    error = False
    empty_answer = False
    form_filled = False
    try:
        competition = Competition.objects.get(slug=questionaire_slug)
    except Competition.DoesNotExist:
        logger.exception('Unknown questionaire slug %s, request: %s' % (questionaire_slug, request))
        return HttpResponse(_(u'<div class="text-error">Tento dotazník v systému nemáme. Pokud si myslíte, že by zde mělo jít vyplnit dotazník, napište prosím na <a href="mailto:kontakt@dopracenakole.net?subject=Neexistující dotazník">kontakt@dopracenakole.net</a></div>'), status=401)
    questions = Question.objects.filter(competition=competition).order_by('order')
    if request.method == 'POST' and competition.can_admit(user_attendance):
        choice_ids = [(int(k.split('-')[1]), request.POST.getlist(k)) for k, v in request.POST.items() if k.startswith('choice')]
        comment_ids = [int(k.split('-')[1]) for k, v in request.POST.items() if k.startswith('comment')]
        fileupload_ids = [int(k.split('-')[1]) for k, v in request.FILES.items() if k.startswith('fileupload')]

        answers_dict = {}
        for question in questions:
            answer, created = Answer.objects.get_or_create(
                user_attendance=user_attendance,
                question=question)
            if not created:
                # Cleanup previous fillings
                answer.choices = []
            answer.save()
            answers_dict[question.id] = answer

        # Save choices
        for answer_id, choices_ids in choice_ids:
            for choice_id in choices_ids:
                choice = Choice.objects.get(id=choice_id)
                answer = answers_dict[answer_id]
                answer.choices.add(choice)
                answer.save()
        # Save comments
        for comment_id in comment_ids:
            answer = answers_dict[comment_id]  # comment_id = question_id
            answer.comment = request.POST.get('comment-%d' % comment_id, '')
            answer.save()
        # Save file uploads
        for fileupload_id in fileupload_ids:
            filehandler = request.FILES.get('fileupload-%d' % fileupload_id, None)
            if filehandler:
                answer = answers_dict[fileupload_id]
                answer.attachment = handle_uploaded_file(filehandler, request.user.username)
                answer.save()

        competition.make_admission(user_attendance)
        form_filled = True

    for question in questions:
        try:
            question.choices = Choice.objects.filter(choice_type=question.choice_type)
        except Choice.DoesNotExist:
            question.choices = None
        try:
            answer = Answer.objects.get(
                question=question,
                user_attendance=user_attendance)

            if question.type == 'choice' and answer.choices.count() == 0:
                error = True
                question.error = True

            question.comment_prefill = answer.comment
            question.points_given = answer.points_given
            question.attachment_prefill = answer.attachment
            question.attachment_prefill_name = re.sub(r"^.*&", "", answer.attachment.name).replace("_", " ")
            question.choices_prefill = [c.id for c in answer.choices.all()]
        except Answer.DoesNotExist:
            empty_answer = True
            question.comment_prefill = ''
            question.choices_prefill = ''

    if not error and not empty_answer and form_filled:
        return redirect(wp_reverse(success_url))

    return render_to_response(template, {
        'user': userprofile,
        'questions': questions,
        'questionaire': questionnaire,
        'media': settings.MEDIA_URL,
        'error': error,
        'is_actual': competition.is_actual(),
        'has_finished': competition.has_finished(),
        }, context_instance=RequestContext(request))


def questionnaire_answers_all(request, template, competition_slug, campaign_slug, limit=None):
    competition = Competition.objects.get(slug=competition_slug)
    if not request.user.is_superuser and hasattr(request.user, 'userprofile') and request.user.userprofile.competition_edition_allowed(competition):
        return HttpResponse(string_concat("<div class='text-warning'>", _(u"Soutěž je vypsána ve měste, pro které nemáte oprávnění."), "</div>"))
    if not competition.public_answers:
        return HttpResponse(string_concat("<div class='text-warning'>", _(u"Tato soutěž nemá povolené prohlížení odpovědí."), "</div>"))

    competitors = competition.get_results()

    for competitor in competitors:
        competitor.answers = Answer.objects.filter(
            user_attendance__in=competitor.user_attendances(),
            question__competition__slug=competition_slug)
    return render_to_response(template, {
        'competitors': competitors,
        'competition': competition,
        }, context_instance=RequestContext(request))


@staff_member_required
def questions(request):
    filter_query = Q()
    if not request.user.is_superuser:
        for administrated_city in request.user.userprofile.administrated_cities.all():
            filter_query |= (Q(competition__city=administrated_city.city) & Q(competition__campaign=administrated_city.campaign))
        # filter_query['competition__city__cityincampaign__in'] = request.user.userprofile.administrated_cities.all()
    questions = Question.objects.filter(filter_query).order_by('competition__campaign', 'competition__slug', 'order')
    return render_to_response('admin/questions.html', {
        'questions': questions
        }, context_instance=RequestContext(request))


@staff_member_required
def questionnaire_results(
        request,
        competition_slug=None,
        ):
    competition = Competition.objects.get(slug=competition_slug)
    if not request.user.is_superuser and request.user.userprofile.competition_edition_allowed(competition):
        return HttpResponse(string_concat("<div class='text-warning'>", _(u"Soutěž je vypsána ve měste, pro které nemáte oprávnění."), "</div>"))

    competitors = competition.get_results()
    return render_to_response('admin/questionnaire_results.html', {
        'competition_slug': competition_slug,
        'competitors': competitors,
        'competition': competition,
        }, context_instance=RequestContext(request))


@staff_member_required
def questionnaire_answers(
        request,
        competition_slug=None,
        ):
    competition = Competition.objects.get(slug=competition_slug)
    if not request.user.is_superuser and request.user.userprofile.competition_edition_allowed(competition):
        return HttpResponse(string_concat("<div class='text-warning'>", _(u"Soutěž je vypsána ve měste, pro které nemáte oprávnění."), "</div>"))

    try:
        competitor_result = competition.get_results().get(pk=request.GET['uid'])
    except:
        return HttpResponse(_(u'<div class="text-error">Nesprávně zadaný soutěžící.</div>'), status=401)
    answers = Answer.objects.filter(
        user_attendance__in=competitor_result.user_attendances(),
        question__competition__slug=competition_slug)
    total_points = competitor_result.result
    return render_to_response('admin/questionnaire_answers.html',
                              {'answers': answers,
                               'competitor': competitor_result,
                               'media': settings.MEDIA_URL,
                               'total_points': total_points
                               }, context_instance=RequestContext(request))


@staff_member_required
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
            stat[city].append((choice_names[k], v, float(v)/respondents[city]*100))
    for k, v in count_all.items():
        stat['Celkem'].append((choice_names[k], v, float(v)/total_respondents*100))

    def get_percentage(r):
        return r[2]
    for k in stat.keys():
        stat[k].sort(key=get_percentage, reverse=True)

    return render_to_response('admin/answers.html',
                              {'question': question,
                               'answers': answers,
                               'stat': stat,
                               'total_respondents': total_respondents,
                               'media': settings.MEDIA_URL,
                               'choice_names': choice_names
                               }, context_instance=RequestContext(request))


def approve_for_team(request, user_attendance, reason="", approve=False, deny=False):
    if deny:
        if not reason:
            messages.add_message(request, messages.ERROR, _(u"Při zamítnutí člena týmu musíte vyplnit zprávu."), extra_tags="user_attendance_%s" % user_attendance.pk, fail_silently=True)
            return
        user_attendance.approved_for_team = 'denied'
        user_attendance.save()
        team_membership_denial_mail(user_attendance, request.user, reason)
        messages.add_message(request, messages.SUCCESS, _(u"Členství uživatele %s ve vašem týmu bylo zamítnuto" % user_attendance), extra_tags="user_attendance_%s" % user_attendance.pk, fail_silently=True)
        return
    elif approve:
        if len(user_attendance.team.members()) >= settings.MAX_TEAM_MEMBERS:
            messages.add_message(request, messages.ERROR, _(u"Tým je již plný, další člen již nemůže být potvrzen."), extra_tags="user_attendance_%s" % user_attendance.pk, fail_silently=True)
            return
        user_attendance.approved_for_team = 'approved'
        user_attendance.save()
        team_membership_approval_mail(user_attendance)
        messages.add_message(request, messages.SUCCESS, _(u"Členství uživatele %(user)s v týmu %(team)s bylo odsouhlaseno.") % {"user": user_attendance, "team": user_attendance.team.name}, extra_tags="user_attendance_%s" % user_attendance.pk, fail_silently=True)
        return


class TeamApprovalRequest(RegistrationViewMixin, TemplateView):
    template_name = 'registration/request_team_approval.html'
    title = _(u"Znovu odeslat žádost o členství")
    current_view = "zmenit_tym"

    @method_decorator(login_required_simple)
    @must_be_competitor
    def dispatch(self, request, *args, **kwargs):
        return super(TeamApprovalRequest, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        approval_request_mail(self.user_attendance)
        return super(TeamApprovalRequest, self).form_valid(form)


class InviteView(RegistrationViewMixin, FormView):
    form_class = InviteForm
    title = _(u'Odeslat pozvánky dalším uživatelům')
    current_view = "zmenit_tym"
    success_url = reverse_lazy('zmenit_tym')

    @method_decorator(login_required_simple)
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
                        approve_for_team(request, invited_user_attendance, "", True, False)
                    else:
                        invitation_register_mail(self.user_attendance, invited_user_attendance)
                        messages.add_message(self.request, messages.SUCCESS, _(u"Odeslána pozvánka uživateli %(user)s na email %(email)s") % {"user": invited_user_attendance, "email": email}, fail_silently=True)
                except models.User.DoesNotExist:
                    invitation_mail(self.user_attendance, email)
                    messages.add_message(self.request, messages.SUCCESS, _(u"Odeslána pozvánka na email %s") % email, fail_silently=True)

        return redirect(self.request.session.get('invite_success_url') or self.success_url)


@must_be_competitor
@login_required_simple
#@user_attendance_has(lambda ua: ua.entered_competition(), string_concat("<div class='text-warning'>", _(u"Po vstupu do soutěže již nemůžete měnit parametry týmu."), "</div>"))
def team_admin_team(
        request,
        backend='registration.backends.simple.SimpleBackend',
        success_url=None,
        form_class=None,
        user_attendance=None,
        template_name='base_generic_form.html',
        extra_context=None):
    team = user_attendance.team
    form_class = TeamAdminForm

    if request.method == 'POST':
        form = form_class(data=request.POST, instance=team)
        if form.is_valid():
            form.save()
            return redirect(reverse(success_url))
    else:
        form = form_class(instance=team)

    return render_to_response(template_name, {
        'form': form,
        }, context_instance=RequestContext(request))



class TeamMembers(UserAttendanceViewMixin, TemplateView):
    template_name='registration/team_admin_members.html'

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super(TeamMembers, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if 'approve' in request.POST:
            action, approve_id = request.POST['approve'].split('-')
            approved_user = UserAttendance.objects.get(id=approve_id)
            userprofile = approved_user.userprofile
            if approved_user.approved_for_team not in ('undecided', 'denied') or not userprofile.user.is_active or approved_user.team != self.user_attendance.team:
                logger.error(u'Approving user with wrong parameters. User: %s (%s), approval: %s, team: %s, active: %s' % (userprofile.user, userprofile.user.username, approved_user.approved_for_team, approved_user.team, userprofile.user.is_active))
                messages.add_message(request, messages.ERROR, mark_safe(_(u"Nastala chyba, kvůli které nejde tento člen ověřit pro tým. Pokud problém přetrvává, prosím kontaktujte <a href='mailto:kontakt@dopracenakole.net?subject=Nejde ověřit člen týmu'>kontakt@dopracenakole.net</a>.")), extra_tags="user_attendance_%s" % approved_user.pk, fail_silently=True)
            else:
                approve_for_team(request, approved_user, request.POST.get('reason-' + str(approved_user.id), ''), action == 'approve', action == 'deny')
        return render_to_response(self.template_name, self.get_context_data(), context_instance=RequestContext(request))


    def get_context_data(self, *args, **kwargs):
        context_data = super(TeamMembers, self).get_context_data(*args, **kwargs)
        team = self.user_attendance.team
        if not team:
            return {'fullpage_error_message': _(u"Další členové vašeho týmu se zobrazí, jakmile budete mít vybraný tým")}
        if self.user_attendance.approved_for_team != 'approved':
            return {'fullpage_error_message': mark_safe(_(u"Vaše členství v týmu %(team)s nebylo odsouhlaseno. <a href='%(address)s'>Znovu požádat o ověření členství</a>.") % {'team': self.user_attendance.team.name, 'address': reverse("zaslat_zadost_clenstvi")})}

        unapproved_users = []
        for self.user_attendance in UserAttendance.objects.filter(team=team, userprofile__user__is_active=True):
            userprofile = self.user_attendance.userprofile
            unapproved_users.append([
                ('state', None, self.user_attendance.approved_for_team),
                ('id', None, str(self.user_attendance.id)),
                ('payment', None, self.user_attendance.payment()),
                ('name', _(u"Jméno"), unicode(userprofile)),
                ('email', _(u"Email"), userprofile.user.email),
                ('payment_description', _(u"Platba"), self.user_attendance.payment()['status_description']),
                ('telephone', _(u"Telefon"), userprofile.telephone),
                ('state_name', _(u"Stav"), unicode(self.user_attendance.get_approved_for_team_display())),
                ])
        context_data['unapproved_users'] = unapproved_users
        return context_data


def facebook_app(request):
    return render_to_response('registration/facebook_app.html', {'user': request.user})


def distance_length_competitions(trips):
    distance = 0
    distance += trips.filter(user_attendance__competitions__type='length', trip_from=True).aggregate(Sum("distance_from"))['distance_from__sum'] or 0
    distance += trips.filter(user_attendance__competitions__type='length', trip_to=True).aggregate(Sum("distance_to"))['distance_to__sum'] or 0
    return distance


def distance(trips):
    distance = 0
    # TODO: Fix calculation also for team length competitions.
    distance += trips.filter(user_attendance__competitions__type='length', trip_from=True).aggregate(Sum("distance_from"))['distance_from__sum'] or 0
    distance += trips.filter(user_attendance__competitions__type='length', trip_to=True).aggregate(Sum("distance_to"))['distance_to__sum'] or 0

    distance += trips.exclude(user_attendance__competitions__type='length').filter(trip_from=True).aggregate(Sum("user_attendance__distance"))['user_attendance__distance__sum'] or 0
    distance += trips.exclude(user_attendance__competitions__type='length').filter(trip_to=True).aggregate(Sum("user_attendance__distance"))['user_attendance__distance__sum'] or 0
    return distance


def total_distance(campaign):
    return distance(Trip.objects.filter(user_attendance__campaign=campaign))


def total_distance_length_competitions(campaign):
    return distance_length_competitions(Trip.objects.filter(user_attendance__campaign=campaign))


def period_distance(campaign, day_from, day_to):
    return distance(Trip.objects.filter(user_attendance__campaign=campaign, date__gte=day_from, date__lte=day_to))


def trips(trips):
    return trips.filter(trip_from=True).count() + trips.filter(trip_to=True).count()


def total_trips(campaign):
    return trips(Trip.objects.filter(user_attendance__campaign=campaign))


def period_trips(campaign, day_from, day_to):
    return trips(Trip.objects.filter(user_attendance__campaign=campaign, date__gte=day_from, date__lte=day_to))


@cache_page(60)
def statistics(
        request,
        variable,
        campaign_slug,
        template='registration/statistics.html'
        ):
    campaign = Campaign.objects.get(slug=campaign_slug)
    if variable == 'ujeta-vzdalenost':
        result = total_distance_length_competitions(campaign)
    if variable == 'ujeta-vzdalenost-vsechny-souteze':
        result = total_distance(campaign)
    elif variable == 'ujeta-vzdalenost-dnes':
        result = period_distance(campaign, util.today(), util.today())
    elif variable == 'pocet-cest':
        result = total_trips(campaign)
    elif variable == 'pocet-cest-dnes':
        result = period_trips(campaign, util.today(), util.today())
    elif variable == 'pocet-zaplacenych':
        result = UserAttendance.objects.filter(campaign=campaign, userprofile__user__is_active=True).filter(Q(transactions__status__in=models.Payment.done_statuses) | Q(team__subsidiary__city__cityincampaign__admission_fee=0)).distinct().count()
    elif variable == 'pocet-prihlasenych':
        result = UserAttendance.objects.filter(campaign=campaign, userprofile__user__is_active=True).distinct().count()
    elif variable == 'pocet-soutezicich':
        result = UserAttendance.objects.filter(campaign=campaign, transactions__useractiontransaction__status=models.UserActionTransaction.Status.COMPETITION_START_CONFIRMED).distinct().count()

    if variable == 'pocet-soutezicich-firma':
        if request.user.is_authenticated() and models.is_competitor(request.user):
            result = UserAttendance.objects.filter(campaign=campaign, userprofile__user__is_active=True, approved_for_team='approved', team__subsidiary__company=models.get_company(campaign, request.user)).count()
        else:
            result = "-"

    return render_to_response(template, {
        'variable': result
        }, context_instance=RequestContext(request))


@cache_page(60)
def daily_chart(
        request,
        campaign_slug,
        template='registration/daily-chart.html',
        ):
    campaign = Campaign.objects.get(slug=campaign_slug)
    values = [period_distance(campaign, day, day) for day in util.days(campaign)]
    return render_to_response(template, {
        'values': values,
        'days': reversed(util.days(campaign)),
        'max_value': max(values),
        }, context_instance=RequestContext(request))


class BikeRepairView(SuccessMessageMixin, CreateView):
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
        return redirect(wp_reverse(self.success_url))


def draw_results(
        request,
        competition_slug,
        template='admin/draw.html'
        ):
    return render_to_response(template, {
        'results': draw.draw(competition_slug),
        }, context_instance=RequestContext(request))
