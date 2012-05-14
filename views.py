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
from django import forms, http
from django.shortcuts import render_to_response, redirect
import django.contrib.auth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import EmailMessage
from django.db.models import Sum, Count
# Registration imports
import registration.forms, registration.signals, registration.backends
# Model imports
from models import User, UserProfile, Team, Payment, Voucher, Trip, Question, Choice, \
    Answer, UserResults, TeamResults
# Local imports
import util

class RegistrationFormDPNK(registration.forms.RegistrationForm):
    required_css_class = 'required'
    
    firstname = forms.CharField(
        label="Jméno",
        max_length=30,
        required=True)
    surname = forms.CharField(
        label="Příjmení",
        max_length=30,
        required=True)
    team = forms.ModelChoiceField(
        label="Tým",
        queryset=Team.objects.all(),
        required=True)
    team_password = forms.CharField(
        label="Tajný kód týmu",
        max_length=20)
    distance = forms.IntegerField(
        label="Vzdálenost z domova do práce vzdušnou čarou (v km)",
        required=True)

    # -- Contacts
    telephone = forms.CharField(
        label="Telefon",
        max_length=30)

    def __init__(self, request=None, *args, **kwargs):
        if request:
            initial = kwargs.get('initial', {})
            if request.GET.get('team_password', None):
                initial['team_password'] = request.GET['team_password']
            if request.GET.get('team', None):
                initial['team'] = request.GET['team']
            kwargs['initial']=initial

        super(RegistrationFormDPNK, self).__init__(*args, **kwargs)
        self.fields.keyOrder = [
            'firstname',
            'surname',
            'team',
            'team_password',
            'distance',
            'email',
            'telephone',
            'username',
            'password1',
            'password2'
            ]

    def clean_team(self):
        data = self.cleaned_data['team']
        if len(UserProfile.objects.filter(team=data, active=True)) >= 5:
            raise forms.ValidationError("Tento tým již má pět členů a je tedy plný")
        return data

    def clean_team_password(self):
        data = self.cleaned_data['team_password']
        try:
            team = Team.objects.get(id=self.data['team'])
        except (Team.DoesNotExist, ValueError):
            raise forms.ValidationError("Neexistující nebo neplatný tým")
        if data.strip().lower() != team.password.strip():
            raise forms.ValidationError("Nesprávné heslo týmu")
        return data

def register(request, backend='registration.backends.simple.SimpleBackend',
             success_url=None, form_class=None,
             disallowed_url='registration_disallowed',
             template_name='registration/registration_form.html',
             extra_context=None):

    backend = registration.backends.get_backend(backend)
    form_class = RegistrationFormDPNK

    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_user = backend.register(request, **form.cleaned_data)
            auth_user = django.contrib.auth.authenticate(
                username=request.POST['username'],
                password=request.POST['password1'])
            django.contrib.auth.login(request, auth_user)
            return redirect(success_url)
    else:
        form = form_class(request)

    return render_to_response(template_name,
                              {'form': form})


class AutoRegistrationFormDPNK(RegistrationFormDPNK):

    def clean_team_password(self):
        return self.cleaned_data['team_password']

# Temporary to allow mass XLS registrations
def auto_register(request, backend='registration.backends.simple.SimpleBackend',
                  success_url=None, form_class=None,
                  disallowed_url='registration_disallowed',
                  template_name='registration/auto_registration_form.html',
                  extra_context=None):

    backend = registration.backends.get_backend(backend)
    form_class = AutoRegistrationFormDPNK

    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_user = backend.register(request, **form.cleaned_data)
            order_id = '%s-1' % new_user.id
            session_id = "%sJ%d " % (order_id, int(time.time()))
            p = Payment(user=new_user.get_profile(), pay_type='fa', status='99',
                        amount=160, order_id=order_id, session_id=session_id,
                        realized=datetime.datetime.now())
            p.save()
            auth_user = django.contrib.auth.authenticate(
                username=request.POST['username'],
                password=request.POST['password1'])
            django.contrib.auth.login(request, auth_user)
            return redirect('/mesto/praha/') # Redirect after POST
    else:
        form = form_class(request)

    return render_to_response(template_name,
                              {'form': form})

