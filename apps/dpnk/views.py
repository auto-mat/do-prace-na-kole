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
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib import auth
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.decorators import method_decorator
from decorators import must_be_approved_for_team, must_be_competitor, must_have_team, user_attendance_has, request_condition, must_be_in_phase
from django.contrib.auth.decorators import login_required as login_required_simple
from django.template import RequestContext
from django.db.models import Sum, Q
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat
from django.views.decorators.cache import cache_page, never_cache, cache_control
from django.views.generic.edit import FormView, UpdateView, CreateView
# Registration imports
import registration.signals
import registration.backends
import registration.backends.simple
# Model imports
from models import UserProfile, Trip, Answer, Question, Team, Payment, Subsidiary, Company, Competition, Choice, City, UserAttendance, Campaign
import forms
from forms import RegistrationFormDPNK, RegisterSubsidiaryForm, RegisterCompanyForm, RegisterTeamForm, ProfileUpdateForm, InviteForm, TeamAdminForm,  PaymentTypeForm, ChangeTeamForm, TrackUpdateForm
from django.conf import settings
from django.http import HttpResponse
from django import http
# Local imports
import util
import draw
from dpnk.email import approval_request_mail, register_mail, team_membership_approval_mail, team_membership_denial_mail, team_created_mail, invitation_mail, invitation_register_mail
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.models import get_current_site
from django.db import transaction

from wp_urls import wp_reverse
from unidecode import unidecode
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
import logging
import models
import tempfile
import shutil
import re
logger = logging.getLogger(__name__)


@never_cache
@cache_control(max_age=0, no_cache=True, no_store=True)
def login(request, template_name='registration/login.html',
          authentication_form=AuthenticationForm):
    redirect_to = wp_reverse("profil")
    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():
            auth.login(request, form.get_user())
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponse(redirect(request.POST["redirect_to"]))
    else:
        if "next" in request.GET:
            redirect_to = ""
        form = authentication_form(request)
    request.session.set_test_cookie()
    current_site = get_current_site(request)
    context = {
        'form': form,
        'site': current_site,
        'redirect_to': redirect_to,
        'django_url': settings.DJANGO_URL,
        'site_name': current_site.name,
    }
    return render_to_response(template_name, context, context_instance=RequestContext(request))


def logout_redirect(request):
    return HttpResponse(redirect(settings.LOGOUT_REDIRECT_URL))


