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
import time, random, httplib, urllib, hashlib, datetime
# Django imports
from django.shortcuts import render_to_response, redirect
import django.contrib.auth
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from decorators import must_be_coordinator, must_be_approved_for_team, must_be_company_admin, must_be_competitor, login_required_simple
from django.template import RequestContext
from django.db.models import Sum, Count, Q
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_page
# Registration imports
import registration.signals, registration.backends, registration.backends.simple
# Model imports
from django.contrib.auth.models import User
from models import UserProfile, Trip, Answer, Question, Team, Payment, Subsidiary, Company, Competition, Choice
from forms import RegistrationFormDPNK, RegisterTeamForm, RegisterSubsidiaryForm, RegisterCompanyForm, RegisterTeamForm, ProfileUpdateForm, InviteForm, TeamAdminForm,  PaymentTypeForm
from django.conf import settings
from  django.http import HttpResponse
from django import http
# Local imports
import util
from dpnk.email import approval_request_mail, register_mail, team_membership_approval_mail, team_membership_denial_mail, team_created_mail, invitation_mail
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm
from django.contrib.sites.models import get_current_site
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, logout as auth_logout

from wp_urls import wp_reverse
from util import redirect
import logging
import models
logger = logging.getLogger(__name__)

def login(request, template_name='registration/login.html',
          authentication_form=AuthenticationForm):
    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():
            redirect_to = settings.LOGIN_REDIRECT_URL
            if request.path == settings.LOGIN_URL:
                redirect_to = redirect(wp_reverse("profil"))
            auth_login(request, form.get_user())
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponse(redirect_to)
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

class UserProfileRegistrationBackend(registration.backends.simple.SimpleBackend):
    def register(self, request, user_team, **cleaned_data):
        new_user = super(UserProfileRegistrationBackend, self).register(request, **cleaned_data)
        from dpnk.models import UserProfile

        new_user.first_name = cleaned_data['first_name']
        new_user.last_name = cleaned_data['last_name']
        new_user.save()

        UserProfile(user = new_user,
                    team = user_team,
                    t_shirt_size = cleaned_data['t_shirt_size'],
                    telephone = cleaned_data['telephone'],
                    distance = cleaned_data['distance']
                    ).save()
        return new_user

