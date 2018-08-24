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
import datetime
import hashlib
import json
import logging
import math
import socket
import time
from fm.views import AjaxCreateView
from http.client import HTTPSConnection
from urllib.parse import urlencode

# Django imports
from braces.views import LoginRequiredMixin

from class_based_auth_views.views import LoginView

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
from django.contrib.gis.db.models.functions import Length
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import BooleanField, Case, Count, F, FloatField, IntegerField, Q, Sum, When
from django.db.models.functions import Coalesce
from django.forms.models import BaseModelFormSet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import cache_control, cache_page, never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import CreateView, FormView, UpdateView

from extra_views import ModelFormSetView

from registration.backends.simple.views import RegistrationView as SimpleRegistrationView

from unidecode import unidecode

# Local imports
from . import draw
from . import exceptions
from . import forms
from . import models
from . import results
from . import util
from . import vacations
from .email import (
    approval_request_mail,
    invitation_mail,
    invitation_register_mail,
    team_created_mail,
    team_membership_approval_mail,
    team_membership_denial_mail,
)
from .forms import (
    ChangeTeamForm,
    InviteForm,
    PaymentTypeForm,
    ProfileUpdateForm,
    RegistrationAccessFormDPNK,
    RegistrationFormDPNK,
    TeamAdminForm,
    TrackUpdateForm,
)
from .models import Answer, Campaign, City, Company, Competition, Payment, Question, Subsidiary, Team, Trip, UserAttendance, UserProfile
from .string_lazy import mark_safe_lazy
from .views_mixins import (
    CampaignFormKwargsMixin,
    CampaignParameterMixin,
    RegistrationMessagesMixin,
    RegistrationViewMixin,
    TitleViewMixin,
    UserAttendanceFormKwargsMixin,
    UserAttendanceParameterMixin,
    UserAttendanceViewMixin,
)
from .views_permission_mixins import (
    GroupRequiredResponseMixin,
    MustBeApprovedForTeamMixin,
    MustBeInPaymentPhaseMixin,
    MustBeInRegistrationPhaseMixin,
    MustHaveTeamMixin,
    RegistrationCompleteMixin,
    registration_complete_gate,
)

logger = logging.getLogger(__name__)


class ProfileRedirectMixin(object):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('profil'))
        else:
            return super().get(request, *args, **kwargs)


class DPNKLoginView(CampaignFormKwargsMixin, TitleViewMixin, ProfileRedirectMixin, LoginView):
    def get_title(self, *args, **kwargs):
        return _("Přihlášení do soutěže %s") % self.campaign.name

    def get_initial(self):
        initial_email = self.kwargs.get('initial_email')
        if initial_email:
            return {'username': self.kwargs['initial_email']}
        else:
            return {}


class ChangeTeamView(RegistrationViewMixin, LoginRequiredMixin, UpdateView):
    form_class = ChangeTeamForm
    template_name = 'registration/change_team.html'
    next_url = 'zmenit_triko'
    prev_url = 'upravit_profil'
    registration_phase = "zmenit_tym"

    def get_title(self, *args, **kwargs):
        if self.user_attendance.team:
            action_text = _('Změnit')
        else:
            action_text = _('Vybrat')

        if self.user_attendance.approved_for_team == 'approved' and self.user_attendance.campaign.competitors_choose_team():
            subject_text = _('organizaci, pobočku a tým')
        else:
            subject_text = _('organizaci')
        return "%s %s" % (action_text, subject_text)

    def get_next_url(self):
        if self.user_attendance.approved_for_team == 'approved' and self.user_attendance.campaign.competitors_choose_team():
            return 'pozvanky'
        return super().get_next_url()

    def get_initial(self):
        if self.user_attendance.team:
            return {
                'subsidiary': self.user_attendance.team.subsidiary,
                'company': self.user_attendance.team.subsidiary.company,
            }
        else:
            previous_user_attendance = self.user_attendance.previous_user_attendance()
            if previous_user_attendance and previous_user_attendance.team:
                return {
                    'subsidiary': previous_user_attendance.team.subsidiary,
                    'company': previous_user_attendance.team.subsidiary.company,
                }

    def get_object(self):
        return self.user_attendance

    def dispatch(self, request, *args, **kwargs):
        if request.user_attendance and (
                request.user_attendance.approved_for_team == 'approved' and
                request.user_attendance.team and
                request.user_attendance.team.member_count == 1 and
                request.user_attendance.team.unapproved_member_count > 0
        ):
                raise exceptions.TemplatePermissionDenied(
                    _("Nemůžete opustit tým, ve kterém jsou samí neschválení členové. Napřed někoho schvalte a pak změňte tým."),
                    self.template_name,
                )
        return super().dispatch(request, *args, **kwargs)


