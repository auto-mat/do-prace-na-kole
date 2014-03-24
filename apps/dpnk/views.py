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
import time, httplib, urllib, hashlib, datetime
# Django imports
from django.shortcuts import render_to_response, get_object_or_404
import django.contrib.auth
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.decorators import method_decorator
from decorators import must_be_coordinator, must_be_approved_for_team, must_be_competitor, login_required_simple, must_have_team, user_attendance_has
from django.template import RequestContext
from django.db.models import Sum, Q
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_page
from django.views.generic.edit import FormView, UpdateView, CreateView
# Registration imports
import registration.signals, registration.backends, registration.backends.simple
# Model imports
from models import UserProfile, Trip, Answer, Question, Team, Payment, Subsidiary, Company, Competition, Choice, City, UserAttendance, Campaign
import forms
from forms import RegistrationFormDPNK, RegisterSubsidiaryForm, RegisterCompanyForm, RegisterTeamForm, ProfileUpdateForm, InviteForm, TeamAdminForm,  PaymentTypeForm, ChangeTeamForm
from django.conf import settings
from  django.http import HttpResponse
from django import http
# Local imports
import util, draw
from dpnk.email import approval_request_mail, register_mail, team_membership_approval_mail, team_membership_denial_mail, team_created_mail, invitation_mail
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.models import get_current_site
from django.contrib.auth import login as auth_login

from wp_urls import wp_reverse
from unidecode import unidecode
from util import redirect
import logging
import models
import tempfile
import shutil
import re
logger = logging.getLogger(__name__)

def login(request, template_name='registration/login.html',
          authentication_form=AuthenticationForm):
    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponse(redirect(wp_reverse(settings.LOGIN_REDIRECT_VIEW)))
    else:
        form = authentication_form(request)
    request.session.set_test_cookie()
    current_site = get_current_site(request)
    context = {
        'form': form,
        'site': current_site,
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

        userprofile = UserProfile(user = new_user,
                    language = cleaned_data['language'],
                    )
        userprofile.save()

        approved_for_team = 'undecided'
        try:
            team = Team.objects.get(invitation_token=invitation_token)
            approved_for_team = 'approved'
        except Team.DoesNotExist:
            team = None
        user_attendance = UserAttendance(userprofile = userprofile,
                    campaign = campaign,
                    team = team,
                    approved_for_team = approved_for_team,
                    )
        user_attendance.save()

        register_mail(user_attendance)
        return new_user

@login_required_simple
@must_be_competitor
def change_team(request,
             success_url=None, form_class=ChangeTeamForm,
             template_name='registration/change_team.html',
             user_attendance=None,
             extra_context=None,
             ):
    create_company = False
    create_subsidiary = False
    create_team = False

    team_member_count = UserAttendance.objects.filter(team=user_attendance.team, userprofile__user__is_active=True).exclude(approved_for_team='denied').count()
    if user_attendance.team and user_attendance.team.coordinator_campaign == user_attendance and team_member_count > 1:
        return HttpResponse(_(u'<div class="text-error">Jako koordinátor týmu nemůžete měnit svůj tým. Napřed musíte <a href="%s">zvolit jiného koordinátora</a>.</div>' % wp_reverse('team_admin')), status=401)

    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES, instance=user_attendance)

        form_company = RegisterCompanyForm(request.POST, prefix = "company")
        form_subsidiary = RegisterSubsidiaryForm(request.POST, prefix = "subsidiary", campaign=user_attendance.campaign)
        form_team = RegisterTeamForm(request.POST, prefix = "team")
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
            form_company = RegisterCompanyForm(prefix = "company")
            form.fields['company'].required = True

        if create_subsidiary:
            subsidiary_valid = form_subsidiary.is_valid()
            form.fields['subsidiary'].required = False
        else:
            form_subsidiary = RegisterSubsidiaryForm(prefix = "subsidiary", campaign=user_attendance.campaign)
            form.fields['subsidiary'].required = True

        if create_team:
            team_valid = form_team.is_valid()
            form.fields['team'].required = False
        else:
            form_team = RegisterTeamForm(prefix = "team")
            form.fields['team'].required = True
        old_team = user_attendance.team

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
                team.campaign = user_attendance.campaign
                form_team.save()
                messages.add_message(request, messages.SUCCESS, _(u"Tým %s úspěšně vytvořen.") % team.name, fail_silently=True)
            else:
                team = form.cleaned_data['team']

            if create_team:
                team = form_team.save(commit=False)

                if hasattr(user_attendance, 'coordinated_team'):
                    coordinated_team_members = UserAttendance.objects.exclude(id=user_attendance.id).filter(team=user_attendance.coordinated_team, userprofile__user__is_active=True)
                    if len(coordinated_team_members)>0:
                        user_attendance.coordinated_team.coordinator = coordinated_team_members[0]
                    else:
                        user_attendance.coordinated_team.coordinator = None
                    user_attendance.coordinated_team.save()

                user_attendance.team = team
                user_attendance.approved_for_team = 'approved'
                team.coordinator = user_attendance

                form_team.save()

                user_attendance.team = team
                success_url = "pozvanky"
                request.session['invite_success_url'] = 'profil'

                team_created_mail(user_attendance)

            form.save()

            if team_changed and not create_team:
                user_attendance.approved_for_team = 'undecided'
                approval_request_mail(user_attendance)

            if user_attendance.approved_for_team != 'approved':
                approval_request_mail(user_attendance)

            messages.add_message(request, messages.SUCCESS, _(u"Údaje o týmu úspěšně nastaveny."), fail_silently=True)
            return redirect(wp_reverse(success_url))
    else:
        form = form_class(request, instance=user_attendance)
        form_company = RegisterCompanyForm(prefix = "company")
        form_subsidiary = RegisterSubsidiaryForm(prefix = "subsidiary", campaign=user_attendance.campaign)
        form_team = RegisterTeamForm(prefix = "team")

    form.fields['company'].widget.underlying_form = form_company
    form.fields['company'].widget.create = create_company

    form.fields['subsidiary'].widget.underlying_form = form_subsidiary
    form.fields['subsidiary'].widget.create = create_subsidiary

    form.fields['team'].widget.underlying_form = form_team
    form.fields['team'].widget.create = create_team

    return render_to_response(template_name,
                              {'form': form,
                               }, context_instance=RequestContext(request))