def register(request, backend='dpnk.views.UserProfileRegistrationBackend',
             success_url=None, form_class=None,
             disallowed_url='registration_disallowed',
             template_name='registration/registration_form.html',
             extra_context=None,
             token=None,
             initial_email=None):
    create_company = False
    create_subsidiary = False
    create_team = False

    backend = registration.backends.get_backend(backend)
    form_class = RegistrationFormDPNK

    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES)

        form_company = RegisterCompanyForm(request.POST, prefix = "company")
        form_subsidiary = RegisterSubsidiaryForm(request.POST, prefix = "subsidiary")
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
            form_subsidiary = RegisterSubsidiaryForm(prefix = "subsidiary")
            form.fields['subsidiary'].required = True

        if create_team:
            team_valid = form_team.is_valid()
            form.fields['team'].required = False
        else:
            form_team = RegisterTeamForm(prefix = "team")
            form.fields['team'].required = True

        form_valid = form.is_valid()

        if form_valid and company_valid and subsidiary_valid and team_valid:
            company = None
            subsidiary = None
            team = None

            if create_company:
                company = form_company.save()
            else:
                company = Company.objects.get(id=form.data['company'])

            if create_subsidiary:
                subsidiary = form_subsidiary.save(commit=False)
                subsidiary.company = company
                form_subsidiary.save()
            else:
                subsidiary = Subsidiary.objects.get(id=form.data['subsidiary'])

            if create_team:
                team = form_team.save(commit=False)
                team.subsidiary = subsidiary
                form_team.save()
            else:
                team = form.cleaned_data['team']

            new_user = backend.register(request, team, **form.cleaned_data)
            auth_user = django.contrib.auth.authenticate(
                username=request.POST['username'],
                password=request.POST['password1'])
            django.contrib.auth.login(request, auth_user)

            if new_user.userprofile.team.invitation_token == token or create_team:
                userprofile = new_user.userprofile
                userprofile.approved_for_team = 'approved'
                userprofile.save()

            if create_team:
                team.coordinator = new_user.userprofile
                team.save()
                new_user.userprofile.approved_for_team = 'approved'
                new_user.userprofile.save()
                success_url = "pozvanky"
                team_created_mail(new_user)
            else:
                register_mail(new_user)

            if new_user.userprofile.approved_for_team != 'approved':
                approval_request_mail(new_user)
            return redirect(wp_reverse(success_url))
    else:
        initial_company = None
        initial_subsidiary = None
        initial_team = None

        if token != None:
            try:
                team = Team.objects.get(invitation_token=token)
            except Exception, e:
                logger.error('Can\'t find team with token %s, email: %s, exception: %s' % (token, initial_team, str(e)))
                return HttpResponse(_(u'<div class="text-error">Automatická registrace selhala. K danému tokenu neexistuje v databázi žádný tým. Zkuste prosím váš tým najít pomocí <a href="%s">manuální registrace</a>.</div>' % wp_reverse("registrace")), status=401)

            initial_company = team.subsidiary.company
            initial_subsidiary = team.subsidiary
            initial_team = team

        form = form_class(request, initial={'company': initial_company, 'subsidiary': initial_subsidiary, 'team': initial_team, 'email': initial_email})
        form_company = RegisterCompanyForm(prefix = "company")
        form_subsidiary = RegisterSubsidiaryForm(prefix = "subsidiary")
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

@login_required
def payment_type(request):
    if request.user.userprofile.team.subsidiary.city.admission_fee == 0:
        return redirect(wp_reverse('profil'))
    template_name='registration/payment_type.html'
    form_class = PaymentTypeForm

    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES)
        userprofile = request.user.userprofile
        if form.is_valid():
            if form.cleaned_data['payment_type'] == 'pay':
                return redirect(wp_reverse('platba'))
            elif form.cleaned_data['payment_type'] == 'company':
                Payment(user=userprofile, amount=0, pay_type='fc', status=Payment.Status.NEW).save()
                logger.info('Inserting company payment for %s' % (userprofile.user))
            elif form.cleaned_data['payment_type'] == 'member':
                Payment(user=userprofile, amount=0, pay_type='am', status=Payment.Status.NEW).save()
                logger.info('Inserting automat club member payment for %s' % (userprofile.user))

            return redirect(wp_reverse('profil'))
    else:
        form = form_class()

    return render_to_response(template_name,
                              {'form': form
                               }, context_instance=RequestContext(request))

@login_required
def payment(request):
    if request.user.userprofile.team.subsidiary.city.admission_fee == 0:
        return redirect(wp_reverse('profil'))
    uid = request.user.id
    order_id = '%s-1' % uid
    session_id = "%sJ%d " % (order_id, int(time.time()))
    userprofile = UserProfile.objects.get(user=request.user)
    # Save new payment record
    p = Payment(session_id=session_id,
                user=userprofile,
                order_id = order_id,
                amount = request.user.userprofile.team.subsidiary.city.admission_fee,
                description = "Ucastnicky poplatek Do prace na kole")
    p.save()
    logger.info('Inserting payment with uid: %s, order_id: %s, session_id: %s, userprofile: %s' % (uid, order_id, session_id, userprofile.user))
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

    logger.info('Payment result: success: %s, trans_id: %s, session_id: %s, pay_type: %s, error: %s, user: %s' % (success, trans_id, session_id, pay_type, error, request.user))
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
    check_sig(sig, (pos_id, session_id, ts))
    # Determine the status of transaction based on the notification
    c = httplib.HTTPSConnection("www.payu.cz")
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