class UserProfileRegistrationBackend(registration.backends.simple.SimpleBackend):
    def register(self, request, campaign, invitation_token, **cleaned_data):
        new_user = super(UserProfileRegistrationBackend, self).register(request, **cleaned_data)
        from dpnk.models import UserProfile

        new_user.first_name = cleaned_data['first_name']
        new_user.last_name = cleaned_data['last_name']
        new_user.save()

        userprofile = UserProfile(
            user=new_user,
            language=cleaned_data['language'],
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


class RegistrationViewMixin(object):
    template_name = 'base_generic_registration_form.html'

    def get_context_data(self, *args, **kwargs):
        context_data = super(RegistrationViewMixin, self).get_context_data(*args, **kwargs)
        context_data['title'] = self.title
        context_data['current_view'] = self.current_view
        context_data['submit_label'] = _(u"Další")

        self.user_attendance = get_object_or_404(UserAttendance, campaign__slug=self.kwargs['campaign_slug'], userprofile=self.request.user.userprofile)
        context_data['campaign_slug'] = self.kwargs['campaign_slug']
        context_data['profile_complete'] = self.request.user.userprofile.profile_complete()
        context_data['team_complete'] = self.user_attendance.team_complete()
        context_data['track_complete'] = self.user_attendance.track_complete()
        context_data['tshirt_complete'] = self.user_attendance.tshirt_complete()
        context_data['payment_complete'] = self.user_attendance.payment_complete()
        return context_data

    def get_success_url(self):
        return reverse(self.success_url, kwargs={'campaign_slug': self.kwargs['campaign_slug']})


class ChangeTeamView(SuccessMessageMixin, RegistrationViewMixin, FormView):
    form_class=ChangeTeamForm
    template_name='registration/change_team.html'
    success_url='upravit_trasu'
    title=_(u'Změnit tým')
    current_view = "zmenit_tym"

    @method_decorator(login_required_simple)
    @method_decorator(must_be_competitor)
    @method_decorator(user_attendance_has(lambda ua: ua.entered_competition(), string_concat("<div class='text-warning'>", _(u"Po vstupu do soutěže nemůžete měnit tým."), "</div>")))
    def dispatch(self, request, *args, **kwargs):
        self.user_attendance = kwargs['user_attendance']
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
                messages.add_message(request, messages.SUCCESS, _(u"Splečnost %s úspěšně vytvořena.") % company, fail_silently=True)
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
                self.success_url = "pozvanky"
                request.session['invite_success_url'] = 'upravit_trasu'

                team_created_mail(self.user_attendance)

            form.save()

            if team_changed and not create_team:
                self.user_attendance.approved_for_team = 'undecided'
                approval_request_mail(self.user_attendance)

            if self.user_attendance.approved_for_team != 'approved':
                approval_request_mail(self.user_attendance)

            messages.add_message(request, messages.SUCCESS, _(u"Údaje o týmu úspěšně nastaveny."), fail_silently=True)
            return redirect(reverse(self.success_url, kwargs={'campaign_slug': self.user_attendance.campaign.slug}))
        form.fields['company'].widget.underlying_form = form_company
        form.fields['company'].widget.create = create_company

        form.fields['subsidiary'].widget.underlying_form = form_subsidiary
        form.fields['subsidiary'].widget.create = create_subsidiary

        form.fields['team'].widget.underlying_form = form_team
        form.fields['team'].widget.create = create_team

        context_data = self.get_context_data()
        context_data['form'] = form
        context_data['campaign_slug'] = self.user_attendance.campaign.slug
        return render_to_response(self.template_name, context_data, context_instance=RequestContext(request))

    def get(self, request, *args, **kwargs):
        form = self.form_class(request, instance=self.user_attendance)
        form_company = RegisterCompanyForm(prefix="company")
        form_subsidiary = RegisterSubsidiaryForm(prefix="subsidiary", campaign=self.user_attendance.campaign)
        form_team = RegisterTeamForm(prefix="team", initial={"campaign": self.user_attendance.campaign})

        form.fields['company'].widget.underlying_form = form_company
        form.fields['subsidiary'].widget.underlying_form = form_subsidiary
        form.fields['team'].widget.underlying_form = form_team

        context_data = self.get_context_data()
        context_data['form'] = form
        context_data['campaign_slug'] = self.user_attendance.campaign.slug
        return render_to_response(self.template_name, context_data, context_instance=RequestContext(request))


class RegistrationView(FormView):
    template_name = 'base_generic_form.html'
    form_class = RegistrationFormDPNK
    model = UserProfile
    success_url = 'profil'

    def get_initial(self):
        return {'email': self.kwargs.get('initial_email', '')}

    def form_valid(self, form, backend='dpnk.views.UserProfileRegistrationBackend'):
        campaign = Campaign.objects.get(slug=self.kwargs['campaign_slug'])
        super(RegistrationView, self).form_valid(form)
        backend = registration.backends.get_backend(backend)
        backend.register(self.request, campaign, self.kwargs.get('token', None), **form.cleaned_data)
        auth_user = auth.authenticate(
            username=self.request.POST['username'],
            password=self.request.POST['password1'])
        auth.login(self.request, auth_user)

        return redirect(wp_reverse(self.success_url))


class ConfirmDeliveryView(UpdateView):
    template_name = 'base_generic_form.html'
    form_class = forms.ConfirmDeliveryForm
    success_url = 'profil'

    def form_valid(self, form):
        super(ConfirmDeliveryView, self).form_valid(form)
        return redirect(wp_reverse(self.success_url))

    def get_object(self):
        return self.user_attendance.package_shipped()

    @method_decorator(user_attendance_has(lambda ua: not ua.t_shirt_size.ship, string_concat("<div class='text-warning'>", _(u"Startovní balíček se neodesílá, pokud nechcete žádné tričko."), "</div>")))
    @method_decorator(user_attendance_has(lambda ua: not ua.package_shipped(), string_concat("<div class='text-warning'>", _(u"Startovní balíček ještě nebyl odeslán"), "</div>")))
    @method_decorator(user_attendance_has(lambda ua: ua.package_delivered(), string_concat("<div class='text-warning'>", _(u"Doručení startovního balíčku potvrzeno"), "</div>")))
    @method_decorator(must_be_competitor)
    def dispatch(self, request, *args, **kwargs):
        self.user_attendance = kwargs['user_attendance']
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

    @method_decorator(must_be_competitor)
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


@login_required_simple
@user_attendance_has(lambda ua: ua.payment()['status'] == 'done', string_concat("<div class='text-warning'>", _(u"Již máte startovné zaplaceno"), "</div>"))
@must_be_competitor
@must_have_team
def payment_type(request, user_attendance=None):
    if user_attendance.payment()['status'] == 'no_admission':
        return redirect(wp_reverse('profil'))
    template_name = 'registration/payment_type.html'
    form_class = PaymentTypeForm

    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES)
        if form.is_valid():
            if form.cleaned_data['payment_type'] == 'pay':
                return redirect(reverse('platba', kwargs={'campaign_slug': user_attendance.campaign.slug}))
            elif form.cleaned_data['payment_type'] == 'company':
                Payment(user_attendance=user_attendance, amount=0, pay_type='fc', status=Payment.Status.NEW).save()
                messages.add_message(request, messages.WARNING, _(u"Platbu ještě musí schválit váš firemní koordinátor"), fail_silently=True)
                logger.info('Inserting company payment for %s' % (user_attendance))
            elif form.cleaned_data['payment_type'] == 'member':
                Payment(user_attendance=user_attendance, amount=0, pay_type='am', status=Payment.Status.NEW).save()
                messages.add_message(request, messages.WARNING, _(u"Vaše členství v klubu přátel ještě bude muset být schváleno"), fail_silently=True)
                logger.info('Inserting automat club member payment for %s' % (user_attendance))

            return redirect(wp_reverse('profil'))
    else:
        form = form_class()

    return render_to_response(template_name, {
        'form': form,
        'campaign_slug': user_attendance.campaign.slug
        }, context_instance=RequestContext(request))


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


