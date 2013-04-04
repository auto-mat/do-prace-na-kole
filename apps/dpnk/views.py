# -*- coding: utf-8 -*-
# Author: Hynek Hanke <hynek.hanke@auto-mat.cz>
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
from django.core.mail import EmailMessage, mail_admins
from django.template import RequestContext
from django.db.models import Sum, Count
from django.utils.translation import gettext as _
# Registration imports
import registration.signals, registration.backends
# Model imports
from django.contrib.auth.models import User
from models import UserProfile, Voucher, Trip, Answer, Question, Team, Payment, Subsidiary, Company
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
from util import Mailing

#decorator
def must_be_coordinator(fn):
    @login_required
    def wrapper(*args, **kwargs):
        request = args[0]
        team = request.user.userprofile.team
        if team.coordinator != request.user.userprofile:
            return HttpResponse(_(u"<div class='text-error'>Nejste koordinátorem týmu %(team)s, nemáte tedy oprávnění editovat jeho údaje. Koordinátorem vašeho týmu je %(coordinator)s, vy jste: %(you)s </div>") % {'team': team.name, 'coordinator': team.coordinator, 'you': request.user.userprofile}, status=401)
        else:
            return fn(*args, **kwargs)
    return wrapper

#decorator
def must_be_approved_for_team(fn):
    @login_required
    def wrapper(*args, **kwargs):
        request = args[0]
        userprofile = request.user.userprofile
        if userprofile.approved_for_team == 'approved' or userprofile.team.coordinator == userprofile:
            return fn(*args, **kwargs)
        else:
            return HttpResponse(_(u"<div class='text-error'>Vaše členství v týmu %s nebylo odsouhlaseno. O ověření členství můžete požádat v <a href='/registrace/profil'>profilu</a>.</div>") % (userprofile.team.name,), status=401)
    return wrapper

def redirect(url):
    return HttpResponse("redirect:"+url)

def login(request, template_name='registration/login.html',
          authentication_form=AuthenticationForm):
    redirect_to = wp_reverse("profil")
    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():
            redirect_to = settings.LOGIN_REDIRECT_URL
            auth_login(request, form.get_user())
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponse(redirect(wp_reverse("profil")))
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
    return render_to_response(template_name, context)

def register(request, backend='registration.backends.simple.SimpleBackend',
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
        create_company = 'id_company_selected' in request.POST
        create_subsidiary = 'id_subsidiary_selected' in request.POST
        create_team = 'id_team_selected' in request.POST
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

            new_user = backend.register(request, **form.cleaned_data)
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

            # Register into mailing list
            try:
                m = Mailing(api_key=settings.MAILING_API_KEY, list_id=settings.MAILING_LIST_ID)
                mailing_id = m.add(new_user.first_name, new_user.last_name, new_user.email,
                                   new_user.userprofile.team.subsidiary.city.name)
            except Exception, e:
                mail_admins("ERROR Do prace na kole: Nepodarilo se pridat ucastnika do mailing listu", str(e))
            else:
                new_user.userprofile.mailing_id = mailing_id
                new_user.userprofile.save()

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
                mail_admins(u"ERROR Do prace na kole: Nepodařilo se najít tým pro token", u"Exception: %s\nToken: %s\nEmail: %s" % (str(e), token, initial_email) )
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



def create_profile(user, request, **kwargs):
    from dpnk.models import UserProfile
    if 'id_team_selected' in request.POST:
        team = Team.objects.get(name=request.POST['team-name'])
    else:
        team = Team.objects.get(id=request.POST['team'])

    user.first_name = request.POST['first_name']
    user.last_name = request.POST['last_name']
    user.save()

    UserProfile(user = user,
                team = team,
                t_shirt_size = request.POST['t_shirt_size'],
                telephone = request.POST['telephone'],
                distance = request.POST['distance']
                ).save()
registration.signals.user_registered.connect(create_profile)

@login_required
def payment_type(request):
    if request.user.userprofile.team.subsidiary.city.admission_fee == 0:
        return redirect(wp_reverse('profil'))
    template_name='registration/payment_type.html'
    form_class = PaymentTypeForm

    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES)
        if form.is_valid():
            if form.cleaned_data['payment_type'] == 'pay':
                return redirect(wp_reverse('platba'))
            elif form.cleaned_data['payment_type'] == 'company':
                Payment(user=request.user.userprofile, amount=0, pay_type='fc', status=Payment.Status.NEW).save()
            elif form.cleaned_data['payment_type'] == 'member':
                Payment(user=request.user.userprofile, amount=0, pay_type='am', status=Payment.Status.NEW).save()

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
    # Save new payment record
    p = Payment(session_id=session_id,
                user=UserProfile.objects.get(user=request.user),
                order_id = order_id,
                amount = request.user.userprofile.team.subsidiary.city.admission_fee,
                description = "Ucastnicky poplatek Do prace na kole")
    p.save()
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
        p = Payment(order_id=r['trans_order_id'], session_id=['trans_session_id'],
                    amount=int(r['trans_amount'])/100, description=r['trans_desc'])

    p.pay_type = r['trans_pay_type']
    p.status = r['trans_status']
    if r['trans_recv'] != '':
        p.realized = r['trans_recv']
    p.save()

    # Return positive error code as per PayU protocol
    return http.HttpResponse("OK")