@login_required
@must_be_competitor
def profile_access(request):
    profile = request.user.get_profile()
    return render_to_response('registration/profile_access.html',
                              {
            'city': profile.team.subsidiary.city
            }, context_instance=RequestContext(request))


def trip_active(day, today):
    return ((day <= today) 
        and (day > today - datetime.timedelta(days=14))
    )

@login_required_simple
@must_be_competitor
@must_be_approved_for_team
def rides(request, template='registration/rides.html',
        success_url="profil"):
    days = util.days()
    today = util.today()
    profile = request.user.get_profile()

    if request.method == 'POST':
        if 'day' in request.POST and request.POST["day"]:
            day = int(request.POST["day"])
            date = days[day-1]
            if not trip_active(date, today):
                logger.error(u'User %s is trying to fill in nonactive day, POST: %s' % (profile, request.POST))
                return HttpResponse(_(u'<div class="text-error">Tento den již není možné vyplnit.</div>'), status=401)
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
    for t in Trip.objects.filter(user=profile):
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
            'has_distance_competition': profile.has_distance_competition(),
            }, context_instance=RequestContext(request))

@login_required
@must_be_competitor
def profile(request):
    profile = request.user.get_profile()

    # Render profile
    payment_status = profile.payment_status()
    if profile.team and profile.team.coordinator:
        team_members_count = profile.team.members().count()
    request.session['invite_success_url'] = 'profil'
    return render_to_response('registration/profile.html',
                              {
            'active': profile.user.is_active,
            'superuser': request.user.is_superuser,
            'user': request.user,
            'profile': profile,
            'team': profile.team,
            'payment_status': payment_status,
            'payment_type': profile.payment_type(),
            'team_members_count': team_members_count,
            'competition_state': settings.COMPETITION_STATE,
            'approved_for_team': request.user.userprofile.approved_for_team,
            'is_company_admin': models.is_company_admin(request.user),
            }, context_instance=RequestContext(request))

@login_required_simple
@must_be_competitor
@must_be_approved_for_team
def other_team_members(request,
        template = 'registration/team_members.html'
        ):
    profile = request.user.get_profile()

    team_members = []
    if profile.team and profile.team.coordinator:
        team_members = profile.team.all_members()

    return render_to_response(template,
                              {
            'team_members': team_members,
            }, context_instance=RequestContext(request))

@login_required_simple
@must_be_competitor
@must_be_approved_for_team
def admissions(request, template, 
        success_url="profil",
        ):
    userprofile = request.user.get_profile()

    if request.method == 'POST':
        if 'admission_competition_id' in request.POST and request.POST['admission_competition_id']:
            competition = Competition.objects.get(id=request.POST['admission_competition_id']) 
            competition.make_admission(userprofile, True)
        if 'cancellation_competition_id' in request.POST and request.POST['cancellation_competition_id']:
            competition = Competition.objects.get(id=request.POST['cancellation_competition_id']) 
            competition.make_admission(userprofile, False)
        return redirect(wp_reverse(success_url))

    competitions = userprofile.get_competitions()
    for competition in competitions:
        competition.competitor_has_admission = competition.has_admission(userprofile)
        competition.competitor_can_admit = competition.can_admit(userprofile)

    return render_to_response(template,
                              {
            'competitions': competitions,
            'userprofile': userprofile,
            }, context_instance=RequestContext(request))

@cache_page(24 * 60 * 60) 
def competition_results(request, template, competition_slug='testing_zavod', limit=None):
    if limit == '':
        limit = None

    #if request.user.is_anonymous():
    #    userprofile = None
    #else:
    #    userprofile = request.user.get_profile()

    competition = Competition.objects.get(slug=competition_slug)

    return render_to_response(template,
                              {
            #'userprofile': userprofile,
            'competition': competition,
            'results': competition.get_results()[:limit],
            }, context_instance=RequestContext(request))