@login_required_simple
@user_attendance_has(lambda ua: ua.payment()['status'] == 'done', string_concat("<div class='text-warning'>", _(u"Již máte startovné zaplaceno"), "</div>"))
@must_be_competitor
@must_have_team
def payment(request, user_attendance=None):
    if user_attendance.payment()['status'] == 'no_admission':
        return redirect(wp_reverse('profil'))
    uid = request.user.id
    order_id = '%s-1' % uid
    session_id = "%sJ%d" % (order_id, int(time.time()))
    # Save new payment record
    p = Payment(session_id=session_id,
                user_attendance=user_attendance,
                order_id=order_id,
                amount=user_attendance.admission_fee(),
                status=Payment.Status.NEW,
                description="Ucastnicky poplatek Do prace na kole")
    p.save()
    logger.info(u'Inserting payment with uid: %s, order_id: %s, session_id: %s, userprofile: %s (%s), status: %s' % (uid, order_id, session_id, user_attendance, user_attendance.userprofile.user.username, p.status))
    messages.add_message(request, messages.WARNING, _(u"Platba vytvořena, čeká se na její potvrzení"), fail_silently=True)
    # Render form
    profile = UserProfile.objects.get(user=request.user)
    return render_to_response('registration/payment.html', {
        'firstname': profile.user.first_name,  # firstname
        'surname': profile.user.last_name,  # surname
        'email': profile.user.email,  # email
        'amount': p.amount,
        'amount_hal': p.amount * 100,  # v halerich
        'description': p.description,
        'order_id': p.order_id,
        'client_ip': request.META['REMOTE_ADDR'],
        'session_id': session_id
        }, context_instance=RequestContext(request))


@login_required_simple
@transaction.atomic
def payment_result(request, success, trans_id, session_id, pay_type, error=None):
    logger.info(u'Payment result: success: %s, trans_id: %s, session_id: %s, pay_type: %s, error: %s, user: %s (%s)' % (success, trans_id, session_id, pay_type, error, request.user, request.user.username))

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

    if success:
        msg = _(u"Vaše platba byla úspěšně zadána. Až platbu obdržíme, dáme vám vědět.")
    else:
        msg = _(u"Vaše platba se nezdařila. Po přihlášení do svého profilu můžete zadat novou platbu.")

    return render_to_response('registration/payment_result.html', {
        'pay_type': pay_type,
        'message': msg,
        }, context_instance=RequestContext(request))


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

trip_active = trip_active_last_week