class RegisterTeamView(UserAttendanceViewMixin, LoginRequiredMixin, AjaxCreateView):
    form_class = forms.RegisterTeamForm
    model = models.Team

    def get_success_result(self):
        team_created_mail(self.user_attendance, self.object.name)
        return {
            'status': 'ok',
            'name': self.object.name,
            'id': self.object.id,
        }

    def get_initial(self):
        previous_user_attendance = self.user_attendance.previous_user_attendance()
        return {
            'subsidiary': models.Subsidiary.objects.get(pk=self.kwargs['subsidiary_id']),
            'campaign': self.user_attendance.campaign,
            'name': previous_user_attendance.team.name if previous_user_attendance and previous_user_attendance.team else None,
        }


class RegisterCompanyView(LoginRequiredMixin, AjaxCreateView):
    form_class = forms.RegisterCompanyForm
    model = models.Company

    def get_success_result(self):
        return {
            'status': 'ok',
            'name': self.object.name,
            'id': self.object.id,
        }


class RegisterSubsidiaryView(CampaignFormKwargsMixin, UserAttendanceViewMixin, LoginRequiredMixin, AjaxCreateView):
    form_class = forms.RegisterSubsidiaryForm
    model = models.Subsidiary

    def get_initial(self):
        return {'company': models.Company.objects.get(pk=self.kwargs['company_id'])}

    def get_success_result(self):
        return {
            'status': 'ok',
            'id': self.object.id,
        }


class RegistrationAccessView(CampaignParameterMixin, TitleViewMixin, ProfileRedirectMixin, FormView):
    template_name = 'base_generic_form.html'
    form_class = RegistrationAccessFormDPNK

    def get_title(self, *args, **kwargs):
        return _("Registrujte se do soutěže %s") % self.campaign.name

    def form_valid(self, form):
        email = form.cleaned_data['email']
        if models.User.objects.filter(Q(email=email) | Q(username=email)).exists():
            return redirect(reverse('login', kwargs={'initial_email': email}))
        else:
            return redirect(reverse('registrace', kwargs={'initial_email': email}))


class RegistrationView(CampaignParameterMixin, TitleViewMixin, MustBeInRegistrationPhaseMixin, ProfileRedirectMixin, SimpleRegistrationView):
    template_name = 'base_generic_form.html'
    form_class = RegistrationFormDPNK
    model = UserProfile
    success_url = 'upravit_profil'

    def get_title(self, *args, **kwargs):
        return _("Registrujte se do soutěže %s") % self.campaign.name

    def get_initial(self):
        return {'email': self.kwargs.get('initial_email', '')}

    def register(self, registration_form):
        new_user = super().register(registration_form)
        userprofile = UserProfile.objects.create(user=new_user)

        invitation_token = self.kwargs.get('token', None)
        try:
            team = Team.objects.get(invitation_token=invitation_token)
            if team.is_full():
                messages.error(self.request, _('Tým do kterého jste byli pozváni je již plný, budete si muset vybrat nebo vytvořit jiný tým.'))
                team = None
        except Team.DoesNotExist:
            team = None
        user_attendance = UserAttendance.objects.create(
            userprofile=userprofile,
            campaign=self.campaign,
            team=team,
        )
        if team:
            approve_for_team(self.request, user_attendance, "", True, False)
        return new_user