@login_required
def update_profile(request,
            success_url = 'profil'
                  ):
    create_team = False
    profile = request.user.get_profile()
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        form_team = RegisterTeamForm(request.POST, prefix = "team")
        create_team = 'id_team_selected' in request.POST
        team_valid = True

        if create_team:
            team_valid = form_team.is_valid()
            if form.can_change_team:
                form.fields['team'].required = False
                form.Meta.exclude = ('team')
        else:
            form_team = RegisterTeamForm(prefix = "team")
            if form.can_change_team:
                form.fields['team'].required = True
                form.Meta.exclude = ()
        old_team = request.user.userprofile.team

        form_valid = form.is_valid()

        if team_valid and form_valid:
            team_changed = form.cleaned_data and 'team' in form.cleaned_data and old_team != form.cleaned_data['team']

            userprofile = form.save(commit=False)

            if create_team:
                team = form_team.save(commit=False)
                team.subsidiary = request.user.userprofile.team.subsidiary

                if hasattr(userprofile, 'coordinated_team'):
                    coordinated_team_members = UserProfile.objects.exclude(id=userprofile.id).filter(team=userprofile.coordinated_team, user__is_active=True)
                    if len(coordinated_team_members)>0:
                        userprofile.coordinated_team.coordinator = coordinated_team_members[0]
                    else:
                        userprofile.coordinated_team.coordinator = None
                    userprofile.coordinated_team.save()

                userprofile.team = team
                userprofile.approved_for_team = 'approved'
                team.coordinator = userprofile

                form_team.save()

                userprofile.team = team
                success_url = "pozvanky"
                request.session['invite_success_url'] = 'profil'

                team_created_mail(userprofile.user)

            if team_changed and not create_team:
                userprofile.approved_for_team = 'undecided'
                approval_request_mail(userprofile.user)

            form.save()

            return redirect(wp_reverse(success_url))
    else:
        form = ProfileUpdateForm(instance=profile)
        form_team = RegisterTeamForm(prefix = "team")

    if form.can_change_team:
        form.fields['team'].widget.underlying_form = form_team
        form.fields['team'].widget.create = create_team
    
    return render_to_response('registration/update_profile.html',
                              {'form': form,
                               'can_change_team': form.can_change_team
                               }, context_instance=RequestContext(request))

@login_required
@must_be_approved_for_team
def questionaire(request, questionaire = None, 
        template = 'registration/questionaire.html',
        success_url = 'profil',
        ):
    userprofile = request.user.get_profile()
    questions = Question.objects.filter(competition__slug=questionaire).order_by('order')
    if request.method == 'POST':
        choice_ids = [v for k, v in request.POST.items() if k.startswith('choice')]
        comment_ids = [int(k.split('-')[1]) for k, v in request.POST.items() if k.startswith('comment')]

        answers_dict = {}
        answers_dict_choice_type = {}
        for question in questions:
            try:
                answer = Answer.objects.get(user = request.user.get_profile(),
                                            question = question)
                # Cleanup previous fillings
                answer.choices = []
            except Answer.DoesNotExist:
                answer = Answer()
                answer.user = request.user.get_profile()
                answer.question = question
            answer.save()
            answers_dict[question.id] = answer
            answers_dict_choice_type[question.choice_type.id] = answer

        # Save choices
        for choice_id in choice_ids:
            choice = Choice.objects.get(id=choice_id)
            answer = answers_dict_choice_type[choice.choice_type.id]
            answer.choices.add(choice_id)
            answer.save()
        # Save comments
        for comment_id in comment_ids:
            answer = answers_dict[comment_id] # comment_id = question_id
            answer.comment = request.POST.get('comment-%d' % comment_id, '')
            answer.save()
    
        competition = Competition.objects.get(slug=questionaire)
        competition.make_admission(userprofile)
        return redirect(wp_reverse(success_url))
    else:
        for question in questions:
            try:
                question.choices = Choice.objects.filter(choice_type=question.choice_type)
            except Choice.DoesNotExist:
                question.choices = None
            try:
                answer = Answer.objects.get(
                    question=question,
                    user=userprofile)
                question.comment_prefill = answer.comment
                question.choices_prefill = [c.id for c in answer.choices.all()]
            except Answer.DoesNotExist:
                question.comment_prefill = ''
                question.choices_prefill = ''

        return render_to_response(template,
                                  {'user': userprofile,
                                   'questions': questions,
                                   'questionaire': questionaire,
                                   }, context_instance=RequestContext(request))