@login_required
def profile_access(request):
    profile = request.user.get_profile()
    return render_to_response('registration/profile_access.html',
                              {
            'city': profile.team.subsidiary.city
            }, context_instance=RequestContext(request))

@login_required
def profile(request):

    days = util.days()
    weekdays = ['Po', 'Út', 'St', 'Čt', 'Pá']
    today = datetime.date.today()
    #today = datetime.date(year=2012, month=5, day=4)
    profile = request.user.get_profile()

    # if request.method == 'POST':
    #     raise http.Http404 # No POST, competition already terminated
    #     if 'day' in request.POST:
    #         try:
    #             trip = Trip.objects.get(user = request.user.get_profile(),
    #                                     date = days[int(request.POST['day'])-1])
    #         except Trip.DoesNotExist:
    #             trip = Trip()
    #             trip.date = days[int(request.POST['day'])-1]
    #             trip.user = request.user.get_profile()
    #         trip.trip_to = request.POST.get('trip_to', False)
    #         trip.trip_from = request.POST.get('trip_from', False)
    #         trip.save()
    #     # Pre-calculate total number of trips into userprofile to save load
    #     trip_counts = Trip.objects.filter(user=profile).values('user').annotate(Sum('trip_to'), Sum('trip_from'))
    #     try:
    #         profile.trips = trip_counts[0]['trip_to__sum'] + trip_counts[0]['trip_from__sum']
    #     except IndexError:
    #         profile.trips = 0
    #     profile.save()
    # try:
    #     voucher_code = Voucher.objects.filter(user=profile)[0].code
    # except IndexError, e:
    #     voucher_code = ''

    # Render profile
    payment_status = profile.payment_status()
    team_members = UserProfile.objects.filter(team=profile.team, user__is_active=True)

    # trips = {}
    # for t in Trip.objects.filter(user=profile):
    #     trips[t.date] = (t.trip_to, t.trip_from)
    # calendar = []

    # counter = 0
    # for i, d in enumerate(days):
    #     cd = {}
    #     cd['name'] = "%s %d.%d." % (weekdays[d.weekday()], d.day, d.month)
    #     cd['iso'] = str(d)
    #     cd['question_active'] = (d <= today)
    #     cd['trips_active'] = (d <= today) and (
    #         len(Answer.objects.filter(
    #                 question=Question.objects.get(date = d),
    #                 user=request.user.get_profile())) > 0)
    #     if d in trips:
    #         cd['default_trip_to'] = trips[d][0]
    #         cd['default_trip_from'] = trips[d][1]
    #         counter += int(trips[d][0]) + int(trips[d][1])
    #     else:
    #         cd['default_trip_to'] = False
    #         cd['default_trip_from'] = False
    #     cd['percentage'] = float(counter)/(2*(i+1))*100
    #     cd['percentage_str'] = "%.0f" % (cd['percentage'])
    #     cd['distance'] = counter * profile.distance
    #     calendar.append(cd)

    # member_counts = []
    # for member in team_members:
    #     member_counts.append({
    #             'name': str(member),
    #             'trips': member.trips,
    #             'percentage': float(member.trips)/(2*util.days_count())*100,
    #             'distance': member.trips * member.distance})
    # if len(team_members):
    #     team_percentage = float(sum([m['trips'] for m in member_counts]))/(2*len(team_members)*util.days_count()) * 100
    # else:
    #     team_percentage = 0
    # team_distance = sum([m['distance'] for m in member_counts])

    #for user_position, u in enumerate(UserResults.objects.filter(city=profile.team.city)):
    #    if u.id == profile.id:
    #        break
    #user_position += 1

    #for team_position, t in enumerate(TeamResults.objects.filter(city=profile.team.city)):
    #    if t.id == profile.team.id:
    #        break
    #team_position += 1

    # company_survey_answers = Answer.objects.filter(
    #     question_id=34, user__in = [m.id for m in team_members])
    # if len(company_survey_answers):
    #     company_survey_by = company_survey_answers[0].user
    #     if company_survey_by == request.user.get_profile():
    #         company_survey_by = 'me'
    # else:
    #     company_survey_by = None
    return render_to_response('registration/profile.html',
                              {
            'active': profile.user.is_active,
            'superuser': request.user.is_superuser,
            'user': request.user,
            'profile': profile,
            'team': profile.team,
            'payment_status': payment_status,
            'payment_type': profile.payment_type(),
            #'voucher': voucher_code,
            'team_members': UserProfile.objects.filter(team=profile.team, user__is_active=True).exclude(id=profile.team.coordinator.id).exclude(id=profile.id),
            'team_members_count': len(profile.team.members()),
            #'calendar': calendar,
            #'member_counts': member_counts,
            #'team_percentage': team_percentage,
            #'team_distance': team_distance,
            #'user_position': user_position,
            #'team_position': team_position,
            #'company_survey_by': company_survey_by,
            'competition_state': settings.COMPETITION_STATE,
            'approved_for_team': request.user.userprofile.approved_for_team,
            }, context_instance=RequestContext(request))