class ConfirmTeamInvitationView(CampaignParameterMixin, RegistrationViewMixin, LoginRequiredMixin, SuccessMessageMixin, FormView):
    template_name = 'registration/team_invitation.html'
    form_class = forms.ConfirmTeamInvitationForm
    success_url = reverse_lazy('zmenit_tym')
    registration_phase = 'zmenit_tym'
    title = _("Pozvánka do týmu")
    success_message = _("Tým úspěšně změněn")

    def get_initial(self):
        return {
            'team': self.new_team,
            'campaign': self.campaign,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['old_team'] = self.user_attendance.team
        context['new_team'] = self.new_team

        if self.new_team.is_full():
            return {
                'fullpage_error_message': _('Tým do kterého jste byli pozváni je již plný, budete si muset vybrat nebo vytvořit jiný tým.'),
                'title': _("Tým je plný"),
            }

        if self.user_attendance.campaign != self.new_team.campaign:
            return {
                'fullpage_error_message': _("Přihlašujete se do týmu ze špatné kampaně (pravděpodobně z minulého roku)."),
                'title': _("Chyba přihlášení"),
            }
        return context

    def get_success_url(self):
        return self.success_url

    def form_valid(self, form):
        self.user_attendance.team = self.new_team
        approve_for_team(self.request, self.user_attendance, "", True, False)
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if Team.objects.filter(invitation_token=kwargs['token']).count() != 1:
            raise exceptions.TemplatePermissionDenied(
                _("Tým nenalezen"),
                self.template_name,
            )

        initial_email = kwargs['initial_email']
        if request.user.is_authenticated and request.user.email != initial_email:
            logout(request)
            messages.add_message(
                self.request,
                messages.WARNING,
                _("Pozvánka je určena jinému uživateli, než je aktuálně přihlášen. Přihlašte se jako uživatel %s." % initial_email),
            )
            return redirect("%s?next=%s" % (reverse("login", kwargs={"initial_email": initial_email}), request.get_full_path()))
        invitation_token = self.kwargs['token']
        self.new_team = Team.objects.get(invitation_token=invitation_token)
        return super().dispatch(request, *args, **kwargs)


class PaymentTypeView(
        UserAttendanceFormKwargsMixin,
        RegistrationViewMixin,
        MustBeInPaymentPhaseMixin,
        MustHaveTeamMixin,
        LoginRequiredMixin,
        FormView,
):
    template_name = 'registration/payment_type.html'
    title = _("Platba")
    registration_phase = "typ_platby"
    next_url = "profil"
    prev_url = "zmenit_triko"

    def dispatch(self, request, *args, **kwargs):
        if request.user_attendance:
            if request.user_attendance.has_paid():
                if request.user_attendance.payment_status == 'done':
                    message = _("Již máte účastnický poplatek zaplacen.")
                else:
                    message = _("Účastnický poplatek se neplatí.")
                raise exceptions.TemplatePermissionDenied(
                    mark_safe_lazy(message + " " + _("Pokračujte na <a href='%s'>zadávání jízd</a>.") % reverse("profil")),
                    self.template_name,
                )
            if request.user_attendance.campaign.has_any_tshirt and not request.user_attendance.t_shirt_size:
                raise exceptions.TemplatePermissionDenied(
                    _("Před tím, než zaplatíte účastnický poplatek, musíte mít vybrané triko"),
                    self.template_name,
                )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.user_attendance.userprofile
        context['user_attendance'] = self.user_attendance
        context['firstname'] = profile.user.first_name  # firstname
        context['surname'] = profile.user.last_name  # surname
        context['email'] = profile.user.email  # email
        context['amount'] = self.user_attendance.admission_fee()
        context['beneficiary_amount'] = self.user_attendance.beneficiary_admission_fee()
        context['prev_url'] = self.prev_url
        return context

    def get_form(self, form_class=PaymentTypeForm):
        form = super().get_form(form_class)
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
                    _(
                        "Platbu ještě musí schválit koordinátor vaší organizace {email}. "
                    ),
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
                _("Pokud jste se dostali sem, tak to může být způsobené tím, že používáte zastaralý prohlížeč nebo máte vypnutý JavaScript."),
                status=500,
            )
        else:
            payment_choice = payment_choices[payment_type]
            if payment_choice:
                Payment(
                    user_attendance=self.user_attendance,
                    amount=payment_choice['amount'],
                    pay_type=payment_choice['type'],
                    status=models.Status.NEW,
                ).save()
                messages.add_message(self.request, messages.WARNING, payment_choice['message'], fail_silently=True)
                logger.info('Inserting payment', extra={'payment_type': payment_type, 'username': self.user_attendance.userprofile.user.username})

        return super().form_valid(form)


class PaymentView(UserAttendanceViewMixin, MustHaveTeamMixin, LoginRequiredMixin, TemplateView):
    beneficiary = False
    template_name = 'registration/payment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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


class PaymentResult(UserAttendanceViewMixin, LoginRequiredMixin, TemplateView):
    registration_phase = 'typ_platby'
    template_name = 'registration/payment_result.html'

    def dispatch(self, request, *args, **kwargs):
        payment = Payment.objects.get(session_id=kwargs['session_id'])
        if hasattr(self.request, 'campaign') and payment.user_attendance:
            if payment.user_attendance.campaign != self.request.campaign:
                return redirect(util.get_redirect(request, slug=payment.user_attendance.campaign.slug))
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def get_context_data(self, success, trans_id, session_id, pay_type, error=None):
        context_data = super().get_context_data()
        logger.info(
            u'Payment result: success: %s, trans_id: %s, session_id: %s, pay_type: %s, error: %s, user: %s (%s)' %
            (
                success,
                trans_id,
                session_id,
                pay_type,
                error,
                self.user_attendance,
                self.user_attendance.userprofile.user.username,
            ),
        )

        if session_id and session_id != "":
            payment = Payment.objects.select_for_update().get(session_id=session_id)
            if payment.status not in Payment.done_statuses:
                if success:
                    payment.status = models.Status.COMMENCED
                else:
                    payment.status = models.Status.REJECTED
            if not payment.trans_id:
                payment.trans_id = trans_id
            if not payment.pay_type:
                payment.pay_type = pay_type
            if not payment.error:
                payment.error = error
            payment.save()

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
                    'user': self.user_attendance.userprofile.user,
                    'request': self.request,
                },
            )
            context_data['payment_message'] = _("Vaše platba se nezdařila. Po přihlášení do svého profilu můžete zadat novou platbu.")
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
@csrf_exempt
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
    for i in [i.split(':', 1) for i in raw_response.split('\n') if i.strip() != '']:
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

    @property
    def initial_forms(self):
        """Return a list of all the initial forms in this formset."""
        return [form for form in self.forms if form.instance.pk is not None]

    @property
    def extra_forms(self):
        """Return a list of all the extra forms in this formset."""
        return [form for form in self.forms if form.instance.pk is None]