@staff_member_required
def questions(request):
    questions = Question.objects.all().order_by('date')
    return render_to_response('admin/questions.html',
                              {'questions': questions
                               }, context_instance=RequestContext(request))

def _company_answers(uid):
    return Answer.objects.filter(user_id=uid,
                                 question__in=Question.objects.filter(competition__slug='cyklozamestnavatel_roku'))

def _total_points(answers):
    total_points = 0
    for a in answers:
        for c in a.choices.all():
            # Points assigned based on choices
            if c.points:
                total_points += c.points
        # Additional points assigned manually
        if a.points_given:
            total_points += a.points_given
    return total_points

@staff_member_required
def company_survey(request):
    companies = [(u.id, u.team.subsidiary.company, u.team.subsidiary.city, u.team.name, _total_points(_company_answers(u.id))) for u in
                 set([a.user for a in Answer.objects.filter(
                    question__in=Question.objects.filter(competition__slug='cyklozamestnavatel_roku'))])]
    return render_to_response('admin/company_survey.html',
                              {'companies': sorted(companies, key = lambda c: c[4], reverse=True)
                               }, context_instance=RequestContext(request))

def company_survey_answers(request):
    answers = _company_answers(request.GET['uid'])
    team = UserProfile.objects.get(id=request.GET['uid']).team
    total_points = _total_points(answers)
    return render_to_response('admin/company_survey_answers.html',
                              {'answers': answers,
                               'team': team,
                               'total_points': total_points
                               }, context_instance=RequestContext(request))


@staff_member_required
def answers(request):
    question_id = request.GET['question']
    question = Question.objects.get(id=question_id)

    if request.method == 'POST':
        points = [(k.split('-')[1], v) for k, v in request.POST.items() if k.startswith('points-')]
        for p in points:
            answer = Answer.objects.get(id=p[0])
            answer.points = int(p[1])
            answer.save()

    answers = Answer.objects.filter(question_id=question_id)
    total_respondents = len(answers)
    count = {'Praha': {}, 'Brno': {}, 'Liberec': {}}
    count_all = {}
    respondents = {'Praha': 0, 'Brno': 0, 'Liberec': 0}
    choice_names = {}
    
    for a in answers:
        a.city = a.user.city()

    
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

    stat = {'Praha': [], 'Brno': [], 'Liberec': [], 'Celkem': []}
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
                               'answers': sorted(answers, key=lambda a: a.city),
                               'stat': stat,
                               'total_respondents': total_respondents,
                               'choice_names': choice_names
                               }, context_instance=RequestContext(request))

def approve_for_team(userprofile, reason, approve=False, deny=False):
    if deny:
        if not reason:
            return 'no_message'
        userprofile.approved_for_team = 'denied'
        userprofile.save()
        team_membership_denial_mail(userprofile.user, reason)
        return 'denied'
    elif approve:
        if len(userprofile.team.members()) >= 5:
            return 'team_full'
        userprofile.approved_for_team = 'approved'
        userprofile.save()
        user_approved = True
        team_membership_approval_mail(userprofile.user)
        return 'approved'

@login_required
def team_approval_request(request):
    approval_request_mail(request.user)
    return render_to_response('registration/request_team_approval.html',
                              context_instance=RequestContext(request))