@login_required_simple
@must_be_competitor
@must_be_approved_for_team
@user_attendance_has(lambda ua: not ua.entered_competition(), string_concat("<div class='text-warning'>", _(u"Vyplnit jízdy můžete až po vstupu do soutěže."), "</div>"))
@never_cache
@cache_control(max_age=0, no_cache=True, no_store=True)
def rides(
        request, user_attendance=None, template='registration/rides.html',
        success_url=""):
    days = util.days(user_attendance.campaign)
    today = util.today()

    if request.method == 'POST':
        for day_m, date in enumerate(days):
            day = day_m + 1
            trip_to = request.POST.get('trip_to-' + str(day), 'off') == 'on'
            trip_from = request.POST.get('trip_from-' + str(day), 'off') == 'on'

            if not trip_active(date, today):
                continue
            trip, created = Trip.objects.get_or_create(
                user_attendance=user_attendance,
                date=date,
                defaults={
                    'trip_from': False,
                    'trip_to': False,
                },
            )

            trip.trip_to = trip_to
            trip.trip_from = trip_from
            if trip.trip_to:
                try:
                    trip.distance_to = max(min(float(request.POST.get('distance_to-' + str(day), None)), 1000), 0)
                except:
                    pass
            else:
                trip.distance_to = None
            if trip.trip_from:
                try:
                    trip.distance_from = max(min(float(request.POST.get('distance_from-' + str(day), None)), 1000), 0)
                except:
                    pass
            else:
                trip.distance_from = None
            logger.info(u'User %s filling in ride: day: %s, trip_from: %s, trip_to: %s, distance_from: %s, distance_to: %s, created: %s' % (
                request.user.username, trip.date, trip.trip_from, trip.trip_to, trip.distance_from, trip.distance_to, created))
            trip.dont_recalculate = True
            trip.save()

        results.recalculate_result_competitor(user_attendance)

        messages.add_message(request, messages.SUCCESS, _(u"Jízdy úspěšně vyplněny"), fail_silently=False)
        if success_url is not None:
            return redirect(wp_reverse(success_url))

    trips = {}
    for t in Trip.objects.filter(user_attendance=user_attendance).select_related('user_attendance__campaign'):
        trips[t.date] = t
    calendar = []

    distance = 0
    trip_count = 0
    for i, d in enumerate(days):
        cd = {}
        cd['day'] = d
        cd['trips_active'] = trip_active(d, today)
        if d in trips:
            cd['default_trip_to'] = trips[d].trip_to
            cd['default_trip_from'] = trips[d].trip_from
            cd['default_distance_to'] = "0" if trips[d].distance_to is None else trips[d].distance_to
            cd['default_distance_from'] = "0" if trips[d].distance_from is None else trips[d].distance_from
            trip_count += int(trips[d].trip_to) + int(trips[d].trip_from)
            if trips[d].distance_to:
                distance += trips[d].distance_to_cutted()
            if trips[d].distance_from:
                distance += trips[d].distance_from_cutted()
        else:
            cd['default_trip_to'] = False
            cd['default_trip_from'] = False
            cd['default_distance_to'] = "0"
            cd['default_distance_from'] = "0"
        cd['percentage'] = float(trip_count)/(2*(i+1))*100
        cd['percentage_str'] = "%.0f" % (cd['percentage'])
        cd['distance'] = distance
        calendar.append(cd)
    return render_to_response(template, {
        'calendar': calendar,
        'has_distance_competition': user_attendance.has_distance_competition(),
        'user_attendance': user_attendance,
        }, context_instance=RequestContext(request))


@login_required_simple
@must_be_competitor
@never_cache
@cache_control(max_age=0, no_cache=True, no_store=True)
def profile(request, user_attendance=None, success_url = 'competition_profile'):
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


@login_required_simple
@must_be_competitor
def user_attendance_view(request, user_attendance=None, template=None):
    return render_to_response(template, {
        'user_attendance': user_attendance,
        }, context_instance=RequestContext(request))


@login_required_simple
@must_be_competitor
@must_be_approved_for_team
@never_cache
@cache_control(max_age=0, no_cache=True, no_store=True)
def other_team_members(
        request, userprofile=None, user_attendance=None,
        template='registration/team_members.html'
        ):
    team_members = []
    if user_attendance.team:
        team_members = user_attendance.team.all_members().select_related('userprofile__user', 'team__subsidiary__city', 'team__subsidiary__company', 'campaign', 'user_attendance')

    return render_to_response(template, {
        'team_members': team_members,
        }, context_instance=RequestContext(request))