class RidesView(RegistrationCompleteMixin, TitleViewMixin, RegistrationMessagesMixin, SuccessMessageMixin, ModelFormSetView):
    model = Trip
    form_class = forms.TripForm
    formset_class = RidesFormSet
    fields = ('commute_mode', 'distance', 'direction', 'user_attendance', 'date')
    extra = 0
    uncreated_trips = []
    success_message = _("Tabulka jízd úspěšně změněna")
    registration_phase = 'profile_view'
    template_name = 'registration/competition_profile.html'
    title = _('Stav registrace')
    opening_message = mark_safe_lazy(
        string_concat(
            '<b class="text-success">',
            _("Vaše registrace je kompletní."),
            '</b><br/>',
        ),
    )

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
            trips = self.trips.annotate(  # fetch only needed fields
                track_isnull=Case(When(track__isnull=True, then=True), default=False, output_field=BooleanField()),
            ).defer('track', 'gpx_file')
            return trips
        else:
            return models.Trip.objects.none()

    def get_initial(self):
        distance = self.user_attendance.get_distance()
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
        context_data['today'] = util.today()
        context_data['num_columns'] = 3 if campaign.recreational else 2
        return context_data


class RidesDetailsView(RegistrationCompleteMixin, TitleViewMixin, RegistrationMessagesMixin, TemplateView):
    title = _("Podrobný přehled jízd")
    template_name = 'registration/rides_details.html'
    registration_phase = 'profile_view'

    def get_context_data(self, *args, **kwargs):
        trips, uncreated_trips = self.user_attendance.get_all_trips(util.today())
        uncreated_trips = [
            {
                'date': trip[0],
                'get_direction_display': models.Trip.DIRECTIONS_DICT[trip[1]],
                'get_commute_mode_display': _('Jinak') if util.working_day(trip[0]) else _('Žádná cesta'),
                'distance': None,
                'direction': trip[1],
                'active': self.user_attendance.campaign.day_active(trip[0]),
            } for trip in uncreated_trips
        ]
        trips = list(trips) + uncreated_trips
        trips = sorted(trips, key=lambda trip: trip.direction if type(trip) == Trip else trip['get_direction_display'], reverse=True)
        trips = sorted(trips, key=lambda trip: trip.date if type(trip) == Trip else trip['date'])

        context_data = super().get_context_data(*args, **kwargs)
        context_data['trips'] = trips
        days = list(util.days(self.user_attendance.campaign.phase("competition"), util.today()))
        context_data['other_trips'] = models.Trip.objects.filter(user_attendance=self.user_attendance).exclude(date__in=days)
        return context_data


class VacationsView(RegistrationCompleteMixin, TitleViewMixin, RegistrationMessagesMixin, TemplateView):
    title = _("Dovolená")
    template_name = 'registration/vacations.html'
    registration_phase = 'profile_view'

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data.update({
            "possible_vacation_days": json.dumps([str(day) for day in self.user_attendance.campaign.possible_vacation_days()]),
            "first_vid": vacations.get_vacations(self.user_attendance)[1],
            "events": json.dumps(vacations.get_events(self.request)),
        })
        return context_data

    def post(self, request, *args, **kwargs):
        on_vacation = request.POST.get('on_vacation', False)
        on_vacation = on_vacation == 'true'
        start_date = util.parse_date(request.POST.get('start_date', None))
        end_date = util.parse_date(request.POST.get('end_date', None))
        possible_vacation_days = self.user_attendance.campaign.possible_vacation_days()
        if not start_date <= end_date:
            raise exceptions.TemplatePermissionDenied(_("Data musí být seřazena chronologicky"))
        if not {start_date, end_date}.issubset(possible_vacation_days):
            raise exceptions.TemplatePermissionDenied(_("Není povoleno editovat toto datum"))
        existing_trips = Trip.objects.filter(
            user_attendance=self.user_attendance,
            date__gte=start_date,
            date__lte=end_date,
        )
        no_work = models.CommuteMode.objects.get(slug='no_work')
        if on_vacation:
            for date in util.daterange(start_date, end_date):
                for direction in ['trip_to', 'trip_from']:
                    Trip.objects.update_or_create(
                        user_attendance=self.user_attendance,
                        date=date,
                        direction=direction,
                        defaults={'commute_mode': no_work},
                    )
        else:
            existing_trips.delete()
        return HttpResponse("OK")


