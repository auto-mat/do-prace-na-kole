import codecs
import hashlib
import logging
import math
import time
from fm.views import AjaxCreateView
from http.client import HTTPSConnection
from urllib.parse import urlencode

# Django imports
from braces.views import LoginRequiredMixin

from class_based_auth_views.views import LoginView

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView, UpdateView

from registration.backends.default.views import (
    RegistrationView as SimpleRegistrationView,
)

from unidecode import unidecode

from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

from t_shirt_delivery.models import TShirtSize

# Local imports
from .team import approve_for_team
from .. import exceptions
from .. import forms
from .. import models
from .. import util
from ..email import (
    approval_request_mail,
    invitation_mail,
    team_created_mail,
)
from ..forms import (
    ChangeTeamForm,
    InviteForm,
    PaymentTypeForm,
    ProfileUpdateForm,
    RegistrationAccessFormDPNK,
    RegistrationFormDPNK,
    RegistrationProfileUpdateForm,
)
from ..models import Payment, Team, UserAttendance, UserProfile
from ..views_mixins import (
    CampaignFormKwargsMixin,
    CampaignParameterMixin,
    ProfileRedirectMixin,
    RegistrationMessagesMixin,
    RegistrationPersonalViewMixin,
    RegistrationViewMixin,
    TitleViewMixin,
    UserAttendanceFormKwargsMixin,
    UserAttendanceViewMixin,
)
from ..views_permission_mixins import (
    MustBeApprovedForTeamMixin,
    MustBeInPaymentPhaseMixin,
    MustBeInRegistrationPhaseMixin,
    MustHaveTeamMixin,
)

logger = logging.getLogger(__name__)


class DPNKLoginView(
    CampaignFormKwargsMixin, TitleViewMixin, ProfileRedirectMixin, LoginView
):
    title = ""

    def get_initial(self):
        initial_email = self.kwargs.get("initial_email")
        if initial_email:
            return {"username": self.kwargs["initial_email"]}
        else:
            return {}


class ChangeTeamView(RegistrationViewMixin, LoginRequiredMixin, UpdateView):
    form_class = ChangeTeamForm
    template_name = "dpnk/change_team.html"
    next_url = "zmenit_triko"
    prev_url = "upravit_profil"
    registration_phase = "zmenit_tym"

    def get_title(self, *args, **kwargs):
        if self.user_attendance.team:
            if self.user_attendance.campaign.competitors_choose_team():
                return _("Vyberte jiný tým")
            else:
                return _("Vyberte jinou společnost")
        else:
            if self.user_attendance.campaign.competitors_choose_team():
                return _("Přidejte se k týmu")
            else:
                return _("Vyhledejte svoji společnost")

    def get_initial(self):
        if self.user_attendance.team:
            return {
                "subsidiary": self.user_attendance.team.subsidiary,
                "company": self.user_attendance.team.subsidiary.company,
            }
        else:
            previous_user_attendance = self.user_attendance.previous_user_attendance()
            if previous_user_attendance and previous_user_attendance.team:
                return {
                    "subsidiary": previous_user_attendance.team.subsidiary,
                    "company": previous_user_attendance.team.subsidiary.company,
                }

    def get_object(self):
        return self.user_attendance

    def dispatch(self, request, *args, **kwargs):
        if request.user_attendance and (
            request.user_attendance.approved_for_team == "approved"
            and request.user_attendance.team
            and request.user_attendance.team.member_count == 1
            and request.user_attendance.team.unapproved_member_count > 0
        ):
            raise exceptions.TemplatePermissionDenied(
                _(
                    "Nemůžete opustit tým, ve kterém jsou samí neschválení členové. Napřed někoho schvalte a pak změňte tým."
                ),
                self.template_name,
            )
        return super().dispatch(request, *args, **kwargs)