@login_required_simple
@must_be_competitor
@never_cache
@cache_control(max_age=0, no_cache=True, no_store=True)
def admissions(
        request, template, user_attendance=None,
        success_url="",
        ):
    if request.method == 'POST':
        if 'admission_competition_id' in request.POST and request.POST['admission_competition_id']:
            competition = Competition.objects.get(id=request.POST['admission_competition_id'])
            competition.make_admission(user_attendance, True)
        if 'cancellation_competition_id' in request.POST and request.POST['cancellation_competition_id']:
            competition = Competition.objects.get(id=request.POST['cancellation_competition_id'])
            competition.make_admission(user_attendance, False)
        if success_url is not None:
            return redirect(wp_reverse(success_url))

    competitions = user_attendance.get_competitions()
    for competition in competitions:
        competition.competitor_has_admission = competition.has_admission(user_attendance)
        competition.competitor_can_admit = competition.can_admit(user_attendance)

    return render_to_response(template, {
        'competitions': competitions,
        'user_attendance': user_attendance,
        }, context_instance=RequestContext(request))


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
        return HttpResponse(_(u'<div class="text-error">Tuto soutěž v systému nemáme. Pokud si myslíte, že by zde měly být výsledky nějaké soutěže, napište prosím na kontakt@dopracenakole.net</div>'), status=401)

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
    success_url = "zmenit_tym"
    current_view = "upravit_profil"
    title = _("Upravit profil")

    def get_object(self):
        return self.request.user.userprofile


class UpdateTrackView(SuccessMessageMixin, RegistrationViewMixin, UpdateView):
    template_name = 'registration/change_track.html'
    form_class = TrackUpdateForm
    model = UserAttendance
    success_message = _(u"Trasa/vzdálenost úspěšně upravena")
    success_url = 'zmenit_triko'
    current_view = "upravit_trasu"
    title = _("Upravit trasu")

    def get_object(self):
        return get_object_or_404(UserAttendance, campaign__slug=self.kwargs['campaign_slug'], userprofile=self.request.user.userprofile)


class ChangeTShirtView(SuccessMessageMixin, RegistrationViewMixin, UpdateView):
    template_name = 'base_generic_registration_form.html'

    form_class = forms.TShirtUpdateForm
    model = UserAttendance
    success_message = _(u"Velikost trička úspěšně nastavena")
    success_url = 'typ_platby'
    current_view = "zmenit_triko"
    title = _("Upravit velikost trika")

    def get_object(self):
        return get_object_or_404(UserAttendance, campaign__slug=self.kwargs['campaign_slug'], userprofile=self.request.user.userprofile)

    @method_decorator(login_required_simple)
    @method_decorator(user_attendance_has(lambda ua: ua.package_shipped(), string_concat("<div class='text-warning'>", _(u"Velikost trika nemůžete měnit, již bylo odesláno"), "</div>")))
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
        return HttpResponse(_(u'<div class="text-error">Tento dotazník v systému nemáme. Pokud si myslíte, že by zde mělo jít vyplnit dotazník, napište prosím na kontakt@dopracenakole.net</div>'), status=401)
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
        query = {}
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
        #filter_query['competition__city__cityincampaign__in'] = request.user.userprofile.administrated_cities.all()
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


@must_be_competitor
@login_required_simple
def team_approval_request(request, user_attendance=None):
    approval_request_mail(user_attendance)
    return render_to_response('registration/request_team_approval.html',
                              context_instance=RequestContext(request))


@must_be_competitor
@login_required_simple
def invite(
        request,
        backend='registration.backends.simple.SimpleBackend',
        success_url=None,
        form_class=None,
        template_name='base_generic_form.html',
        user_attendance=None,
        extra_context=None):
    form_class = InviteForm

    if 'invite_success_url' in request.session:
        success_url = request.session.get('invite_success_url')

    if request.method == 'POST':
        form = form_class(data=request.POST)
        if form.is_valid():
            emails = [form.cleaned_data['email1'], form.cleaned_data['email2'], form.cleaned_data['email3'], form.cleaned_data['email4']]

            for email in emails:
                if email:
                    try:
                        invited_user = models.User.objects.get(is_active=True, email=email)

                        invited_user_attendance, created = UserAttendance.objects.get_or_create(
                            userprofile=invited_user.userprofile,
                            campaign=user_attendance.campaign,
                            )

                        if invited_user_attendance.team == user_attendance.team:
                            approve_for_team(request, invited_user_attendance, "", True, False)
                        else:
                            invitation_register_mail(user_attendance, invited_user_attendance)
                            messages.add_message(request, messages.SUCCESS, _(u"Odeslána pozvánka uživateli %(user)s na email %(email)s") % {"user": invited_user_attendance, "email": email}, fail_silently=True)
                    except models.User.DoesNotExist:
                        invitation_mail(user_attendance, email)
                        messages.add_message(request, messages.SUCCESS, _(u"Odeslána pozvánka na email %s") % email, fail_silently=True)

            return redirect(reverse(success_url, kwargs={'campaign_slug': user_attendance.campaign.slug}))
    else:
        form = form_class()
    return render_to_response(template_name, {
        'form': form,
        }, context_instance=RequestContext(request))