class DiplomasView(TitleViewMixin, UserAttendanceViewMixin, LoginRequiredMixin, TemplateView):
    title = _("Váše diplomy a výsledky v minulých ročnících")
    template_name = 'registration/diplomas.html'
    registration_phase = 'profile_view'

    def get_context_data(self, *args, **kwargs):
        user_attendances = self.user_attendance.userprofile.userattendance_set.all().order_by('-id')
        teams = []
        for ua in self.user_attendance.userprofile.userattendance_set.all():
            if ua.team:
                teams.append(ua.team)
        context_data = super().get_context_data(*args, **kwargs)
        context_data['user_attendances'] = user_attendances
        context_data['teams'] = teams
        return context_data


class RegistrationUncompleteForm(TitleViewMixin, RegistrationMessagesMixin, LoginRequiredMixin, TemplateView):
    template_name = 'base_generic_form.html'
    title = _('Stav registrace')
    opening_message = mark_safe_lazy(
        string_concat(
            '<b class="text-warning">',
            _("Vaše registrace není kompletní."),
            '</b><br/>',
            _("K dokončení registrace bude ještě nutné vyřešit několik věcí:"),
        ),
    )
    registration_phase = 'registration_uncomplete'

    def get(self, request, *args, **kwargs):
        reason = self.user_attendance.entered_competition_reason()
        if reason is True:
            return redirect(reverse('profil'))
        else:
            return super().get(request, *args, **kwargs)


class UserAttendanceView(TitleViewMixin, UserAttendanceViewMixin, LoginRequiredMixin, TemplateView):
    pass


class PackageView(RegistrationViewMixin, LoginRequiredMixin, TemplateView):
    template_name = "registration/package.html"
    title = _("Sledování balíčku")
    registration_phase = "zmenit_tym"


class ApplicationView(RegistrationViewMixin, LoginRequiredMixin, TemplateView):
    template_name = "registration/applications.html"
    title = _("Aplikace")
    registration_phase = "application"


class OtherTeamMembers(UserAttendanceViewMixin, TitleViewMixin, MustBeApprovedForTeamMixin, LoginRequiredMixin, TemplateView):
    template_name = 'registration/team_members.html'
    title = _("Výsledky členů týmu")

    @method_decorator(never_cache)
    @method_decorator(cache_control(max_age=0, no_cache=True, no_store=True))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
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


class CompetitionsRulesView(CampaignFormKwargsMixin, TitleViewMixin, TemplateView):
    title_base = _("Pravidla soutěží")

    def get_title(self, *args, **kwargs):
        city = get_object_or_404(City, slug=kwargs['city_slug'])
        return "%s - %s" % (self.title_base, city)

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        city_slug = kwargs['city_slug']
        competitions = Competition.objects.filter(
            Q(city__slug=city_slug) | Q(city__isnull=True, company=None),
            campaign=self.campaign,
            is_public=True,
        )
        context_data['competitions'] = competitions
        context_data['city_slug'] = city_slug
        context_data['campaign_slug'] = self.campaign.slug
        return context_data


class AdmissionsView(UserAttendanceViewMixin, TitleViewMixin, LoginRequiredMixin, TemplateView):
    title = _("Výsledky soutěží")
    success_url = reverse_lazy("competitions")
    competition_types = None

    @method_decorator(never_cache)
    @method_decorator(cache_control(max_age=0, no_cache=True, no_store=True))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data['competitions'] = self.user_attendance.get_competitions(competition_types=self.competition_types)
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

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        competition_slug = kwargs.get('competition_slug')

        try:
            context_data['competition'] = Competition.objects.get(slug=competition_slug)
        except Competition.DoesNotExist:
            logger.info('Unknown competition', extra={'slug': competition_slug, 'request': self.request})
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


class UpdateProfileView(CampaignFormKwargsMixin, RegistrationViewMixin, LoginRequiredMixin, UpdateView):
    template_name = 'base_generic_registration_form.html'
    form_class = ProfileUpdateForm
    model = UserProfile
    success_message = _("Osobní údaje úspěšně upraveny")
    next_url = "zmenit_tym"
    registration_phase = "upravit_profil"
    title = _("Osobní údaje")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            instance={
                'user': self.user_attendance.userprofile.user,
                'userprofile': self.user_attendance.userprofile,
                'userattendance': self.user_attendance,
            },
        )
        return kwargs


class UpdateTrackView(RegistrationViewMixin, LoginRequiredMixin, UpdateView):
    template_name = 'registration/change_track.html'
    form_class = TrackUpdateForm
    model = UserAttendance
    success_message = _("Trasa/vzdálenost úspěšně upravena")
    success_url = 'profil'
    registration_phase = "upravit_profil"
    title = _("Upravit typickou trasu")

    def get_object(self):
        return self.user_attendance