class RegistrationView(FormView):
    template_name = 'generic_form_template.html'
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
        auth_user = django.contrib.auth.authenticate(
            username=self.request.POST['username'],
            password=self.request.POST['password1'])
        django.contrib.auth.login(self.request, auth_user)

        return redirect(wp_reverse(self.success_url))


@login_required_simple
@user_attendance_has(lambda ua: ua.payment()['status'] == 'done', "<div class='text-warning'>Již máte startovné zaplaceno</div>")
@must_be_competitor
@must_have_team
def payment_type(request, user_attendance=None):
    if user_attendance.payment()['status'] == 'no_admission':
        return redirect(wp_reverse('profil'))
    template_name='registration/payment_type.html'
    form_class = PaymentTypeForm

    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES)
        if form.is_valid():
            if form.cleaned_data['payment_type'] == 'pay':
                return redirect(wp_reverse('platba'))
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

    return render_to_response(template_name,
                              {'form': form
                               }, context_instance=RequestContext(request))


def header_bar(request, campaign_slug):
    user_attendance = None
    company_admin = None
    try:
        if request.user.is_authenticated():
            user_attendance = request.user.userprofile.userattendance_set.get(campaign__slug=campaign_slug)
            company_admin = models.get_company_admin(user_attendance.userprofile.user, user_attendance.campaign)
    except UserAttendance.DoesNotExist:
        pass
    return render_to_response('registration/header_bar.html',
                              {
            'is_authentificated': request.user.is_authenticated(),
            'company_admin': company_admin,
            'user_attendance': user_attendance,
             }, context_instance=RequestContext(request))