@must_be_coordinator
@login_required
def invite(request, backend='registration.backends.simple.SimpleBackend',
             success_url=None, form_class=None,
             template_name='registration/invitation.html',
             extra_context=None):
    form_class = InviteForm

    if 'invite_success_url' in request.session:
        success_url = request.session.get('invite_success_url')

    if request.method == 'POST':
        form = form_class(data=request.POST)
        if form.is_valid():
            invitation_mail(request.user, [form.cleaned_data['email1'], form.cleaned_data['email2'], form.cleaned_data['email3'], form.cleaned_data['email4'] ])
            return redirect(wp_reverse(success_url))
    else:
        form = form_class()
    return render_to_response(template_name,
                              {'form': form,
                              }, context_instance=RequestContext(request))

@must_be_coordinator
@login_required
def team_admin_team(request, backend='registration.backends.simple.SimpleBackend',
             success_url=None, form_class=None,
             template_name='registration/team_admin_team.html',
             extra_context=None):
    team = request.user.userprofile.team
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
@login_required
def team_admin_members(request, backend='registration.backends.simple.SimpleBackend',
             template_name='registration/team_admin_members.html',
             extra_context=None):
    team = request.user.userprofile.team
    unapproved_users = []
    denial_message = 'unapproved'

    if 'button_action' in request.POST and request.POST['button_action']:
        b_action = request.POST['button_action'].split('-')
        userprofile = UserProfile.objects.get(id=b_action[1])
        if userprofile.approved_for_team not in ('undecided', 'denied') or userprofile.team != team or not userprofile.user.is_active:
            logger.error('Approving user with wrong parameters. User: %s, approval: %s, team: %s, active: %s' % (userprofile.user, userprofile.approved_for_team, userprofile.team, userprofile.user.is_active))
            denial_message = 'cannot_approve'
        else:
            denial_message = approve_for_team(userprofile, request.POST.get('reason-' + str(userprofile.id), ''), b_action[0] == 'approve', b_action[0] == 'deny')

    for userprofile in UserProfile.objects.filter(team = team, user__is_active=True):
        unapproved_users.append([
            ('state', None, userprofile.approved_for_team),
            ('id', None, userprofile.id),
            ('payment', None, userprofile.payment()),
            ('name', _(u"Jméno"), unicode(userprofile)),
            ('username', _(u"Uživatel"), userprofile.user),
            ('email', _(u"Email"), userprofile.user.email),
            ('payment_description', _(u"Platba"), userprofile.payment()['status_description']),
            ('telephone', _(u"Telefon"), userprofile.telephone),
            ('state_name', _(u"Stav"), unicode(userprofile.get_approved_for_team_display())),
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
    distance += trips.filter(Q(distance_from = None) | Q(distance_from = 0), trip_from = True).aggregate(Sum("user__distance"))['user__distance__sum'] or 0
    distance += trips.filter(Q(distance_to = None) | Q(distance_to = 0), trip_to = True).aggregate(Sum("user__distance"))['user__distance__sum'] or 0
    return distance

def total_distance():
    return distance(Trip.objects)

def period_distance(day_from, day_to):
    return distance(Trip.objects.filter(date__gte=day_from, date__lte=day_to))

def statistics(request,
        variable,
        template = 'registration/statistics.html'
        ):

    variables = {}
    variables['ujeta-vzdalenost'] = total_distance()
    variables['ujeta-vzdalenost-dnes'] = period_distance(util.today(), util.today())
    variables['pocet-soutezicich'] = UserProfile.objects.filter(user__is_active = True, approved_for_team='approved').count()

    if request.user.is_authenticated() and models.is_competitor(request.user):
        variables['pocet-soutezicich-firma'] = UserProfile.objects.filter(user__is_active = True, approved_for_team='approved', team__subsidiary__company = models.get_company(request.user)).count()
    else:
        variables['pocet-soutezicich-firma'] = "-"

    return render_to_response(template,
            {
                'variable': variables[variable],
            }, context_instance=RequestContext(request))