def results(request, template):

    city = request.GET.get('mesto', None)

    #if city:
    #    user_by_percentage = UserResults.objects.filter(city=city)[:10]
    #    user_by_distance = UserResults.objects.filter(city=city).order_by('-distance')[:10]
    #    team_by_distance = TeamResults.objects.filter(city=city).order_by('-distance')[:20]
    #    team_by_percentage = TeamResults.objects.filter(city=city)
    #    user_count = UserResults.objects.filter(city=city).count()
    #    team_count = TeamResults.objects.filter(city=city).count()
    #else:
    #    user_by_percentage = UserResults.objects.all()[:10]
    #    user_by_distance = UserResults.objects.all().order_by('-distance')[:10]
    #    team_by_distance = TeamResults.objects.all().order_by('-distance')[:20]
    #    team_by_percentage = TeamResults.objects.all()
    #    user_count = UserProfile.objects.filter(active=True).count()
    #    team_count = Team.objects.all().count()

    return render_to_response(template,
                              {
            'user_by_percentage': user_by_percentage,
            'user_by_distance': user_by_distance,
            'team_by_percentage': team_by_percentage,
            'team_by_distance': team_by_distance,
            'city': city,
            'user_count': user_count,
            'team_count': team_count,
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

        form_valid = form.is_valid()

        if team_valid and form_valid:
            userprofile = form.save(commit=False)

            if create_team:
                team = form_team.save(commit=False)
                team.subsidiary = request.user.userprofile.team.subsidiary

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
                request.session['success_url'] = 'profil'

                team_created_mail(userprofile.user)

            team_changed = form.cleaned_data and request.user.userprofile.team != form.cleaned_data['team']
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
def questionaire(request, template = 'registration/questionaire.html'):

    def get_questions(params):
        if not params.has_key('questionaire'):
            raise http.Http404
        questionaire = params['questionaire']
        if questionaire == 'player':
            if not params.has_key('day'):
                raise http.Http404
            try:
                iso_day = params['day']
                day = datetime.date(*[int(v) for v in iso_day.split('-')])
            except ValueError:
                raise http.Http404
            if day > datetime.date.today():
                raise http.Http404
            questions = [Question.objects.get(questionaire=questionaire, date=day)]
        elif questionaire == 'company':
            questions = Question.objects.filter(questionaire=questionaire).order_by('order')
        return (questionaire, questions)

    if request.method == 'POST':
        raise http.Http404 # No POST, competition already terminated
        questionaire, questions = get_questions(request.POST)
        choice_ids = [v for k, v in request.POST.items() if k.startswith('choice')]
        comment_ids = [int(k.split('-')[1]) for k, v in request.POST.items() if k.startswith('comment')]

        answers_dict = {}
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

        # Save choices
        for choice_id in choice_ids:
            choice = Choice.objects.get(id=choice_id)
            answer = answers_dict[choice.question.id]
            answer.choices.add(choice_id)
            answer.save()
        # Save comments
        for comment_id in comment_ids:
            answer = answers_dict[comment_id] # comment_id = question_id
            answer.comment = request.POST.get('comment-%d' % comment_id, '')
            answer.save()
        return http.HttpResponseRedirect('/registrace/profil/') # Redirect after POST
    else:
        questionaire, questions = get_questions(request.GET)
        for question in questions:
            try:
                question.choices = Choice.objects.filter(question=question)
            except Choice.DoesNotExist:
                question.choices = None
            try:
                answer = Answer.objects.get(
                    question=question,
                    user=request.user.get_profile())
                question.comment_prefill = answer.comment
                question.choices_prefill = [c.id for c in answer.choices.all()]
            except Answer.DoesNotExist:
                question.comment_prefill = ''
                question.choices_prefill = ''

        return render_to_response(template,
                                  {'user': request.user.get_profile(),
                                   'questions': questions,
                                   'questionaire': questionaire,
                                   'day': request.GET.get('day', '')
                                   }, context_instance=RequestContext(request))

@staff_member_required
def questions(request):
    questions = Question.objects.all().order_by('date')
    return render_to_response('admin/questions.html',
                              {'questions': questions
                               }, context_instance=RequestContext(request))

def _company_answers(uid):
    return Answer.objects.filter(user_id=uid,
                                 question__in=Question.objects.filter(questionaire='company'))

def _total_points(answers):
    total_points = 0
    for a in answers:
        for c in a.choices.all():
            # Points assigned based on choices
            if c.points:
                total_points += c.points
        # Additional points assigned manually
        total_points += a.points
    return total_points

@staff_member_required
def company_survey(request):
    companies = [(u.id, u.team.company, u.team.city, u.team.name, _total_points(_company_answers(u.id))) for u in
                 set([a.user for a in Answer.objects.filter(
                    question__in=Question.objects.filter(questionaire='company'))])]
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

    if 'success_url' in request.session:
        success_url = request.session.get('success_url')

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
            mail_admins(u"ERROR Do prace na kole: Ověřování uživatele se špatnými parametry", u"Uživatel: %s\nApproval: %s\nTým: %s\nActive: %s" % (userprofile, userprofile.approved_for_team, userprofile.team, userprofile.user.is_active) )
            denial_message = 'cannot_approve'
        else:
            denial_message = approve_for_team(userprofile, request.POST.get('reason-' + str(userprofile.id), ''), b_action[0] == 'approve', b_action[0] == 'deny')

    for userprofile in UserProfile.objects.filter(team = team, user__is_active=True):
        unapproved_users.append([
            ('state', None, userprofile.approved_for_team),
            ('id', None, userprofile.id),
            ('payment_status', None, userprofile.payment_status()),
            ('name', _(u"Jméno"), unicode(userprofile)),
            ('username', _(u"Uživatel"), userprofile.user),
            ('email', _(u"Email"), userprofile.user.email),
            ('payment', _(u"Platba"), {'waiting': _(u"Nezaplaceno"), 'done': _(u"Zaplaceno"), 'no_admission': _(u"Není potřeba"), None: _(u"Neznámý")}[userprofile.payment_status()]),
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