@login_required_simple
@user_attendance_has(lambda ua: ua.payment()['status'] == 'done', "<div class='text-warning'>Již máte startovné zaplaceno</div>")
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
                order_id = order_id,
                amount = user_attendance.admission_fee(),
                status=Payment.Status.NEW,
                description = "Ucastnicky poplatek Do prace na kole")
    p.save()
    logger.info('Inserting payment with uid: %s, order_id: %s, session_id: %s, userprofile: %s, status: %s' % (uid, order_id, session_id, user_attendance, p.status))
    messages.add_message(request, messages.WARNING, _(u"Platba vytvořena, čeká se na její potvrzení"), fail_silently=True)
    # Render form
    profile = UserProfile.objects.get(user=request.user)
    return render_to_response('registration/payment.html',
                              {
            'firstname': profile.user.first_name, # firstname
            'surname': profile.user.last_name, # surname
            'email': profile.user.email, # email
            'amount': p.amount,
            'amount_hal': p.amount * 100, # v halerich
            'description' : p.description,
            'order_id' : p.order_id,
            'client_ip': request.META['REMOTE_ADDR'],
            'session_id': session_id
             }, context_instance=RequestContext(request))

def payment_result(request, success, trans_id, session_id, pay_type, error = None):
    logger.info('Payment result: success: %s, trans_id: %s, session_id: %s, pay_type: %s, error: %s, user: %s' % (success, trans_id, session_id, pay_type, error, request.user))

    if session_id and session_id != "":
        p = Payment.objects.get(session_id=session_id)
        if p.status == Payment.Status.NEW:
            p.trans_id = trans_id
            p.pay_type = pay_type
            if success:
                p.status = Payment.Status.COMMENCED
            else:
                p.status = Payment.Status.REJECTED
            p.error = error
            p.save()

    if success == True:
        msg = _(u"Vaše platba byla úspěšně zadána. Až platbu obdržíme, dáme vám vědět.")
    else:
        msg = _(u"Vaše platba se nezdařila. Po přihlášení do svého profilu můžete zadat novou platbu.")

    return render_to_response('registration/payment_result.html',
                              {
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
    for i in [i.split(':',1) for i in raw_response.split('\n') if i != '']:
        r[i[0]] = i[1].strip()
    check_sig(r['trans_sig'], (r['trans_pos_id'], r['trans_session_id'], r['trans_order_id'],
                               r['trans_status'], r['trans_amount'], r['trans_desc'],
                               r['trans_ts']))
    # Update the corresponding payment
    try:
        p = Payment.objects.get(session_id=r['trans_session_id'])
    except Payment.DoesNotExist:
        p = Payment(order_id=r['trans_order_id'], session_id=r['trans_session_id'],
                    amount=int(r['trans_amount'])/100, description=r['trans_desc'])

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

    return render_to_response('registration/profile_access.html',
                              {
            'city_redirect': city_redirect
            }, context_instance=RequestContext(request))


def trip_active(day, today):
    return ((day <= today)
        and (day > today - datetime.timedelta(days=14))
    )

@login_required_simple
@must_be_competitor
@must_be_approved_for_team
def rides(request, user_attendance=None, template='registration/rides.html',
        success_url="profil"):
    days = util.days()
    today = util.today()

    if request.method == 'POST':
        if 'day' in request.POST and request.POST["day"]:
            day = int(request.POST["day"])
            date = days[day-1]
            if not trip_active(date, today):
                logger.error(u'User %s is trying to fill in nonactive day %s (%s), POST: %s' % (user_attendance, day, date, request.POST))
                return HttpResponse(_(u'<div class="text-error">Den %s již není možné vyplnit.</div>' % date), status=401)
            trip, created = Trip.objects.get_or_create(user = request.user.get_profile(),
                date = date)

            trip.trip_to = request.POST.get('trip_to-' + str(day), 'off') == 'on'
            trip.trip_from = request.POST.get('trip_from-' + str(day), 'off') == 'on'
            if trip.trip_to:
                try:
                    trip.distance_to = int(request.POST.get('distance_to-' + str(day), None))
                except:
                    trip.distance_to = 0
            else:
                trip.distance_to = None
            if trip.trip_from:
                try:
                    trip.distance_from = int(request.POST.get('distance_from-' + str(day), None))
                except:
                    trip.distance_from = 0
            else:
                trip.distance_from = None
            logger.info(u'User %s filling in ride: day: %s, trip_from: %s, trip_to: %s, distance_from: %s, distance_to: %s, created: %s' %
                (request.user.username, trip.date, trip.trip_from, trip.trip_to, trip.distance_from, trip.distance_to, created))
            trip.save()

            return redirect(wp_reverse(success_url))

    trips = {}
    for t in Trip.objects.filter(user_attendance=user_attendance):
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
            cd['default_distance_to'] = "" if trips[d].distance_to == None else trips[d].distance_to
            cd['default_distance_from'] = "" if trips[d].distance_from == None else trips[d].distance_from
            trip_count += int(trips[d].trip_to) + int(trips[d].trip_from)
            if trips[d].distance_to:
                distance += trips[d].distance_to
            if trips[d].distance_from:
                distance += trips[d].distance_from
        else:
            cd['default_trip_to'] = False
            cd['default_trip_from'] = False
            cd['default_distance_to'] = "0"
            cd['default_distance_from'] = "0"
        cd['percentage'] = float(trip_count)/(2*(i+1))*100
        cd['percentage_str'] = "%.0f" % (cd['percentage'])
        cd['distance'] = distance
        calendar.append(cd)
    return render_to_response(template,
                              {
            'calendar': calendar,
            'has_distance_competition': user_attendance.has_distance_competition(),
            }, context_instance=RequestContext(request))

@login_required_simple
@must_be_competitor
def profile(request, user_attendance=None):

    # Render profile
    payment_status = user_attendance.payment_status()
    if user_attendance.team and user_attendance.team.coordinator_campaign:
        team_members_count = user_attendance.team.members().count()
    else:
        team_members_count = 0
    request.session['invite_success_url'] = 'profil'

    is_package_shipped = user_attendance.package_shipped() != None
    return render_to_response('registration/profile.html',
                              {
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
def other_team_members(request, userprofile=None, user_attendance=None,
        template = 'registration/team_members.html'
        ):
    campaign = user_attendance.campaign

    team_members = []
    if user_attendance.team and user_attendance.team.coordinator_campaign:
        team_members = user_attendance.team.all_members(campaign)

    return render_to_response(template,
                              {
            'team_members': team_members,
            }, context_instance=RequestContext(request))

@login_required_simple
@must_be_competitor
@must_be_approved_for_team
def admissions(request, template, user_attendance=None,
        success_url="souteze",
        ):
    if request.method == 'POST':
        if 'admission_competition_id' in request.POST and request.POST['admission_competition_id']:
            competition = Competition.objects.get(id=request.POST['admission_competition_id'])
            competition.make_admission(user_attendance, True)
        if 'cancellation_competition_id' in request.POST and request.POST['cancellation_competition_id']:
            competition = Competition.objects.get(id=request.POST['cancellation_competition_id'])
            competition.make_admission(user_attendance, False)
        return redirect(wp_reverse(success_url))

    competitions = user_attendance.get_competitions()
    for competition in competitions:
        competition.competitor_has_admission = competition.has_admission(user_attendance)
        competition.competitor_can_admit = competition.can_admit(user_attendance)

    return render_to_response(template,
                              {
            'competitions': competitions,
            'user_attendance': user_attendance,
            }, context_instance=RequestContext(request))

@cache_page(24 * 60 * 60)
def competition_results(request, template, competition_slug, campaign_slug, limit=None):
    if limit == '':
        limit = None

    #if request.user.is_anonymous():
    #    userprofile = None
    #else:
    #    userprofile = request.user.get_profile()

    try:
        competition = Competition.objects.get(slug=competition_slug)
    except Competition.DoesNotExist:
        logger.error('Unknown competition slug %s, request: %s' % (competition_slug, request))
        return HttpResponse(_(u'<div class="text-error">Tuto soutěž v systému nemáme. Pokud si myslíte, že by zde měly být výsledky nějaké soutěže, napište prosím na kontakt@dopracenakole.net</div>'), status=401)


    return render_to_response(template,
                              {
            #'userprofile': userprofile,
            'competition': competition,
            'results': competition.get_results()[:limit],
            }, context_instance=RequestContext(request))


class UpdateProfileView(SuccessMessageMixin, UpdateView):
    template_name = 'generic_form_template.html'
    form_class = ProfileUpdateForm
    model = UserAttendance
    success_message = _(u"Osobní údaje úspěšně upraveny")
    success_url = 'profil'

    def get_object(self):
        return get_object_or_404(UserAttendance, campaign__slug=self.kwargs['campaign_slug'], userprofile=self.request.user.userprofile)

    def form_valid(self, form):
        super(UpdateProfileView, self).form_valid(form)
        return redirect(wp_reverse(self.success_url))


class ChangeTShirtView(SuccessMessageMixin, UpdateView):
    template_name = 'generic_form_template.html'
    form_class = forms.TShirtUpdateForm
    model = UserAttendance
    success_message = _(u"Velikost trička úspěšně nastavena")
    success_url = 'profil'

    def get_object(self):
        return get_object_or_404(UserAttendance, campaign__slug=self.kwargs['campaign_slug'], userprofile=self.request.user.userprofile)

    def form_valid(self, form):
        super(ChangeTShirtView, self).form_valid(form)
        return redirect(wp_reverse(self.success_url))

    @method_decorator(login_required_simple)
    @method_decorator(user_attendance_has(lambda ua: ua.package_shipped(), "<div class='text-warning'>Velikost trika nemůžete měnit, již bylo odesláno</div>"))
    def dispatch(self, request, *args, **kwargs):
        return super(ChangeTShirtView, self).dispatch(request, *args, **kwargs)


def handle_uploaded_file(source, username):
    logger.info("Saving file: username: %s, filenmae: %s" % (username, source.name))
    fd, filepath = tempfile.mkstemp(suffix=u"_%s&%s" % (username, unidecode(source.name).replace(" ", "_")), dir=settings.MEDIA_ROOT + u"/questionaire")
    with open(filepath, 'wb') as dest:
        shutil.copyfileobj(source, dest)
    return u"questionaire/" + filepath.rsplit("/", 1)[1]

@login_required_simple
@must_be_approved_for_team
def questionaire(request, questionaire_slug = None,
        template = 'registration/questionaire.html',
        user_attendance = None,
        success_url = 'profil',
        ):
    userprofile = request.user.get_profile()
    error = False
    empty_answer = False
    form_filled = False
    try:
        competition = Competition.objects.get(slug=questionaire_slug)
    except Competition.DoesNotExist:
        logger.error('Unknown questionaire slug %s, request: %s' % (questionaire_slug, request))
        return HttpResponse(_(u'<div class="text-error">Tento dotazník v systému nemáme. Pokud si myslíte, že by zde mělo jít vyplnit dotazník, napište prosím na kontakt@dopracenakole.net</div>'), status=401)
    questions = Question.objects.filter(competition=competition).order_by('order')
    if request.method == 'POST' and competition.can_admit(user_attendance) == True:
        choice_ids = [(int(k.split('-')[1]), request.POST.getlist(k)) for k, v in request.POST.items() if k.startswith('choice')]
        comment_ids = [int(k.split('-')[1]) for k, v in request.POST.items() if k.startswith('comment')]
        fileupload_ids = [int(k.split('-')[1]) for k, v in request.FILES.items() if k.startswith('fileupload')]

        answers_dict = {}
        for question in questions:
            answer, created = Answer.objects.get_or_create(
                    user = request.user.get_profile(),
                    question = question)
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
            answer = answers_dict[comment_id] # comment_id = question_id
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

    return render_to_response(template,
                              {'user': userprofile,
                               'questions': questions,
                               'questionaire': questionaire_slug,
                               'media': settings.MEDIA_URL,
                               'error': error,
                               'is_actual': competition.is_actual(),
                               'has_finished': competition.has_finished(),
                               }, context_instance=RequestContext(request))

@staff_member_required
def questions(request):
    questions = Question.objects.all().order_by('competition', 'date', 'order')
    return render_to_response('admin/questions.html',
                              {'questions': questions
                               }, context_instance=RequestContext(request))

@staff_member_required
def questionnaire_results(request,
                competition_slug = None,
                  ):
    competitors = Competition.objects.get(slug = competition_slug).get_results()
    return render_to_response('admin/questionnaire_results.html',
                               {
                               'competition_slug': competition_slug,
                               'competitors': competitors,
                               }, context_instance=RequestContext(request))

@staff_member_required
def questionnaire_answers(request,
                competition_slug = None,
                  ):
    competition = Competition.objects.get(slug = competition_slug)
    competitor = competition.get_results().get(pk = request.GET['uid'])
    if competition.competitor_type == 'single_user' or competition.competitor_type == 'libero':
        userprofile = [competitor.userprofile]
    elif competition.competitor_type == 'team':
        userprofile = competitor.team.members
    answers = Answer.objects.filter(user__in=userprofile,
                                 question__competition__slug=competition_slug)
    total_points = competitor.result
    return render_to_response('admin/questionnaire_answers.html',
                              {'answers': answers,
                               'competitor': competitor,
                               'media': settings.MEDIA_URL,
                               'total_points': total_points
                               }, context_instance=RequestContext(request))


@staff_member_required
def answers(request):
    question_id = request.GET['question']
    question = Question.objects.get(id=question_id)

    if request.method == 'POST':
        points = [(k.split('-')[1], v) for k, v in request.POST.items() if k.startswith('points-')]
        for p in points:
            if not p[1] in ('', 'None', None):
                answer = Answer.objects.get(id=p[0])
                answer.points_given = int(p[1])
                answer.save()

    answers = Answer.objects.filter(question_id=question_id)
    total_respondents = len(answers)
    count = dict((c, {}) for c in City.objects.all())
    count_all = {}
    respondents = dict((c, 0) for c in City.objects.all())
    choice_names = {}

    for a in answers:
        a.city = a.user_attendance.team.subsidiary.city


    if question.type in ('choice', 'multiple-choice'):
        for a in answers:
            respondents[a.city] += 1
            for c in a.choices.all():
                try:
                    count[a.city][c.id] += 1;
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

def approve_for_team(user_attendance, reason, approve=False, deny=False):
    if deny:
        if not reason:
            return 'no_message'
        user_attendance.approved_for_team = 'denied'
        user_attendance.save()
        team_membership_denial_mail(user_attendance.userprofile.user, reason)
        return 'denied'
    elif approve:
        if len(user_attendance.team.members()) >= 5:
            return 'team_full'
        user_attendance.approved_for_team = 'approved'
        user_attendance.save()
        user_approved = True
        team_membership_approval_mail(user_attendance.userprofile.user)
        return 'approved'

@must_be_competitor
@login_required_simple
def team_approval_request(request, user_attendance=None):
    approval_request_mail(user_attendance)
    return render_to_response('registration/request_team_approval.html',
                              context_instance=RequestContext(request))

@must_be_coordinator
@login_required_simple
def invite(request, backend='registration.backends.simple.SimpleBackend',
             success_url=None, form_class=None,
             template_name = 'generic_form_template.html',
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
                #try:
                #    invited_user = User.objects.get(email=email)

                #    if hasattr(invited_user, "userprofile") and invited_user.userprofile.userattendance_set.filter(campaign=user_attendance.campaign).count() == 0:
                #        invited_user_attendance = UserAttendance(userprofile = invited_user.userprofile,
                #                    campaign = user_attendance.campaign,
                #                    team = user_attendance.team,
                #                    approved_for_team = 'approved',
                #                    )
                #        invited_user_attendance.save()

                #        invitation_register_mail(user_attendance, invited_user_attendance)
                #    else:
                #        invitation_mail(user_attendance, email)
                #except User.DoesNotExist:
                invitation_mail(user_attendance, email)

            return redirect(wp_reverse(success_url))
    else:
        form = form_class()
    return render_to_response(template_name,
                              {'form': form,
                              }, context_instance=RequestContext(request))

@must_be_coordinator
@login_required_simple
def team_admin_team(request, backend='registration.backends.simple.SimpleBackend',
             success_url=None, form_class=None,
             user_attendance=None,
             template_name = 'generic_form_template.html',
             extra_context=None):
    team = user_attendance.team
    form_class = TeamAdminForm

    if request.method == 'POST':
        form = form_class(data=request.POST, instance = team)
        if form.is_valid():
            form.save()
            return redirect(wp_reverse(success_url))
    else:
        form = form_class(instance = team)

    return render_to_response(template_name,
                              {'form': form,
                                }, context_instance=RequestContext(request))

@must_be_coordinator
@login_required_simple
def team_admin_members(request, backend='registration.backends.simple.SimpleBackend',
             template_name='registration/team_admin_members.html',
             user_attendance=None,
             extra_context=None):
    team = user_attendance.team
    unapproved_users = []
    denial_message = 'unapproved'

    if 'button_action' in request.POST and request.POST['button_action']:
        b_action = request.POST['button_action'].split('-')
        user_attendance = UserAttendance.objects.get(id=b_action[1])
        userprofile = user_attendance.userprofile
        if user_attendance.approved_for_team not in ('undecided', 'denied') or user_attendance.team != team or not userprofile.user.is_active:
            logger.error('Approving user with wrong parameters. User: %s, approval: %s, team: %s, active: %s' % (userprofile.user, user_attendance.approved_for_team, user_attendance.team, userprofile.user.is_active))
            denial_message = 'cannot_approve'
        else:
            denial_message = approve_for_team(user_attendance, request.POST.get('reason-' + str(user_attendance.id), ''), b_action[0] == 'approve', b_action[0] == 'deny')

    for user_attendance in UserAttendance.objects.filter(team = team, userprofile__user__is_active=True):
        userprofile = user_attendance.userprofile
        unapproved_users.append([
            ('state', None, user_attendance.approved_for_team),
            ('id', None, user_attendance.id),
            ('payment', None, user_attendance.payment()),
            ('name', _(u"Jméno"), unicode(userprofile)),
            ('username', _(u"Uživatel"), userprofile.user),
            ('email', _(u"Email"), userprofile.user.email),
            ('payment_description', _(u"Platba"), user_attendance.payment()['status_description']),
            ('telephone', _(u"Telefon"), userprofile.telephone),
            ('state_name', _(u"Stav"), unicode(user_attendance.get_approved_for_team_display())),
            ])

    return render_to_response(template_name,
                              {
                               'unapproved_users': unapproved_users,
                                'denial_message': denial_message,
                                }, context_instance=RequestContext(request))

def facebook_app(request):
    return render_to_response('registration/facebook_app.html', {'user': request.user})

def distance(trips):
    distance = 0
    distance += trips.filter(trip_from = True).aggregate(Sum("distance_from"))['distance_from__sum'] or 0
    distance += trips.filter(trip_to = True).aggregate(Sum("distance_to"))['distance_to__sum'] or 0

    #TODO: Distance 0 shouldn't be counted, but due to bug in first two days of season 2013 competition it has to be.
    #distance += trips.filter(distance_from = None, trip_from = True).aggregate(Sum("user__distance"))['user__distance__sum']
    #distance += trips.filter(distance_to = None, trip_to = True).aggregate(Sum("user__distance"))['user__distance__sum']
    distance += trips.filter(Q(distance_from = None) | Q(distance_from = 0), trip_from = True).aggregate(Sum("user_attendance__distance"))['user_attendance__distance__sum'] or 0
    distance += trips.filter(Q(distance_to = None) | Q(distance_to = 0), trip_to = True).aggregate(Sum("user_attendance__distance"))['user_attendance__distance__sum'] or 0
    return distance

def total_distance():
    return distance(Trip.objects)

def period_distance(day_from, day_to):
    return distance(Trip.objects.filter(date__gte=day_from, date__lte=day_to))

def statistics(request,
        variable,
        campaign_slug,
        template = 'registration/statistics.html'
        ):

    campaign = Campaign.objects.get(slug=campaign_slug)
    variables = {}
    variables['ujeta-vzdalenost'] = total_distance()
    variables['ujeta-vzdalenost-dnes'] = period_distance(util.today(), util.today())
    variables['pocet-soutezicich'] = UserAttendance.objects.filter(campaign=campaign, userprofile__user__is_active = True, approved_for_team='approved').count()

    if request.user.is_authenticated() and models.is_competitor(request.user):
        variables['pocet-soutezicich-firma'] = UserAttendance.objects.filter(campaign=campaign, userprofile__user__is_active = True, approved_for_team='approved', team__subsidiary__company = models.get_company(campaign, request.user)).count()
    else:
        variables['pocet-soutezicich-firma'] = "-"

    return render_to_response(template,
            {
                'variable': variables[variable],
            }, context_instance=RequestContext(request))

@cache_page(24 * 60 * 60)
def daily_chart(request, campaign_slug,
        template = 'registration/daily-chart.html'
        ):
    values = [period_distance(day, day) for day in util.days()]
    return render_to_response(template,
            {
                'values': values,
                'days': reversed(util.days()),
                'max_value': max(values),
            }, context_instance=RequestContext(request))


class BikeRepairView(SuccessMessageMixin, CreateView):
    template_name = 'generic_form_template.html'
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


def draw_results(request,
        competition_slug,
        template = 'admin/draw.html'
        ):
    return render_to_response(template,
            {
                'results': draw.draw(competition_slug),
            }, context_instance=RequestContext(request))