@must_be_competitor
@login_required_simple
@user_attendance_has(lambda ua: ua.entered_competition(), string_concat("<div class='text-warning'>", _(u"Po vstupu do soutěže již nemůžete měnit parametry týmu."), "</div>"))
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
            return redirect(reverse(success_url, kwargs={'campaign_slug': user_attendance.campaign.slug}))
    else:
        form = form_class(instance=team)

    return render_to_response(template_name, {
        'form': form,
        }, context_instance=RequestContext(request))


@must_be_competitor
@login_required_simple
def team_admin_members(
        request,
        backend='registration.backends.simple.SimpleBackend',
        template_name='registration/team_admin_members.html',
        user_attendance=None,
        extra_context=None):
    team = user_attendance.team
    unapproved_users = []

    if 'button_action' in request.POST and request.POST['button_action']:
        b_action = request.POST['button_action'].split('-')
        user_attendance = UserAttendance.objects.get(id=b_action[1])
        userprofile = user_attendance.userprofile
        if user_attendance.approved_for_team not in ('undecided', 'denied') or user_attendance.team != team or not userprofile.user.is_active:
            logger.error(u'Approving user with wrong parameters. User: %s (%s), approval: %s, team: %s, active: %s' % (userprofile.user, userprofile.user.username, user_attendance.approved_for_team, user_attendance.team, userprofile.user.is_active))
            messages.add_message(request, messages.ERROR, _(u"Nastala chyba, kvůli které nejde tento člen ověřit pro tým. Pokud problém přetrvává, prosím kontaktujte kontakt@dopracenakole.net."), fail_silently=True)
        else:
            approve_for_team(request, user_attendance, request.POST.get('reason-' + str(user_attendance.id), ''), b_action[0] == 'approve', b_action[0] == 'deny')

    for user_attendance in UserAttendance.objects.filter(team=team, userprofile__user__is_active=True):
        userprofile = user_attendance.userprofile
        unapproved_users.append([
            ('state', None, user_attendance.approved_for_team),
            ('id', None, str(user_attendance.id)),
            ('payment', None, user_attendance.payment()),
            ('name', _(u"Jméno"), unicode(userprofile)),
            ('username', _(u"Uživatel"), userprofile.user),
            ('email', _(u"Email"), userprofile.user.email),
            ('payment_description', _(u"Platba"), user_attendance.payment()['status_description']),
            ('telephone', _(u"Telefon"), userprofile.telephone),
            ('state_name', _(u"Stav"), unicode(user_attendance.get_approved_for_team_display())),
            ])

    return render_to_response(template_name, {
        'unapproved_users': unapproved_users,
        }, context_instance=RequestContext(request))


def facebook_app(request):
    return render_to_response('registration/facebook_app.html', {'user': request.user})


def distance_length_competitions(trips):
    distance = 0
    distance += trips.filter(user_attendance__competitions__type='length', trip_from=True).aggregate(Sum("distance_from"))['distance_from__sum'] or 0
    distance += trips.filter(user_attendance__competitions__type='length', trip_to=True).aggregate(Sum("distance_to"))['distance_to__sum'] or 0
    return distance


def distance(trips):
    distance = 0
    #TODO: Fix calculation also for team length competitions.
    distance += trips.filter(user_attendance__competitions__type='length', trip_from=True).aggregate(Sum("distance_from"))['distance_from__sum'] or 0
    distance += trips.filter(user_attendance__competitions__type='length', trip_to=True).aggregate(Sum("distance_to"))['distance_to__sum'] or 0

    distance += trips.exclude(user_attendance__competitions__type='length').filter(trip_from = True).aggregate(Sum("user_attendance__distance"))['user_attendance__distance__sum'] or 0
    distance += trips.exclude(user_attendance__competitions__type='length').filter(trip_to = True).aggregate(Sum("user_attendance__distance"))['user_attendance__distance__sum'] or 0
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
    variables = {}
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
        result= UserAttendance.objects.filter(campaign=campaign, transactions__useractiontransaction__status=models.UserActionTransaction.Status.COMPETITION_START_CONFIRMED).distinct().count()

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
        campaign = Campaign.objects.get(slug=self.kwargs['campaign_slug'])
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