def create_profile(user, request, **kwargs):
    from dpnk.models import UserProfile
    UserProfile(user = user,
                team = Team.objects.get(id=request.POST['team']),
                firstname = request.POST['firstname'],
                surname = request.POST['surname'],
                telephone = request.POST['telephone'],
                distance = request.POST['distance']
                ).save()
registration.signals.user_registered.connect(create_profile)

class RegisterTeamForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'
    
    class Meta:
        model = Team
        fields = ('city', 'name', 'company', 'address')

def register_team(request):
    if request.method == 'POST':
        form = RegisterTeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.password = random.choice([l.strip() for l in open('/home/aplikace/dpnk/slova.txt')])
            form.save()
            return render_to_response('registration/team_password.html', {
                    'team_id': team.id,
                    'team_name': team.name,
                    'team_password': team.password
                    })
    else:
        form = RegisterTeamForm()
    return render_to_response('registration/register_team.html', {
            'form': form,
            })

@login_required
def payment(request):
    uid = request.user.id
    order_id = '%s-1' % uid
    session_id = "%sJ%d " % (order_id, int(time.time()))
    # Save new payment record
    p = Payment(session_id=session_id,
                user=UserProfile.objects.get(user=request.user),
                order_id = order_id,
                amount = 160,
                description = "Ucastnicky poplatek Do prace na kole")
    p.save()
    # Render form
    profile = UserProfile.objects.get(user=request.user)
    return render_to_response('registration/payment.html',
                              {
            'firstname': profile.firstname, # firstname
            'surname': profile.surname, # surname
            'email': profile.email, # email
            'amount': p.amount,
            'amount_hal': p.amount * 100, # v halerich
            'description' : p.description,
            'order_id' : p.order_id,
            'client_ip': request.META['REMOTE_ADDR'],
            'session_id': session_id
            })

def payment_result(request, success):
    trans_id = request.GET['trans_id']
    session_id = request.GET['session_id']
    pay_type = request.GET['pay_type']
    error = request.GET.get('error' or None)

    if session_id and session_id != "":
        p = Payment.objects.get(session_id=session_id)
        p.trans_id = trans_id
        p.pay_type = pay_type
        p.error = error
        p.save()

    if success == True:
        msg = "Vaše platba byla úspěšně přijata."
    else:
        msg = "Vaše platba se nezdařila. Po přihlášení do svého profilu můžete zadat novou platbu."

    try:
        city = UserProfile.objects.get(user=request.user).team.city
    except TypeError, e:
        # Looks like sometimes we loose the session before user comes
        # back from PayU
        city = None

    return render_to_response('registration/payment_result.html',
                              {
            'pay_type': pay_type,
            'message': msg,
            'city': city
            })

def make_sig(values):
    key1 = 'eac82603809d388f6a2b8b11471f1805'
    return hashlib.md5("".join(values+(key1,))).hexdigest()

def check_sig(sig, values):
    key2 = 'c2b52884c3816d209ea6c5e7cd917abb'
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
    p = Payment.objects.get(session_id=r['trans_session_id'])
    p.status = r['trans_status']
    if r['trans_recv'] != '':
        p.realized = r['trans_recv']
    p.save()

    if p.status == 99 or p.status == '99':
        if len(Voucher.objects.filter(user = p.user)) == 0:
            # Assign voucher to user
            v = random.choice(Voucher.objects.filter(user__isnull=True))
            v.user = p.user
            v.save()
            # Send user email confirmation and a voucher
            email = EmailMessage(subject=u"Platba Do práce na kole a slevový kupon",
                                 body=u"""Obdrželi jsme Vaši platbu startovného pro soutěž Do práce na kole.

Zaplacením startovného získáváte poukaz na designové triko kampaně Do
práce na kole 2012 (včetně poštovného a balného). Objednávku můžete
uskutečnit na adrese:

http://www.coromoro.com/designova_trika/detail/139-do-prace-na-kole-2012

Váš slevový kód pro nákup trička v obchodě Čoromoro je %s.

K jeho zadání budete vyzváni poté, co si vyberete velikost a přejdete
na svůj nákupní košík.

S pozdravem
Auto*Mat
""" % v.code,
                             from_email = u'Do práce na kole <kontakt@dopracenakole.net>',
                             to = [p.user.email()])
            email.send(fail_silently=True)

    # Return positive error code as per PayU protocol
    return http.HttpResponse("OK")