class RegisterTeamView(UserAttendanceViewMixin, LoginRequiredMixin, AjaxCreateView):
    form_class = forms.RegisterTeamForm
    model = models.Team

    def get_success_result(self):
        team_created_mail(self.user_attendance, self.object.name)
        return {
            "status": "ok",
            "name": self.object.name,
            "id": self.object.id,
        }

    def get_initial(self):
        previous_user_attendance = self.user_attendance.previous_user_attendance()
        return {
            "subsidiary": models.Subsidiary.objects.get(
                pk=self.kwargs["subsidiary_id"]
            ),
            "campaign": self.user_attendance.campaign,
            "name": previous_user_attendance.team.name
            if previous_user_attendance and previous_user_attendance.team
            else None,
        }


class RegisterCompanyView(LoginRequiredMixin, AjaxCreateView):
    form_class = forms.RegisterCompanyForm
    model = models.Company

    def get_success_result(self):
        return {
            "status": "ok",
            "name": self.object.name,
            "id": self.object.id,
        }


class RegisterSubsidiaryView(
    CampaignFormKwargsMixin, UserAttendanceViewMixin, LoginRequiredMixin, AjaxCreateView
):
    form_class = forms.RegisterSubsidiaryForm
    model = models.Subsidiary

    def get_initial(self):
        return {"company": models.Company.objects.get(pk=self.kwargs["company_id"])}

    def get_success_result(self):
        return {
            "status": "ok",
            "name": self.object.name(),
            "id": self.object.id,
        }


class RegistrationAccessView(
    CampaignParameterMixin,
    TitleViewMixin,
    ProfileRedirectMixin,
    FormView,
):
    template_name = "dpnk/base_login_registration.html"
    form_class = RegistrationAccessFormDPNK
    title = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form_class()({"campaign": self.campaign})
        return context

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        if models.User.objects.filter(Q(email=email) | Q(username=email)).exists():
            return redirect(reverse("login", kwargs={"initial_email": email}))
        else:
            return redirect(reverse("registrace", kwargs={"initial_email": email}))


class RegistrationView(
    CampaignParameterMixin,
    TitleViewMixin,
    MustBeInRegistrationPhaseMixin,
    ProfileRedirectMixin,
    SimpleRegistrationView,
):
    template_name = "dpnk/base_login_registration.html"
    form_class = RegistrationFormDPNK
    model = UserProfile
    title = ""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["invitation_token"] = self.kwargs.get("token", None)
        kwargs["campaign"] = self.campaign
        kwargs["request"] = self.request
        return kwargs

    def get_initial(self):
        return {"email": self.kwargs.get("initial_email", "")}