class QuestionnaireView(TitleViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'registration/questionaire.html'
    success_url = reverse_lazy('profil')
    title = _("Vyplňte odpovědi")
    form_class = forms.AnswerForm

    def dispatch(self, request, *args, **kwargs):
        questionaire_slug = kwargs['questionnaire_slug']
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        self.user_attendance = request.user_attendance
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
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        if not self.is_actual:
            return HttpResponse(string_concat("<div class='text-warning'>", _("Soutěž již nelze vyplňovat"), "</div>"))

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
            # TODO: use Celery for this
            results.recalculate_result_competitor(self.user_attendance)
            messages.add_message(request, messages.SUCCESS, _("Odpovědi byly úspěšně zadány"))
            return redirect(self.success_url)
        context_data = self.get_context_data()
        context_data['invalid_count'] = invalid_count
        return render(request, self.template_name, context_data)

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)

        context_data.update({
            'questions': self.questions,
            'questionaire': self.competition,
            'show_submit': self.is_actual,
            'show_points': self.show_points,
        })
        return context_data


class QuestionnaireAnswersAllView(TitleViewMixin, TemplateView):
    template_name = 'registration/questionnaire_answers_all.html'
    title = _("Výsledky všech soutěží")

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)

        competition_slug = kwargs.get('competition_slug')
        competition = Competition.objects.get(slug=competition_slug)
        if (
                not competition.public_answers and
                not self.request.user.is_superuser and
                self.request.user.userprofile.competition_edition_allowed(competition)
        ):
            context_data['fullpage_error_message'] = _("Tato soutěž nemá povolené prohlížení odpovědí.")
            context_data['title'] = _("Odpovědi nejsou dostupné")
            return context_data

        competitors = competition.get_results()
        competitors = competitors.select_related('user_attendance__team__subsidiary__city', 'user_attendance__userprofile__user')

        for competitor in competitors:
            competitor.answers = Answer.objects.filter(
                user_attendance__in=competitor.user_attendances(),
                question__competition__slug=competition_slug,
            ).select_related('question')
        context_data['show_points'] = (
            competition.has_finished() or
            (self.request.user.is_authenticated and
             self.request.user.userprofile.user.is_superuser)
        )
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
        return HttpResponse(string_concat("<div class='text-warning'>", _("Soutěž je vypsána ve městě, pro které nemáte oprávnění."), "</div>"))

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
        return HttpResponse(string_concat("<div class='text-warning'>", _("Soutěž je vypsána ve městě, pro které nemáte oprávnění."), "</div>"))

    try:
        competitor_result = competition.get_results().get(pk=request.GET['uid'])
    except models.CompetitionResult.DoesNotExist:
        return HttpResponse(_('<div class="text-danger">Nesprávně zadaný soutěžící.</div>'), status=401)
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
        return HttpResponse(
            string_concat("<div class='text-warning'>", _("Otázka je položená ve městě, pro které nemáte oprávnění."), "</div>"),
            status=401,
        )

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
                _("Při zamítnutí člena týmu musíte vyplnit zprávu."),
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
            _("Členství uživatele %s ve vašem týmu bylo zamítnuto" % user_attendance),
            extra_tags="user_attendance_%s" % user_attendance.pk,
            fail_silently=True,
        )
        return
    elif approve:
        if user_attendance.campaign.too_much_members(user_attendance.team.members().count() + 1):
            messages.add_message(
                request,
                messages.ERROR,
                _("Tým je již plný, další člen již nemůže být potvrzen."),
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
            _("Členství uživatele %(user)s v týmu %(team)s bylo odsouhlaseno.") %
            {"user": user_attendance, "team": user_attendance.team.name},
            extra_tags="user_attendance_%s" % user_attendance.pk,
            fail_silently=True,
        )
        return


class TeamApprovalRequest(TitleViewMixin, UserAttendanceViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'registration/request_team_approval.html'
    title = _("Znovu odeslat žádost o členství")
    registration_phase = "zmenit_tym"

    def dispatch(self, request, *args, **kwargs):
        if request.user_attendance:
            approval_request_mail(request.user_attendance)
        return super().dispatch(request, *args, **kwargs)


class InviteView(UserAttendanceViewMixin, MustBeInRegistrationPhaseMixin, TitleViewMixin, MustBeApprovedForTeamMixin, LoginRequiredMixin, FormView):
    template_name = 'base_generic_registration_form.html'
    form_class = InviteForm
    title = _('Pozvětě své kolegy do týmu')
    registration_phase = "zmenit_tym"
    success_url = reverse_lazy('pozvanky')

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data['registration_phase'] = self.registration_phase
        return context_data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user_attendance'] = self.user_attendance
        return kwargs

    def form_valid(self, form):
        for email in form.cleaned_data.values():
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
                            _("Uživatel %(user)s byl přijat do vašeho týmu.") % {"user": invited_user_attendance, "email": email},
                            fail_silently=True,
                        )
                    else:
                        invitation_register_mail(self.user_attendance, invited_user_attendance)
                        messages.add_message(
                            self.request,
                            messages.SUCCESS,
                            _("Odeslána pozvánka uživateli %(user)s na e-mail %(email)s") % {"user": invited_user_attendance, "email": email},
                            fail_silently=True,
                        )
                except models.User.DoesNotExist:
                    invitation_mail(self.user_attendance, email)
                    messages.add_message(self.request, messages.SUCCESS, _("Odeslána pozvánka na e-mail %s") % email, fail_silently=True)

        invite_success_url = self.request.session.get('invite_success_url')
        self.request.session['invite_success_url'] = None
        return redirect(invite_success_url or self.success_url)