def login(request):
    return render_to_response('registration/payment_result.html',
                              {
            'pay_type': pay_type,
            'message': msg
            })

@login_required
def profile(request):

    days = util.days()
    weekdays = ['Po', 'Út', 'St', 'Čt', 'Pá']
    today = datetime.date.today()
    #today = datetime.date(year=2012, month=5, day=4)
    profile = request.user.get_profile()

    if request.method == 'POST':
        if 'day' in request.POST:
            try:
                trip = Trip.objects.get(user = request.user.get_profile(),
                                        date = days[int(request.POST['day'])-1])
            except Trip.DoesNotExist:
                trip = Trip()
                trip.date = days[int(request.POST['day'])-1]
                trip.user = request.user.get_profile()
            trip.trip_to = request.POST.get('trip_to', False)
            trip.trip_from = request.POST.get('trip_from', False)
            trip.save()
        # Pre-calculate total number of trips into userprofile to save load
        trip_counts = Trip.objects.filter(user=profile).values('user').annotate(Sum('trip_to'), Sum('trip_from'))
        try:
            profile.trips = trip_counts[0]['trip_to__sum'] + trip_counts[0]['trip_from__sum']
        except IndexError:
            profile.trips = 0
        profile.save()
    try:
        voucher_code = Voucher.objects.filter(user=profile)[0].code
    except IndexError, e:
        voucher_code = ''

    # Render profile
    payment_status = profile.payment_status()
    team_members = UserProfile.objects.filter(team=profile.team, active=True)

    trips = {}
    for t in Trip.objects.filter(user=profile):
        trips[t.date] = (t.trip_to, t.trip_from)
    calendar = []

    counter = 0
    for i, d in enumerate(days):
        cd = {}
        cd['name'] = "%s %d.%d." % (weekdays[d.weekday()], d.day, d.month)
        cd['iso'] = str(d)
        cd['question_active'] = (d <= today)
        cd['trips_active'] = (d <= today) and (
            len(Answer.objects.filter(
                    question=Question.objects.get(date = d),
                    user=request.user.get_profile())) > 0)
        if d in trips:
            cd['default_trip_to'] = trips[d][0]
            cd['default_trip_from'] = trips[d][1]
            counter += int(trips[d][0]) + int(trips[d][1])
        else:
            cd['default_trip_to'] = False
            cd['default_trip_from'] = False
        cd['percentage'] = float(counter)/(2*(i+1))*100
        cd['percentage_str'] = "%.0f" % (cd['percentage'])
        cd['distance'] = counter * profile.distance
        calendar.append(cd)

    member_counts = []
    for member in team_members:
        member_counts.append({
                'name': str(member),
                'trips': member.trips,
                'percentage': float(member.trips)/(2*util.days_count())*100,
                'distance': member.trips * member.distance})
    team_percentage = float(sum([m['trips'] for m in member_counts]))/(2*len(team_members)*util.days_count()) * 100
    team_distance = sum([m['distance'] for m in member_counts])

    for user_position, u in enumerate(UserResults.objects.filter(city=profile.team.city)):
        if u.id == profile.id:
            break
    user_position += 1

    for team_position, t in enumerate(TeamResults.objects.filter(city=profile.team.city)):
        if t.id == profile.team.id:
            break
    team_position += 1

    req_city = request.GET.get('mesto', None)
    if req_city and (req_city.lower() != profile.team.city.lower()):
        own_city = False
    else:
        own_city = True


    company_survey_answers = Answer.objects.filter(
        question_id=34, user__in = [m.id for m in team_members])
    if len(company_survey_answers):
        company_survey_by = company_survey_answers[0].user
        if company_survey_by == request.user.get_profile():
            company_survey_by = 'me'
    else:
        company_survey_by = None
    return render_to_response('registration/profile.html',
                              {
            'active': profile.active,
            'superuser': request.user.is_superuser,
            'user': request.user,
            'profile': profile,
            'team': profile.team,
            'payment_status': payment_status,
            'voucher': voucher_code,
            'team_members': ", ".join([str(p) for p in team_members]),
            'calendar': calendar,
            'member_counts': member_counts,
            'team_percentage': team_percentage,
            'team_distance': team_distance,
            'user_position': user_position,
            'team_position': team_position,
            'req_city': req_city,
            'own_city': own_city,
            'company_survey_by': company_survey_by,
            })