class ConfirmTeamInvitationView(
    CampaignParameterMixin,
    RegistrationViewMixin,
    LoginRequiredMixin,
    SuccessMessageMixin,
    FormView,
):
    template_name = "dpnk/team_invitation.html"
    form_class = forms.ConfirmTeamInvitationForm
    success_url = reverse_lazy("zmenit_tym")
    registration_phase = "zmenit_tym"
    title = _("Pozvánka do týmu")
    success_message = _("A jste v jiném týmu!")

    def get_initial(self):
        return {
            "team": self.new_team,
            "campaign": self.campaign,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["old_team"] = self.user_attendance.team
        context["new_team"] = self.new_team

        if self.new_team.is_full():
            return {
                "fullpage_error_message": _(
                    "Tým do kterého jste byli pozváni je již plný, budete si muset vybrat nebo vytvořit jiný tým."
                ),
                "title": _("Tým je plný"),
            }

        if self.user_attendance.campaign != self.new_team.campaign:
            return {
                "fullpage_error_message": _(
                    "Přihlašujete se do týmu ze špatné kampaně (pravděpodobně z minulého roku)."
                ),
                "title": _("Chyba přihlášení"),
            }
        return context

    def get_success_url(self):
        return self.success_url

    def form_valid(self, form):
        self.user_attendance.team = self.new_team
        approve_for_team(self.request, self.user_attendance, "", True, False)
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if Team.objects.filter(invitation_token=kwargs["token"]).count() != 1:
            raise exceptions.TemplatePermissionDenied(
                _("Tým nenalezen"),
                self.template_name,
            )

        initial_email = kwargs["initial_email"]
        if request.user.is_authenticated and request.user.email != initial_email:
            logout(request)
            messages.add_message(
                self.request,
                messages.WARNING,
                _(
                    "Pozvánka je určena jinému uživateli, než je aktuálně přihlášen. Přihlašte se jako uživatel %s."
                    % initial_email
                ),
            )
            return redirect(
                "%s?next=%s"
                % (
                    reverse("login", kwargs={"initial_email": initial_email}),
                    request.get_full_path(),
                )
            )
        invitation_token = self.kwargs["token"]
        self.new_team = Team.objects.get(invitation_token=invitation_token)
        return super().dispatch(request, *args, **kwargs)


@method_decorator(never_cache, name="dispatch")
class PaymentTypeView(
    UserAttendanceFormKwargsMixin,
    RegistrationViewMixin,
    MustBeInPaymentPhaseMixin,
    MustHaveTeamMixin,
    LoginRequiredMixin,
    CampaignParameterMixin,
    FormView,
):
    template_name = "dpnk/payment_type.html"
    registration_phase = "typ_platby"
    next_url = "profil"
    prev_url = "zmenit_triko"
    title = _("Děkujeme, že s námi chcete jezdit Do práce na kole!")

    def dispatch(self, request, *args, **kwargs):
        if request.user_attendance:
            if request.user_attendance.has_paid():
                if request.user_attendance.payment_status == "done":
                    message = _("Vaši platbu jsme úspěšně přijali.")
                else:
                    message = _("Startovné se neplatí.")
                raise exceptions.TemplatePermissionDenied(
                    message,
                    self.template_name,
                    title=_("Děkujeme!"),
                    error_level="success",
                )
            if (
                request.user_attendance.campaign.has_any_tshirt
                and not request.user_attendance.t_shirt_size
            ):
                raise exceptions.TemplatePermissionDenied(
                    format_html(
                        _(
                            "Zatím není co platit. Nejdříve se {join_team} a {choose_shirt}."
                        ),
                        join_team=format_html(
                            "<a href='{}'>{}</a>",
                            reverse("zmenit_tym"),
                            _("přidejte k týmu"),
                        ),
                        choose_shirt=format_html(
                            "<a href='{}'>{}</a>",
                            reverse("zmenit_triko"),
                            _("vyberte tričko"),
                        ),
                    ),
                    self.template_name,
                    title=_("Dobrá hospodyňka pro kolo i přes plot skočí"),
                    error_level="warning",
                )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.user_attendance.userprofile
        context["user_attendance"] = self.user_attendance
        context["firstname"] = profile.user.first_name  # firstname
        context["surname"] = profile.user.last_name  # surname
        context["email"] = profile.user.email  # email
        context["amount"] = self.user_attendance.admission_fee()
        context["beneficiary_amount"] = self.user_attendance.beneficiary_admission_fee()
        context["prev_url"] = self.prev_url
        context["disable_payment_btn"] = ""

        campaign_tshirts = (
            TShirtSize.objects.filter(
                campaign=self.campaign,
                available=True,
            )
            .exclude(t_shirt_preview=None)
            .values_list("name", flat=True)
        )
        package_transaction_content_type = ContentType.objects.get(
            model="packagetransaction",
            app_label="t_shirt_delivery",
        )
        payment_content_type = ContentType.objects.get(
            model="payment",
            app_label="dpnk",
        )
        transactions = self.user_attendance.transactions.all()
        if transactions:
            payment_not_done_transaction = transactions.exclude(
                polymorphic_ctype_id__in=[
                    package_transaction_content_type.id,
                ],
            ).exclude(
                polymorphic_ctype_id__in=[
                    payment_content_type.id,
                ],
                payment__status=models.Status.DONE,
            )
        else:
            payment_not_done_transaction = True
        if (
            self.user_attendance.t_shirt_size
            and self.user_attendance.t_shirt_size.name not in campaign_tshirts
            and payment_not_done_transaction
        ):
            context["disable_payment_btn"] = "disabled"
            context["payment_disabled_txt"] = _(
                "Platba není možná. Vámi vybraná velikost trika {} již"
                " není dostupná. Vyberte jinú velikost trika."
            ).format(
                "<strong>{}</strong>".format(
                    self.user_attendance.t_shirt_size.name,
                )
            )

        return context

    def get_form(self, form_class=PaymentTypeForm):
        form = super().get_form(form_class)
        form.user_attendance = self.user_attendance
        return form

    def form_valid(self, form):
        payment_type = form.cleaned_data["payment_type"]

        if payment_type == "company":
            company_admin_email_string = mark_safe(
                ", ".join(
                    [
                        format_html(
                            "<a href='mailto:{email}'>{email}</a>",
                            email=a.userprofile.user.email,
                        )
                        for a in self.user_attendance.get_asociated_company_admin()
                    ]
                ),
            )
        elif payment_type == "coupon":
            return redirect(reverse("discount_coupon"))
        else:
            company_admin_email_string = ""
        payment_choices = {
            "member_wannabe": {
                "type": "amw",
                "message": _(
                    "Vaše členství v klubu přátel ještě bude muset být schváleno."
                ),
                "amount": 0,
            },
            "company": {
                "type": "fc",
                "message": format_html(
                    _(
                        "Platbu ještě musí schválit koordinátor Vaší organizace {email}. "
                    ),
                    email=company_admin_email_string,
                ),
                "amount": self.user_attendance.company_admission_fee(),
            },
        }

        if payment_type in ("pay", "pay_beneficiary"):
            logger.error(
                "Wrong payment type",
                extra={"request": self.request, "payment_type": payment_type},
            )
            return HttpResponse(
                _(
                    "Pokud jste se dostali sem, tak to může být způsobené tím, že používáte zastaralý prohlížeč nebo máte vypnutý JavaScript."
                ),
                status=500,
            )
        else:
            payment_choice = payment_choices[payment_type]
            if payment_choice:
                Payment(
                    user_attendance=self.user_attendance,
                    amount=payment_choice["amount"],
                    pay_type=payment_choice["type"],
                    status=models.Status.NEW,
                ).save()
                messages.add_message(
                    self.request,
                    messages.WARNING,
                    payment_choice["message"],
                    fail_silently=True,
                )
                logger.info(
                    "Inserting payment",
                    extra={
                        "payment_type": payment_type,
                        "username": self.user_attendance.userprofile.user.username,
                    },
                )

        return super().form_valid(form)


class PaymentView(
    UserAttendanceViewMixin, MustHaveTeamMixin, LoginRequiredMixin, TemplateView
):
    beneficiary = False
    template_name = "dpnk/payment.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.user_attendance.payment_status == "no_admission":
            return redirect(reverse("dpnk_registration_complete"))
        uid = self.request.user.id
        order_id = "%s-1" % uid
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
            "Inserting payment with uid: %s, order_id: %s, session_id: %s, userprofile: %s (%s), status: %s"
            % (
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
        # client_ip = util.get_client_ip(self.request)
        client_ip = self.request.COOKIES.get("client_ip")
        timestamp = str(int(time.time()))
        language_code = self.user_attendance.userprofile.language

        context["firstname"] = firstname
        context["surname"] = lastname
        context["email"] = email
        context["amount"] = amount
        context["amount_hal"] = amount_hal
        context["description"] = description
        context["order_id"] = order_id
        context["client_ip"] = client_ip
        context["language_code"] = language_code
        context["session_id"] = session_id
        context["ts"] = timestamp
        context["sig"] = make_sig(
            (
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
                timestamp,
            )
        )
        return context


class BeneficiaryPaymentView(PaymentView):
    beneficiary = True


class PaymentResult(UserAttendanceViewMixin, LoginRequiredMixin, TemplateView):
    registration_phase = "typ_platby"
    template_name = "dpnk/payment_result.html"

    def dispatch(self, request, *args, **kwargs):
        payment = Payment.objects.get(session_id=kwargs["session_id"])
        if hasattr(self.request, "campaign") and payment.user_attendance:
            if payment.user_attendance.campaign != self.request.campaign:
                return redirect(
                    util.get_redirect(
                        request, slug=payment.user_attendance.campaign.slug
                    )
                )
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def get_context_data(self, success, trans_id, session_id, pay_type, error=None):
        context_data = super().get_context_data()
        logger.info(
            "Payment result: success: %s, trans_id: %s, session_id: %s, pay_type: %s, error: %s, user: %s (%s)"
            % (
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

        context_data["pay_type"] = pay_type
        context_data["success"] = success

        if success:
            context_data["title"] = _("Platba úspěšná")
            context_data["payment_message"] = _(
                "Vaše platba byla úspěšně zadána. "
                "Až platbu obdržíme, dáme Vám vědět na e-mail. "
                "Tím bude Vaše registrace úspěšně dokončena.",
            )
        else:
            context_data["title"] = _("Platba neúspěšná")
            logger.warning(
                "Payment unsuccessful",
                extra={
                    "success": success,
                    "pay_type": pay_type,
                    "trans_id": trans_id,
                    "session_id": session_id,
                    "user": self.user_attendance.userprofile.user,
                    "request": self.request,
                },
            )
            context_data["payment_message"] = _(
                "Vaše platba se nezdařila. Po přihlášení do svého profilu můžete zadat novou platbu."
            )
        context_data["registration_phase"] = self.registration_phase
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
    pos_id = request.POST["pos_id"]
    session_id = request.POST["session_id"]
    ts = request.POST["ts"]
    sig = request.POST["sig"]
    logger.info(
        "Payment status - pos_id: %s, session_id: %s, ts: %s, sig: %s"
        % (pos_id, session_id, ts, sig)
    )
    check_sig(sig, (pos_id, session_id, ts))
    # Determine the status of transaction based on the notification
    c = HTTPSConnection("secure.payu.com")
    timestamp = str(int(time.time()))
    c.request(
        "POST",
        "/paygw/UTF/Payment/get/txt/",
        urlencode(
            (
                ("pos_id", pos_id),
                ("session_id", session_id),
                ("ts", timestamp),
                ("sig", make_sig((pos_id, session_id, timestamp))),
            )
        ),
        {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": "text/plain",
        },
    )
    raw_response = codecs.decode(c.getresponse().read(), "utf-8")
    r = {}
    for i in [i.split(":", 1) for i in raw_response.split("\n") if i.strip() != ""]:
        r[i[0]] = i[1].strip()
    check_sig(
        r["trans_sig"],
        (
            r["trans_pos_id"],
            r["trans_session_id"],
            r["trans_order_id"],
            r["trans_status"],
            r["trans_amount"],
            r["trans_desc"],
            r["trans_ts"],
        ),
    )
    amount = math.floor(int(r["trans_amount"]) / 100)
    # Update the corresponding payment
    # TODO: use update_or_create in Django 1.7
    p, created = Payment.objects.select_for_update().get_or_create(
        session_id=r["trans_session_id"],
        defaults={
            "order_id": r["trans_order_id"],
            "amount": amount,
            "description": r["trans_desc"],
        },
    )

    if p.amount != amount:
        logger.error(
            "Payment amount doesn't match",
            extra={
                "pay_type": p.pay_type,
                "status": p.status,
                "payment_response": r,
                "expected_amount": p.amount,
                "request": request,
            },
        )
        return HttpResponse("Bad amount", status=400)
    p.pay_type = r["trans_pay_type"]
    p.status = r["trans_status"]
    if r["trans_recv"] != "":
        p.realized = r["trans_recv"]
    p.save()

    logger.info(
        "Payment status: pay_type: %s, status: %s, payment response: %s"
        % (p.pay_type, p.status, r)
    )

    # Return positive error code as per PayU protocol
    return HttpResponse("OK")


class RegistrationCompleteView(TitleViewMixin, TemplateView):
    title = _("Registrace dokončena!")
    template_name = "dpnk/dpnk_registration_complete.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["app_redirect"] = reverse(
            "open-application-with-rest-token", args=("2")
        )
        return context


class RegistrationUncompleteForm(
    TitleViewMixin, RegistrationMessagesMixin, LoginRequiredMixin, TemplateView
):
    template_name = "dpnk/base_generic_form.html"
    title = _("Nastal čas seřídit kolo a vyřešit drobné papírování…")
    opening_message = util.mark_safe_lazy(
        _(
            "<p>"
            "Nemůžeme Vás pustit dál, protože Vaše registrace není kompletní. "
            "Stačí si ještě poradit s pár maličkostmi a dostanete se na startovací čáru."
            "</p>"
            "<img src='https://www.dopracenakole.cz/wp-content/uploads/bajk-servis.jpg'/>",
        ),
    )
    registration_phase = "registration_uncomplete"

    def get(self, request, *args, **kwargs):
        reason = self.user_attendance.entered_competition_reason()
        if reason is True:
            return redirect(reverse("dpnk_registration_complete"))
        else:
            return super().get(request, *args, **kwargs)


class PackageView(RegistrationViewMixin, LoginRequiredMixin, TemplateView):
    template_name = "dpnk/package.html"
    title = _("Sledování balíčku")
    registration_phase = "zmenit_tym"


class DataReportView(LoginRequiredMixin, TemplateView):
    """Incorporate Metabase app may, september/january competition data
    report dashboard
    """

    template_name = "dpnk/datareport.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "may" == kwargs["challenge"]:
            base_url = settings.METABASE_DPNK_MAY_CHALLENGE_DATA_REPORT_URL
        elif "september-january" == kwargs["challenge"]:
            base_url = (
                settings.METABASE_DPNK_SEPTEMBER_JANUARY_CHALLENGE_DATA_REPORT_URL
            )
        context["base_url"] = base_url
        return context


class DataReportResultsView(LoginRequiredMixin, TemplateView):
    """Incorporate Metabase app

    1. organization regulariry (Company/City organizator),
    2. organization/city performance (Company/City organizator),
    3. orgaznization review

    results data report dashboard.
    """

    template_name = "dpnk/datareport_results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "regularity" == kwargs["type"]:
            base_url = settings.METABASE_DPNK_REGULARITY_RESULTS_DATA_REPORT_URL
        elif "performance-organization" == kwargs["type"]:
            base_url = (
                settings.METABASE_DPNK_PERFORMANCE_ORGANIZATION_RESULTS_DATA_REPORT_URL
            )
        elif "performance-city" == kwargs["type"]:
            base_url = settings.METABASE_DPNK_PERFORMANCE_CITY_RESULTS_DATA_REPORT_URL
        elif "organizations-review" == kwargs["type"]:
            base_url = (
                settings.METABASE_DPNK_ORGANIZATION_REVIEW_RESULTS_DATA_REPORT_URL
            )
        context["base_url"] = base_url
        return context


class RegistrationProfileView(
    CampaignFormKwargsMixin,
    RegistrationPersonalViewMixin,
    LoginRequiredMixin,
    UpdateView,
):
    template_name = "dpnk/profile_update.html"
    form_class = RegistrationProfileUpdateForm
    model = UserProfile
    success_message = _("Vaše osobní údaje jsme pečlivě uložili.")
    next_url = "zmenit_tym"
    registration_phase = "upravit_profil"
    title = _("Vyplňte soutěžní údaje")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            instance={
                "user": self.user_attendance.userprofile.user,
                "usermail": self.user_attendance.userprofile.user,
                "userprofiledontshowname": self.user_attendance.userprofile,
                "userprofile": self.user_attendance.userprofile,
                "userattendance": self.user_attendance,
            },
        )
        return kwargs


class UpdateProfileView(RegistrationProfileView):
    form_class = ProfileUpdateForm
    success_url = "edit_profile_detailed"
    title = _("Můj profil")
    template_name = "dpnk/profile_update_detailed.html"


class TeamApprovalRequest(
    TitleViewMixin, UserAttendanceViewMixin, LoginRequiredMixin, TemplateView
):
    template_name = "dpnk/request_team_approval.html"
    title = _("Žádost o ověření členství byla odeslána")
    registration_phase = "zmenit_tym"

    def dispatch(self, request, *args, **kwargs):
        if request.user_attendance:
            approval_request_mail(request.user_attendance)
        return super().dispatch(request, *args, **kwargs)


class InviteView(
    UserAttendanceViewMixin,
    MustBeInRegistrationPhaseMixin,
    TitleViewMixin,
    MustBeApprovedForTeamMixin,
    LoginRequiredMixin,
    FormView,
):
    template_name = "dpnk/base_generic_form.html"
    form_class = InviteForm
    title = _("Pozvěte další kolegy do svého týmu")
    registration_phase = "zmenit_tym"
    next_url = reverse_lazy("zmenit_triko")

    def get_success_url(self):
        if self.user_attendance.entered_competition():
            return reverse_lazy("team_members")
        else:
            return reverse_lazy("zmenit_triko")

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data["registration_phase"] = self.registration_phase
        context_data["introduction_message"] = (
            _(
                "Pozvěte přátele z práce, aby podpořili Váš tým, který může mít až %s členů."
            )
            % self.user_attendance.campaign.max_team_members
        )
        return context_data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user_attendance"] = self.user_attendance
        kwargs["success_url"] = self.get_success_url()
        return kwargs

    def form_valid(self, form):
        for email in form.cleaned_data.values():
            if email:
                try:
                    invited_user = models.User.objects.get(is_active=True, email=email)

                    (
                        invited_user_attendance,
                        created,
                    ) = UserAttendance.objects.get_or_create(
                        userprofile=invited_user.userprofile,
                        campaign=self.user_attendance.campaign,
                    )

                    if invited_user_attendance.team == self.user_attendance.team:
                        approve_for_team(
                            self.request, invited_user_attendance, "", True, False
                        )
                        messages.add_message(
                            self.request,
                            messages.SUCCESS,
                            _("Uživatel %(user)s byl přijat do Vašeho týmu.")
                            % {"user": invited_user_attendance, "email": email},
                            fail_silently=True,
                        )
                    else:
                        invitation_mail(
                            self.user_attendance,
                            invited_user_attendance.userprofile.user.email,
                            invited_user_attendance,
                        )
                        messages.add_message(
                            self.request,
                            messages.SUCCESS,
                            _(
                                "Odeslána pozvánka uživateli %(user)s na e-mail %(email)s"
                            )
                            % {"user": invited_user_attendance, "email": email},
                            fail_silently=True,
                        )
                except models.User.DoesNotExist:
                    invitation_mail(self.user_attendance, email)
                    messages.add_message(
                        self.request,
                        messages.SUCCESS,
                        _("Odeslána pozvánka na e-mail %s") % email,
                        fail_silently=True,
                    )

        return super().form_valid(form)


class ApplicationView(RegistrationViewMixin, LoginRequiredMixin, TemplateView):
    template_name = "dpnk/applications.html"
    title = _("Aplikace")
    registration_phase = "application"


class OpenApplicationWithRestTokenView(View):
    def get(self, request, *args, **kwargs):
        try:
            app_id = int(kwargs["app_id"])
        except ValueError:
            return "./"
        rough_url = settings.DPNK_MOBILE_APP_URLS[app_id]
        campaign_slug_identifier = self.request.campaign.slug_identifier
        HttpResponseRedirect.allowed_schemes.append("dpnk")
        if not request.user.is_authenticated:
            return HttpResponseRedirect(
                rough_url.format(
                    auth_token="null",
                    campaign_slug_identifier=campaign_slug_identifier,
                )
            )

        from rest_framework.authtoken.models import Token

        token, _ = Token.objects.get_or_create(user=self.request.user)
        return HttpResponseRedirect(
            rough_url.format(
                auth_token=token.key,
                campaign_slug_identifier=campaign_slug_identifier,
            )
        )


class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.GOOGLE_SOCIAL_MEDIA_LOGIN_CALLBACK_URL
    client_class = OAuth2Client