class UpdateTeam(
        TitleViewMixin,
        CampaignParameterMixin,
        UserAttendanceParameterMixin,
        MustBeInRegistrationPhaseMixin,
        SuccessMessageMixin,
        MustBeApprovedForTeamMixin,
        LoginRequiredMixin,
        UpdateView,
):
    template_name = 'base_generic_form.html'
    form_class = TeamAdminForm
    success_url = reverse_lazy('edit_team')
    title = _("Upravit název týmu")
    registration_phase = 'zmenit_tym'
    success_message = _("Název týmu úspěšně změněn na %(name)s")

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data['registration_phase'] = self.registration_phase
        return context_data

    def get_object(self):
        return self.user_attendance.team

    def get_initial(self):
        return {'campaign': self.campaign}


class TeamMembers(
        TitleViewMixin,
        UserAttendanceViewMixin,
        MustBeInRegistrationPhaseMixin,
        MustBeApprovedForTeamMixin,
        LoginRequiredMixin,
        TemplateView,
):
    template_name = 'registration/team_admin_members.html'
    registration_phase = "zmenit_tym"
    title = _("Schvalování členů týmu")

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if 'approve' in request.POST:
            approve_id = None
            try:
                action, approve_id = request.POST['approve'].split('-')
            except ValueError:
                logger.exception('Can\'t split POST approve parameter', extra={'request': request})
                messages.add_message(
                    request,
                    messages.ERROR,
                    _("Nastala chyba při přijímání uživatele, patrně používáte zastaralý internetový prohlížeč."),
                )

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
                    approve_for_team(
                        request,
                        approved_user,
                        request.POST.get('reason-' + str(approved_user.id), ''),
                        action == 'approve',
                        action == 'deny',
                    )
        return render(request, self.template_name, self.get_context_data())

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        team = self.user_attendance.team
        if not team:
            return {
                'fullpage_error_message': _("Další členové vašeho týmu se zobrazí, jakmile budete mít vybraný tým"),
                'title': _("Není vybraný tým"),
            }

        unapproved_users = []
        for self.user_attendance in UserAttendance.objects.filter(team=team, userprofile__user__is_active=True):
            userprofile = self.user_attendance.userprofile
            unapproved_users.append([
                ('state', None, self.user_attendance.approved_for_team),
                ('id', None, str(self.user_attendance.id)),
                ('class', None, self.user_attendance.payment_class()),
                ('name', _("Jméno"), str(userprofile)),
                ('email', _("E-mail"), userprofile.user.email),
                ('payment_description', _("Platba"), self.user_attendance.get_payment_status_display()),
                ('telephone', _("Telefon"), userprofile.telephone),
                ('state_name', _("Stav"), str(self.user_attendance.get_approved_for_team_display())),
            ])
        context_data['unapproved_users'] = unapproved_users
        context_data['registration_phase'] = self.registration_phase
        return context_data