def results(request, template):

    city = request.GET.get('mesto', None)

    if city:
        user_by_percentage = UserResults.objects.filter(city=city)[:10]
        user_by_distance = UserResults.objects.filter(city=city).order_by('-distance')[:10]
        team_by_distance = TeamResults.objects.filter(city=city).order_by('-distance')[:20]
        team_by_percentage = TeamResults.objects.filter(city=city)
        user_count = UserResults.objects.filter(city=city).count()
        team_count = Team.objects.filter(city=city).count()
    else:
        user_by_percentage = UserResults.objects.all()[:10]
        user_by_distance = UserResults.objects.all().order_by('-distance')[:10]
        team_by_distance = TeamResults.objects.all().order_by('-distance')[:20]
        team_by_percentage = TeamResults.objects.all()
        user_count = UserProfile.objects.filter(active=True).count()
        team_count = Team.objects.all().count()

    return render_to_response(template,
                              {
            'user_by_percentage': user_by_percentage,
            'user_by_distance': user_by_distance,
            'team_by_percentage': team_by_percentage,
            'team_by_distance': team_by_distance,
            'city': city,
            'user_count': user_count,
            'team_count': team_count,
            })

class ProfileUpdateForm(forms.ModelForm):

    team_password = forms.CharField(
        label="Heslo nového týmu (pokud měníte tým)",
        max_length=20,
        required=False)

    class Meta:
        model = UserProfile
        fields = ('firstname', 'surname', 'telephone', 'distance', 'team', 'team_password')
    
    def clean_team_password(self):
        data = self.data['team_password']
        try:
            team = Team.objects.get(id=self.data['team'])
        except (Team.DoesNotExist, ValueError):
            raise forms.ValidationError("Neexistující nebo neplatný tým")
        if team != self.instance.team:
            # Change in team requested, validate team password
            if data.strip().lower() != team.password.strip():
                raise forms.ValidationError("Nesprávné heslo týmu")
        return data

@login_required
def update_profile(request):
    profile = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('/registrace/profil/')
    else:
        form = ProfileUpdateForm(instance=profile)
    return render_to_response('registration/update_profile.html',
                              {'form': form}
                              )

@login_required
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
                                   'day': request.GET.get('day', '')}
                                  )

@staff_member_required
def questions(request):
    questions = Question.objects.all().order_by('date')
    return render_to_response('admin/questions.html',
                              {'questions': questions})

@staff_member_required
def answers(request):
    question_id = request.GET['question']
    question = Question.objects.get(id=question_id)
    answers = Answer.objects.filter(question_id=question_id)
    total_respondents = len(answers)

    count = {'Praha': {}, 'Brno': {}, 'Liberec': {}}
    count_all = {}
    respondents = {'Praha': 0, 'Brno': 0, 'Liberec': 0}
    choice_names = {}

    if question.type in ('choice', 'multiple-choice'):
        for a in answers:
            city = a.user.city()
            a.city = a.user.city()
            respondents[city] += 1
            for c in a.choices.all():
                try:
                    count[city][c.id] += 1;
                except KeyError:
                    count[city][c.id] = 1
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
                               'answers': answers,
                               'stat': stat,
                               'total_respondents': total_respondents,
                               'choice_names': choice_names})