def distance_all_modes(trips):
    return trips.filter(commute_mode__eco=True, commute_mode__does_count=True).aggregate(
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
        Q(payment_status='done'),
    ).exclude(Q(transactions__payment__pay_type__in=models.Payment.NOT_PAYING_TYPES)).distinct().count()
    variables['pocet-prihlasenych'] = UserAttendance.objects.filter(campaign=campaign).distinct().count()
    variables['pocet-soutezicich'] = UserAttendance.objects.filter(
        Q(campaign=campaign) &
        Q(payment_status='done'),
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

    @method_decorator(cache_page(60))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        campaign_slug = self.request.subdomain
        context_data['campaign_slug'] = campaign_slug
        cities = City.objects.\
            filter(subsidiary__teams__users__payment_status='done', subsidiary__teams__users__campaign__slug=campaign_slug).\
            annotate(competitor_count=Count('subsidiary__teams__users')).\
            order_by('-competitor_count')
        for city in cities:
            city.distances = distance_all_modes(
                models.Trip.objects.filter(
                    user_attendance__payment_status='done',
                    user_attendance__team__subsidiary__city=city,
                    user_attendance__campaign__slug=campaign_slug,
                ),
            )
            city.emissions = util.get_emissions(city.distances['distance__sum'])
        context_data['cities'] = cities
        context_data['without_city'] =\
            UserAttendance.objects.\
            filter(payment_status='done', campaign__slug=campaign_slug, team=None)
        context_data['total'] =\
            UserAttendance.objects.\
            filter(payment_status='done', campaign__slug=campaign_slug)
        context_data['total_distances'] = distance_all_modes(
            models.Trip.objects.filter(
                user_attendance__payment_status='done',
                user_attendance__campaign__slug=campaign_slug,
            ),
        )
        context_data['total_emissions'] = util.get_emissions(context_data['total_distances']['distance__sum'])
        return context_data


class BikeRepairView(CampaignParameterMixin, TitleViewMixin, GroupRequiredResponseMixin, LoginRequiredMixin, CreateView):
    group_required = 'cykloservis'
    template_name = 'base_generic_form.html'
    form_class = forms.BikeRepairForm
    success_url = 'bike_repair'
    success_message = _("%(user_attendance)s je nováček a právě si zažádal o opravu kola")
    model = models.CommonTransaction
    title = _("Cykloservis")

    def get_initial(self):
        return {'campaign': self.campaign}

    def form_valid(self, form):
        super().form_valid(form)
        return redirect(reverse(self.success_url))


class DrawResultsView(TitleViewMixin, TemplateView):
    template_name = 'admin/draw.html'
    title = _("Losování")

    def get_context_data(self, city_slug=None, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        competition_slug = kwargs.get('competition_slug')
        context_data['results'] = draw.draw(competition_slug)
        return context_data


class CombinedTracksKMLView(TemplateView):
    template_name = "gis/tracks.kml"

    @method_decorator(gzip_page)
    @method_decorator(never_cache)              # don't cache KML in browsers
    @method_decorator(cache_page(24 * 60 * 60))  # cache in memcached for 24h
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, city_slug=None, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        filter_params = {}
        if city_slug:
            filter_params['team__subsidiary__city__slug'] = city_slug
        user_attendances = models.UserAttendance.objects.filter(campaign__slug=self.request.subdomain, **filter_params).kml()
        context_data['user_attendances'] = user_attendances
        return context_data


def view_edit_trip(request, date, direction):
    incomplete = registration_complete_gate(request.user_attendance)
    if incomplete is not None:
        return incomplete
    parse_error = False
    try:
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        parse_error = True
    if parse_error:
        raise exceptions.TemplatePermissionDenied(_("Nemůžete editovat cesty ke starším datům."))
    if direction not in ["trip_to", "trip_from", "recreational"]:
        raise exceptions.TemplatePermissionDenied(_("Neplatný směr cesty."))
    if not request.user_attendance.campaign.day_active(date):
        return TripView.as_view()(request, date=date, direction=direction)
    if models.Trip.objects.filter(user_attendance=request.user_attendance, date=date, direction=direction).exists():
        return UpdateTripView.as_view()(request, date=date, direction=direction)
    else:
        return CreateTripView.as_view()(request, date=date, direction=direction)


class EditTripView(TitleViewMixin, UserAttendanceParameterMixin, SuccessMessageMixin, LoginRequiredMixin):
    form_class = forms.TrackTripForm
    model = models.Trip
    template_name = "registration/trip.html"
    title = _("Zadat trasu")

    def get_initial(self, initial=None):
        if initial is None:
            initial = {}
        initial['origin'] = self.request.META.get('HTTP_REFERER', reverse_lazy("profil"))
        initial['user_attendance'] = self.user_attendance
        return initial

    def form_valid(self, form):
        self.success_url = form.data['origin']
        return super().form_valid(form)


class WithTripMixin():
    def get_object(self, queryset=None):
        return get_object_or_404(
            models.Trip,
            user_attendance=self.request.user_attendance,
            direction=self.kwargs['direction'],
            date=self.kwargs['date'],
        )


class UpdateTripView(EditTripView, WithTripMixin, UpdateView):
    def get_initial(self):
        initial = {}
        instance = self.get_object()
        if instance.track is None and self.user_attendance.track:
                initial['track'] = self.user_attendance.track
        if not instance.distance:
                initial['distance'] = self.user_attendance.get_distance()
        return super().get_initial(initial)


class CreateTripView(EditTripView, CreateView):
    def get_initial(self):
        if self.user_attendance.track:
            track = self.user_attendance.track
        else:
            track = None
        initial = {
            'direction': self.kwargs['direction'],
            'date': self.kwargs['date'],
            'track': track,
            'distance': self.user_attendance.distance,
        }
        return super().get_initial(initial)


class TripView(TitleViewMixin, LoginRequiredMixin, WithTripMixin, TemplateView):
    template_name = 'registration/view_trip.html'
    title = _("Prohlédnout trasu")

    def get_context_data(self, *args, **kwargs):
        trip = self.get_object()
        context = {
            "title": self.title,
            "days_active": trip.user_attendance.campaign.days_active,
        }
        context["trip"] = trip
        return context


class TripGeoJsonView(LoginRequiredMixin, WithTripMixin, View):
    def get(self, *args, **kwargs):
        if self.get_object().track:
            track_json = self.get_object().track.geojson
        else:
            track_json = {}
        return HttpResponse(track_json)


def status(request):
    status_page = str(datetime.datetime.now()) + '\n'
    status_page += socket.gethostname()
    return HttpResponse(status_page)
