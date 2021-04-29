# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2015 o.s. Auto*Mat
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
import datetime
import gzip
import logging
from collections import OrderedDict

from betterforms.multiform import MultiModelForm

from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Div, Field, Fieldset, HTML, Layout, Submit

from dal import autocomplete

from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms.widgets import HiddenInput
from django.urls import reverse
from django.utils import formats
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ngettext
from django.utils.translation import ugettext_lazy as _

from django_gpxpy import gpx_parse

from initial_field import InitialFieldsMixin

from leaflet.forms.widgets import LeafletWidget

from notifications.signals import notify

import photologue

import registration.forms

from . import email, models, util, views
from .fields import CommaFloatField, ShowPointsMultipleModelChoiceField
from .string_lazy import format_html_lazy
from .widgets import CommuteModeSelect

logger = logging.getLogger(__name__)


class RequiredFieldsMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        fields_required = getattr(self.Meta, "fields_required", None)
        if fields_required:
            for key in self.fields:
                if key in fields_required:
                    self.fields[key].required = True


class UserLeafletWidget(LeafletWidget):
    geometry_field_class = "ClearableGeometryField"
    template_name = "widgets/leaflet.html"

    def __init__(self, *args, **kwargs):
        user_attendance = kwargs["user_attendance"]
        settings_overrides = {}
        if user_attendance.team and user_attendance.team.subsidiary.city.location:
            settings_overrides["DEFAULT_CENTER"] = (
                user_attendance.team.subsidiary.city.location.y,
                user_attendance.team.subsidiary.city.location.x,
            )
            settings_overrides["DEFAULT_ZOOM"] = 13

        super().__init__(
            attrs={
                "geom_type": "MULTILINESTRING",
                "map_height": "500px",
                "map_width": "100%",
                "settings_overrides": settings_overrides,
                "prev_tracks": models.Trip.objects.filter(
                    user_attendance=user_attendance, track__isnull=False
                ).order_by("-date", "direction"),
            },
        )


class SubmitMixin(object):
    submit_text = _("Odeslat")

    def __init__(self, *args, **kwargs):
        if not hasattr(self, "helper"):
            self.helper = FormHelper()
        super().__init__(*args, **kwargs)
        self.helper.add_input(Submit("submit", self.submit_text))


class PrevNextMixin(object):
    next_text = _("Pokračovat")
    submit_text = _("Hotovo")

    def show_edit_form(self):
        if getattr(self, "instance", False):
            return self.instance.entered_competition()

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        prev_url = kwargs.pop("prev_url", None)
        ret_val = super().__init__(*args, **kwargs)
        if self.show_edit_form():
            self.helper.add_input(
                Submit("submit", self.submit_text, css_class="form-actions")
            )
            return super().__init__(*args, **kwargs)
        if not hasattr(self, "no_dirty"):
            self.helper.form_class = "dirty-check"
        if not hasattr(self, "no_prev"):
            self.helper.add_input(
                Button(
                    "prev",
                    _("Zpět"),
                    css_class="btn-default form-actions",
                    onclick='window.location.href="{}"'.format(reverse(prev_url)),
                ),
            )
        if not hasattr(self, "no_next"):
            self.helper.add_input(
                Submit("next", self.next_text, css_class="form-actions")
            )
        return ret_val


class CampaignMixin(object):
    """ set self.campaign parameter from kwargs """

    def __init__(self, *args, **kwargs):
        self.campaign = kwargs.pop("campaign", None)
        return super().__init__(*args, **kwargs)


def social_html(login=True):
    action_word = _("Přihlásit přes") if login else _("Registrovat přes")
    apple_action_word = _("Pokračovat přes") if login else _("Zaregistrovat se přes")
    return HTML(
        format_html_lazy(
            "<div class=\"social-login-buttons\">"
            "<p>"
            '<a class="btn facebook" href="{{% url "social:begin" "facebook" %}}">'
            '<i class="fab fa-facebook"></i>&nbsp;'
            "{} Facebook"
            "</a>"
            "</p>"
            "<p>"
            '<a class="btn google" href="{{% url "social:begin" "google-oauth2" %}}">'
            '<i class="fab fa-google"></i>&nbsp;'
            "{} Google"
            "</a>"
            "</p>"
            "<p>"
            '<a class="btn apple" href="{{% url "social:begin" "apple-id" %}}">'
            '<i class="fab fa-apple"></i>&nbsp;'
            "{} Apple"
            "</a>"
            "</p>"
            "</div>",
            action_word,
            action_word,
            apple_action_word,
        ),
    )


class RegisterCompanyForm(forms.ModelForm):
    required_css_class = "required"
    error_css_class = "error"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs["autocomplete"] = "organization"

    class Meta:
        model = models.Company
        fields = ("name", "ico")
        error_messages = {"ico": {"stdnum_format": models.company.ICO_ERROR_MESSAGE}}


class AddressForm(CampaignMixin, forms.ModelForm):
    required_css_class = "required"
    error_css_class = "error"

    address_psc = forms.CharField(
        label=_("PSČ"),
    )

    def clean_address_psc(self):
        address_psc = self.cleaned_data["address_psc"]
        try:
            address_psc = int(address_psc.replace(" ", ""))
        except (TypeError, ValueError):
            raise ValidationError("PSČ musí být pěticiferné číslo")
        if address_psc > 99999 or address_psc < 10000:
            raise ValidationError("PSČ musí být pěticiferné číslo")
        return address_psc

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        super().__init__(*args, **kwargs)
        if "city" in self.fields:
            self.fields["city"].queryset = models.City.objects.filter(
                cityincampaign__campaign=self.campaign
            )
        self.helper.layout = Layout(
            "city" if "city" in self.fields else None,
            "address_recipient",
            Fieldset(
                "", "address_street", "address_street_number", css_class="field-row"
            ),
            Fieldset("", "address_city", "address_psc", css_class="field-row"),
        )

    class Meta:
        model = models.Subsidiary
        fields = (
            "city",
            "address_recipient",
            "address_street",
            "address_street_number",
            "address_psc",
            "address_city",
        )


class RegisterSubsidiaryForm(AddressForm):
    def clean_company(self):
        return self.company

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = kwargs["initial"]["company"]
        self.fields["address_recipient"].widget.attrs["autocomplete"] = "subsidiary"
        self.helper = FormHelper()
        self.helper.form_id = "register-subsidiary-form"
        self.helper.layout = Layout(
            HTML('<div class="form-group"> <label class="control-label">'),
            HTML(_("Společnost")),
            HTML("</label>"),
            HTML(self.company),
            HTML("</div>"),
            "company",
            "city",
            "address_recipient",
            Fieldset(
                "", "address_street", "address_street_number", css_class="field-row"
            ),
            Fieldset("", "address_city", "address_psc", css_class="field-row"),
        )

    class Meta:
        model = models.Subsidiary
        fields = (
            "company",
            "city",
            "address_recipient",
            "address_street",
            "address_street_number",
            "address_psc",
            "address_city",
        )
        widgets = {"company": forms.HiddenInput()}


class RegisterTeamForm(InitialFieldsMixin, forms.ModelForm):
    initial_fields = ("campaign",)
    required_css_class = "required"
    error_css_class = "error"

    def clean_subsidiary(self):
        return self.subsidiary

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subsidiary = kwargs["initial"]["subsidiary"]
        self.fields["name"].label = _("Jméno")
        self.fields["name"].help_text = _(
            "Zvolte jméno, pod kterým bude Váš tým bojovat."
        )

        self.helper = FormHelper()
        self.helper.form_id = "register-team-form"
        self.helper.layout = Layout(
            HTML(
                '<div class="form-group"> <label class="control-label">Adresa</label>'
            ),
            HTML(self.subsidiary),
            HTML("</div>"),
            *self._meta.fields,
        )

    class Meta:
        model = models.Team
        fields = ("subsidiary", "name", "campaign")
        widgets = {"subsidiary": forms.HiddenInput()}


class ChangeTeamForm(PrevNextMixin, forms.ModelForm):
    company = forms.ModelChoiceField(
        queryset=models.Company.objects.all(),
        widget=autocomplete.ModelSelect2(url="company_autocomplete"),
        label=_("Společnost"),
    )

    subsidiary = forms.ModelChoiceField(
        queryset=models.Subsidiary.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="subsidiary_autocomplete",
            forward=["company"],
        ),
        label=_("Adresa společnosti nebo pobočky"),
    )

    team = forms.ModelChoiceField(
        queryset=models.Team.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="team_autocomplete",
            forward=["subsidiary"],
        ),
        label=_("Tým"),
    )

    def clean(self):
        cleaned_data = super().clean()

        if "subsidiary" in cleaned_data:
            subsidiary = cleaned_data["subsidiary"]
            if (
                subsidiary
                and not models.CityInCampaign.objects.filter(
                    city=subsidiary.city, campaign__slug=self.instance.campaign.slug
                ).exists()
            ):
                logger.error(
                    "Subsidiary in city that doesn't belong to this campaign",
                    extra={"subsidiary": subsidiary},
                )
                raise forms.ValidationError(
                    _(
                        "Zvolená pobočka je registrována ve městě, které v aktuální kampani nesoutěží. "
                        "Prosím žádejte změnu po Vašem vnitrofiremním koordinátorovi."
                    ),
                )

            if (
                not self.instance.campaign.competitors_choose_team()
            ):  # We ask only for company and subsidiary
                team = cleaned_data["team"]
                team.subsidiary = subsidiary
                team.save()
                self.instance.team = team
                self.instance.approved_for_team = "approved"
                self.instance.save()

        return cleaned_data

    def clean_team(self):
        if self.instance.campaign.competitors_choose_team():  # We ask only for team
            team = self.cleaned_data["team"]
            if team.campaign.slug != self.instance.campaign.slug:
                logger.error(
                    "Team not in campaign",
                    extra={"team": team.pk, "subdomain": self.instance.campaign.slug},
                )
                raise forms.ValidationError(
                    _("Zvolený tým není dostupný v aktuální kampani")
                )
        elif not self.instance.team:
            team = models.Team(campaign=self.instance.campaign)
        else:
            team = self.instance.team
        return team

    def save(self, *args, **kwargs):
        user_attendance = super().save(*args, **kwargs)
        if user_attendance.approved_for_team != "approved":
            email.approval_request_mail(user_attendance)
        elif (
            user_attendance.campaign.competitors_choose_team()
            and not user_attendance.team.is_full()
        ):
            notify.send(
                user_attendance,
                recipient=user_attendance.userprofile.user,
                verb=_("Pozvěte další členy do Vášeho týmu"),
                url=reverse("pozvanky"),
                icon=static("/img/dpnk_logo.svg"),
            )
        return user_attendance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.form_class = "noAsterisks"

        self.fields["team"].widget.manager = (
            "team_in_campaign_%s" % self.instance.campaign.slug
        )
        self.fields["subsidiary"].help_text += format_html(
            "{}<br/><br/>{}<br/>{}",
            _("Zadejte adresu, kam jezdíte každý den do práce."),
            _("Je název nebo adresa společnosti napsaná chybně?"),
            self.instance.company_coordinator_mail_text(),
        )

        company = self.initial.get("company")
        subsidiary = self.initial.get("subsidiary")
        self.helper.form_id = "change-team-form"
        self.helper.layout = Layout(
            FieldWithButtons(
                "company",
                StrictButton(
                    format_html(
                        '<span class="glyphicon glyphicon-plus"></span> {}',
                        _("Nová společnost"),
                    ),
                    href=reverse("register_company"),
                    data_fm_head=_("Přidejte novou společnost"),
                    data_fm_ok=_("Přidat"),
                    data_fm_cancel=_("Zpět"),
                    data_fm_callback="createCompanyCallback",
                    css_class="btn fm-create",
                    id="fm-create-company",
                ),
            ),
            FieldWithButtons(
                "subsidiary",
                StrictButton(
                    format_html(
                        '<span class="glyphicon glyphicon-plus"></span> {}',
                        _("Přidat adresu"),
                    ),
                    href=reverse("register_subsidiary", args=(company.id,))
                    if company
                    else "",
                    data_fm_head=_("Přidejte novou adresu"),
                    data_fm_ok=_("Přidat"),
                    data_fm_cancel=_("Zpět"),
                    data_fm_callback="createSubsidiaryCallback",
                    css_class="btn fm-create",
                    id="fm-create-subsidiary",
                    **(
                        {"disabled": True} if company is None else {}
                    ),  # Disable button if no company is selected
                ),
            ),
            FieldWithButtons(
                "team",
                StrictButton(
                    format_html(
                        '<span class="glyphicon glyphicon-plus"></span> {}',
                        _("Založit tým"),
                    ),
                    href=reverse("register_team", args=(subsidiary.id,))
                    if subsidiary
                    else "",
                    data_fm_head=_("Založte nový tým"),
                    data_fm_ok=_("Založit"),
                    data_fm_cancel=_("Zpět"),
                    data_fm_callback="createTeamCallback",
                    css_class="btn fm-create",
                    id="fm-create-team",
                    **(
                        {"disabled": True} if subsidiary is None else {}
                    ),  # Disable button if no subsidiary is selected
                ),
            ),
        )

        if (
            not self.instance.campaign.competitors_choose_team()
        ):  # We ask only for comapny and subsidiary
            self.fields["team"].widget = HiddenInput()
            self.fields["team"].required = False
            del self.helper.layout.fields[2]

    class Meta:
        model = models.UserAttendance
        fields = ("company", "subsidiary", "team")


class RegistrationAccessFormDPNK(SubmitMixin, forms.Form):
    email = forms.CharField(
        required=True,
        label=_("Zadejte svůj e-mail"),
        help_text=_(
            "Na tento e-mail budete dostávat všechny důležité informace v průběhu kampaně."
        ),
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "noAsterisks"
        self.helper.form_id = "registration-access-form"
        self.helper.layout = Layout(
            "email",
            Submit("submit", _("Pokračovat")),
            social_html(False),
        )


class EmailUsernameMixin(object):
    def clean_username(self):
        "This function is required to overwrite an inherited username clean"
        return self.cleaned_data["username"]

    def clean(self):
        cleaned_data = super().clean()
        if not self.errors:
            cleaned_data["username"] = "%s%s" % (
                cleaned_data["email"].split("@", 1)[0],
                User.objects.count(),
            )
        return cleaned_data


class RegistrationBaseForm(
    EmailUsernameMixin, registration.forms.RegistrationFormUniqueEmail
):
    submit_text = _("Registrovat")
    required_css_class = "required"

    username = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(
        self, request=None, invitation_token=None, campaign=None, *args, **kwargs
    ):
        if not hasattr(self, "campaign"):
            self.campaign = campaign
        self.invitation_token = invitation_token
        self.request = request
        self.helper = FormHelper()
        self.helper.form_class = "noAsterisks"
        self.helper.form_id = "registration-form"

        super().__init__(*args, **kwargs)

        self.fields["email"].help_text = _(
            "Na tento e-mail budete dostávat všechny důležité informace v průběhu kampaně."
        )
        self.fields["password1"].label = _("Vyberte heslo")
        self.fields["password1"].help_text = _(
            "Heslo musí mít minimálně 6 znaků a obsahovat alespoň jedno písmeno."
        )
        self.fields["password2"].help_text = _(
            "Zadejte vybrané heslo ještě jednou. Teď máte jistotu, že je napsané správně."
        )

    def clean_email(self):
        if User.objects.filter(email__iexact=self.cleaned_data["email"]):
            raise forms.ValidationError(
                mark_safe(
                    _(
                        "Tato e-mailová adresa je již registrovaná. "
                        "<a href='%(login)s' class='btn login_redirection_button'>Přihlasit se</a>"
                        "<a href='%(password)s' class='btn login_redirection_button'>Obnovit heslo</a>"
                    )
                    % {
                        "password": reverse("password_reset"),
                        "login": reverse("login"),
                    },
                ),
            )
        return self.cleaned_data["email"]

    class Meta:
        model = User
        fields = ("email", "password1", "password2", "username")


class RegistrationFormDPNK(RegistrationBaseForm):
    def __init__(self, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            *self._meta.fields,
            Submit("submit", _("Registrovat")),
            social_html(False),
        )
        return ret_val

    def save(self, *args, **kwargs):
        new_user = super().save(*args, **kwargs)
        new_user.save()
        userprofile = models.UserProfile.objects.create(user=new_user)
        try:
            team = models.Team.objects.get(invitation_token=self.invitation_token)
            if team.is_full():
                messages.error(
                    self.request,
                    _(
                        "Tým do kterého jste byli pozváni je již plný, budete si muset vybrat nebo vytvořit jiný tým."
                    ),
                )
                team = None
        except models.Team.DoesNotExist:
            team = None
        user_attendance = models.UserAttendance.objects.create(
            userprofile=userprofile,
            campaign=self.campaign,
            team=team,
        )
        if team:
            views.approve_for_team(self.request, user_attendance, "", True, False)
        return new_user


class InviteForm(SubmitMixin, forms.Form):
    required_css_class = "required"
    error_css_class = "error"

    def __init__(self, user_attendance, success_url, *args, **kwargs):
        self.user_attendance = user_attendance
        if self.user_attendance.campaign.max_team_members and self.user_attendance.team:
            self.free_capacity = (
                self.user_attendance.campaign.max_team_members
                - self.user_attendance.team.member_count
            )
        else:
            self.free_capacity = 0
        ret_val = super().__init__(*args, **kwargs)
        fields = []
        for i in range(1, min(self.free_capacity + 1, 11)):
            field_name = "email%s" % i
            self.fields[field_name] = forms.EmailField(
                label=_("E-mail kolegy"),
                required=False,
            )
            fields.append(field_name)
        self.helper = FormHelper()
        self.helper.form_class = "dirty-check"
        self.helper.form_id = "invite-form"
        self.helper.add_input(
            Button(
                "submit",
                _("Přeskočit"),
                css_class="btn-default",
                onclick='window.location.href="{}"'.format(success_url),
            ),
        )
        self.helper.add_input(Submit("submit", _("Odeslat pozvánku")))
        for field in self.fields.values():
            field.widget.attrs["autocomplete"] = "new-password"
        return ret_val


class TeamSettingsForm(InitialFieldsMixin, SubmitMixin, forms.ModelForm):
    initial_fields = ("campaign",)
    required_css_class = "required"
    error_css_class = "error"

    class Meta:
        model = models.Team
        fields = ("name", "campaign")


class PhotoForm(forms.ModelForm):
    required_css_class = "required"
    error_css_class = "error"
    galleries = forms.ModelMultipleChoiceField(
        queryset=photologue.models.Gallery.objects.all()
    )

    def save(self, *args, **kwargs):
        returnv = super().save(*args, **kwargs)
        for gallery in self.data["galleries"]:
            self.instance.galleries.add(gallery)
        return returnv

    class Meta:
        model = photologue.models.Photo
        fields = ("image", "title", "slug", "is_public")


class PaymentTypeForm(PrevNextMixin, forms.Form):
    no_dirty = True
    next_text = _("Zaplatit")
    payment_type = forms.ChoiceField(
        label="",
        widget=forms.RadioSelect(),
    )

    def clean_payment_type(self):
        payment_type = self.cleaned_data["payment_type"]
        if (
            payment_type == "company"
            and not self.user_attendance.get_asociated_company_admin_with_payments().exists()
        ):
            raise forms.ValidationError(
                format_html(
                    _(
                        "Váš zaměstnavatel {employer} nemá zvoleného firemního koordinátora nebo neumožňuje platbu za zaměstnance. "
                        "Vaše organizace bude muset nejprve ustanovit zástupce, který za ní bude schvalovat platby ve Vaší organizaci."
                        "<ul><li><a href='{url}'>Chci se stát firemním koordinátorem</a></li></ul>"
                    ),
                    employer=self.user_attendance.team.subsidiary.company,
                    url=reverse("company_admin_application"),
                ),
            )
        return payment_type

    def __init__(self, *args, **kwargs):
        self.user_attendance = kwargs.pop("user_attendance")
        ret_val = super().__init__(*args, **kwargs)
        self.helper.form_class = "noAsterisks"
        self.helper.form_id = "payment-type-form"
        self.fields["payment_type"].choices = [
            (
                "pay",
                format_html(
                    '<span id="payment_amount">{} Kč</span><p class="price-descriptor">{}</p>',
                    round(self.user_attendance.admission_fee()),
                    _("Zaplatím běžné startovné."),
                ),
            ),
            (
                "pay_beneficiary",
                format_html(
                    '{} Kč<p class="price-descriptor">{}</p>',
                    round(self.user_attendance.beneficiary_admission_fee()),
                    _("Podpořím soutěž benefičním startovným %s Kč.")
                    % (
                        round(
                            self.user_attendance.beneficiary_admission_fee()
                            - self.user_attendance.admission_fee()
                        )
                    ),
                ),
            ),
            (
                "company",
                format_html(
                    '0 Kč<p class="price-descriptor">{}</p>',
                    _("Startovné mi platí zaměstnavatel."),
                ),
            ),
        ]
        if self.user_attendance.campaign.club_membership_integration:
            self.fields["payment_type"].choices.append(
                (
                    "member_wannabe",
                    format_html(
                        '0 Kč<p class="price-descriptor">{}</p>',
                        _(
                            "Chci se stát členem Klubu přátel organizace AutoMat a podpořit rozvoj udržitelné mobility. "
                        ),
                    ),
                ),
            )

        self.fields["payment_type"].choices.append(
            (
                "coupon",
                format_html(
                    '? Kč<p class="price-descriptor">{}</p>',
                    _("Chci uplatnit voucher."),
                ),
            ),
        )
        return ret_val


class AnswerForm(forms.ModelForm):
    choices = ShowPointsMultipleModelChoiceField(
        queryset=models.Choice.objects.none(), label="", help_text=""
    )

    def __init__(self, *args, **kwargs):
        question = kwargs.pop("question")
        show_points = kwargs.pop("show_points")
        is_actual = kwargs.pop("is_actual")
        ret_val = super().__init__(*args, **kwargs)
        if question.comment_type:
            if question.comment_type == "link":
                self.fields["comment"] = forms.URLField(
                    help_text=_("Adresa URL včetně úvodního http:// nebo https://"),
                )
            if question.comment_type == "one-liner":
                self.fields["comment"] = forms.CharField()
            self.fields["comment"].label = ""
            if question.question_type == "text":
                self.fields["comment"].required = question.required
        else:
            del self.fields["comment"]

        choices_layout = Field("choices")
        if question.question_type != "text":
            if question.question_type == "choice":
                choices_layout = Field(
                    "choices", template="widgets/radioselectmultiple.html"
                )
            self.fields["choices"].widget = forms.CheckboxSelectMultiple()
            if question.choice_type:
                self.fields["choices"].queryset = question.choice_type.choice_set.all()
            else:
                self.fields["choices"].queryset = models.Choice.objects.none()
            self.fields["choices"].show_points = show_points
            self.fields["choices"].required = question.required
            self.fields["choices"].help_text = ""
        else:
            del self.fields["choices"]

        if not question.with_attachment:
            del self.fields["attachment"]

        self.helper = FormHelper()
        self.helper.form_id = "answers-form"
        self.helper.layout = Layout(
            Div(
                choices_layout if question.question_type != "text" else None,
                "comment" if question.comment_type else None,
                "attachment" if question.with_attachment else None,
                css_class=None if is_actual else "readonly",
            ),
        )
        self.helper.form_tag = False
        return ret_val

    class Meta:
        model = models.Answer
        fields = ("choices", "comment", "attachment")


class ConfirmTeamInvitationForm(InitialFieldsMixin, SubmitMixin, forms.ModelForm):
    initial_fields = ("team", "campaign")
    question = forms.BooleanField(
        label=_("Chci být zařazen do nového týmu"),
    )

    class Meta:
        model = models.UserAttendance
        fields = ("team", "question", "campaign")


class BikeRepairForm(SubmitMixin, forms.ModelForm):
    user_attendance = forms.CharField(
        label=_("Uživatelské jméno zákazníka"),
        help_text=_("Uživatelské jméno, které Vám sdělí zákazník"),
        max_length=100,
    )
    description = forms.CharField(
        label=_("Poznámka"),
        max_length=500,
        required=False,
    )

    def clean_user_attendance(self):
        campaign = self.initial["campaign"]
        user_attendance = self.cleaned_data.get("user_attendance")
        try:
            user_attendance = models.UserAttendance.objects.get(
                Q(userprofile__user__username=user_attendance)
                | Q(userprofile__user__email=user_attendance),
                campaign=campaign,
            )
        except models.UserAttendance.DoesNotExist:
            raise forms.ValidationError(_("Takový uživatel neexistuje"))

        other_user_attendances = user_attendance.other_user_attendances(campaign)
        if other_user_attendances.count() > 0:
            raise forms.ValidationError(
                _(
                    "Tento uživatel není nováček, soutěžil již v předcházejících kampaních: %s"
                )
                % ", ".join(
                    [u.campaign.display_name() for u in other_user_attendances]
                ),
            )

        return user_attendance

    def clean(self):
        try:
            transaction = models.CommonTransaction.objects.get(
                user_attendance=self.cleaned_data.get("user_attendance"),
                status=models.Status.BIKE_REPAIR,
            )
        except models.CommonTransaction.DoesNotExist:
            transaction = None
        if transaction:
            created_formated_date = formats.date_format(
                transaction.created, "SHORT_DATETIME_FORMAT"
            )
            raise forms.ValidationError(
                _(
                    "Tento uživatel byl již %(time)s v cykloservisu %(bike_shop)s (poznámka: %(note)s)."
                )
                % {
                    "time": created_formated_date,
                    "bike_shop": transaction.author.get_full_name(),
                    "note": transaction.description,
                },
            )
        return super().clean()

    def save(self, *args, **kwargs):
        self.instance.status = models.Status.BIKE_REPAIR
        return super().save(*args, **kwargs)

    class Meta:
        model = models.CommonTransaction
        fields = ("user_attendance", "description")


class FormWithTrackMixin:
    def clean_parse_and_calculate_track(self):
        if "gpx_file" in self.changed_data and self.cleaned_data["gpx_file"]:
            if self.cleaned_data["gpx_file"].name.endswith(".gz"):
                track_file = gzip.open(self.cleaned_data["gpx_file"])
            else:
                track_file = self.cleaned_data["gpx_file"]
            try:
                track_file = track_file.read().decode("utf-8")
            except UnicodeDecodeError:
                raise ValidationError(
                    {
                        "gpx_file": _(
                            "Chyba při načítání GPX souboru. Jste si jistí, že jde o GPX soubor?"
                        )
                    }
                )
            self.cleaned_data["track"] = gpx_parse.parse_gpx(track_file)
            self.changed_data.append("track")
        if self.cleaned_data.get("track", None) and (
            "track" in self.changed_data or not self.cleaned_data["distance"]
        ):
            self.cleaned_data["distance"] = round(
                util.get_multilinestring_length(self.cleaned_data["track"]), 2
            )
        return self.cleaned_data


class UserUpdateForm(CampaignMixin, RequiredFieldsMixin, forms.ModelForm):
    def clean_email(self):
        """
        Validate that the email is not already in use.
        """
        if (
            User.objects.filter(email__iexact=self.cleaned_data["email"])
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError(
                _("Tento e-mail již je v našem systému zanesen.")
            )
        else:
            return self.cleaned_data["email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "first_name" in self.fields:
            self.fields["first_name"].label = _("Jméno")
        if "email" in self.fields:
            self.fields["email"].label = _("E-mail")

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
        )
        fields_required = (
            "email",
            "first_name",
            "last_name",
        )
        help_texts = {
            "email": _("E-mail slouží jako přihlašovací jméno."),
        }


class UserEmailUpdateForm(UserUpdateForm):
    class Meta(UserUpdateForm.Meta):
        fields = ("email",)
        help_texts = {
            "email": None,
        }


class UserNameUpdateForm(UserUpdateForm):
    class Meta(UserUpdateForm.Meta):
        fields = (
            "first_name",
            "last_name",
        )


class UserProfileLanguageUpdateForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        fields = ("language",)


class UserProfileRidesUpdateForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        fields = ("default_rides_view",)


class RegistrationUserProfileUpdateForm(CampaignMixin, forms.ModelForm):
    def clean_mailing_opt_in(self):
        if self.cleaned_data["mailing_opt_in"] is None:
            raise forms.ValidationError(_("Zvolte jednu možnost"))
        else:
            return self.cleaned_data["mailing_opt_in"]

    def __init__(self, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        if "sex" in self.fields:
            self.fields["sex"].required = True
        if "mailing_opt_in" in self.fields:
            self.fields["mailing_opt_in"].initial = None
            self.fields["mailing_opt_in"].required = True
            self.fields["mailing_opt_in"].choices = [
                (
                    True,
                    _(
                        "Ano, chci dostávat soutěžní novinky, informace o akcích a pozvánky do dalších ročníků soutěže."
                    ),
                ),
                (False, _("Ne, mám zájem pouze o informační e-maily.")),
            ]
            self.fields["mailing_opt_in"].label = _(
                "Přejete si dostávat náš newsletter?"
            )
            self.fields["mailing_opt_in"].help_text = None
        return ret_val

    class Meta:
        model = models.UserProfile
        fields = (
            "nickname",
            "sex",
            "mailing_opt_in",
        )
        widgets = {
            "mailing_opt_in": forms.RadioSelect(attrs={"required": True}),
        }


class UserProfileUpdateForm(RegistrationUserProfileUpdateForm):
    class Meta(RegistrationUserProfileUpdateForm.Meta):
        fields = (
            "occupation",
            "sex",
            "age_group",
            "mailing_opt_in",
        )
        widgets = {
            "mailing_opt_in": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        self.fields["mailing_opt_in"].label = _(
            "Chci dostávat e-mailem soutěžní novinky, informace o akcích a pozvánky do dalších ročníků soutěže."
        )
        self.fields["mailing_opt_in"].required = False
        return ret_val


class UserProfileDontShowNameUpdateForm(RegistrationUserProfileUpdateForm):
    class Meta(RegistrationUserProfileUpdateForm.Meta):
        fields = ("nickname",)


class UserAttendanceUpdateForm(CampaignMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        self.fields["personal_data_opt_in"].required = True
        self.fields["personal_data_opt_in"].label = _(
            "Souhlasím se zpracováním osobních údajů podle "
            "<a target='_blank' href='http://www.auto-mat.cz/zasady'>Zásad o ochraně a zpracování údajů AutoMat z.s.</a> "
            "a <a target='_blank' href='http://www.dopracenakole.cz/obchodni-podminky'>Obchodními podmínkami soutěže {campaign}</a>."
            " {extra_agreement_text}",
        ).format(
            campaign=self.campaign,
            extra_agreement_text=self.campaign.extra_agreement_text,
        )
        return ret_val

    class Meta:
        model = models.UserAttendance
        fields = ("personal_data_opt_in",)


class RegistrationProfileUpdateForm(PrevNextMixin, MultiModelForm):
    no_prev = True

    form_classes = OrderedDict(
        [
            ("user", UserUpdateForm),
            ("userprofile", RegistrationUserProfileUpdateForm),
            ("userattendance", UserAttendanceUpdateForm),
        ]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_class = "noAsterisks"
        self.helper.form_id = "personal-data-form"


class ProfileUpdateForm(SubmitMixin, MultiModelForm):
    submit_text = _("Hotovo")

    form_classes = OrderedDict(
        [
            ("user", UserNameUpdateForm),
            ("userprofiledontshowname", UserProfileDontShowNameUpdateForm),
            ("usermail", UserEmailUpdateForm),
            ("userprofile", UserProfileUpdateForm),
            ("userattendance", UserAttendanceUpdateForm),
        ]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_class = "noAsterisks form-horizontal"
        self.helper.label_class = "col-12"
        self.helper.field_class = "col-12"
        self.helper.form_id = "profile-update-form"


class TripForm(InitialFieldsMixin, forms.ModelForm):
    initial_fields = ("direction", "date")
    distance = CommaFloatField(
        label=_("Vzdálenost (km)"),
        required=False,
    )
    duration = CommaFloatField(
        label=_("Doba (min)"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})
        instance = kwargs.get("instance", None)
        if instance is not None and instance.duration:
            initial["duration"] = instance.duration / 60
        else:
            initial["duration"] = 0
        kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def working_day(self):
        return util.working_day(self.initial["date"])

    def get_direction(self):
        return self.initial["direction"] or self.instance.direction

    def get_date(self):
        return self.initial["date"] or self.instance.date

    def clean_user_attendance(self):
        return self.instance.user_attendance or self.initial["user_attendance"]

    def clean(self):
        cleaned_data = super().clean()

        if "commute_mode" in cleaned_data:
            commute_mode_slug = cleaned_data["commute_mode"].slug
            cm = models.CommuteMode.objects.get(slug=commute_mode_slug)
            if cm.distance_important and not cleaned_data.get("distance", False):
                raise forms.ValidationError(_("Musíte vyplnit vzdálenost"))

            if (
                cleaned_data["distance"] is not None
                and cleaned_data["distance"] < cm.minimum_distance
            ):
                raise forms.ValidationError(
                    ngettext("Cesta musí mít minimálně %(km)d kilometru")
                    % {"km": cm.minimum_distance / 1000}
                )
            try:
                if cleaned_data["duration"]:
                    cleaned_data["duration"] = cleaned_data["duration"] * 60
                    if cleaned_data["duration"] < cm.minimum_duration:
                        raise forms.ValidationError(
                            ngettext(
                                "Činnost musí trvat minimálně %(min)d minuta",
                                "Činnost musí trvat minimálně %(min)d minut",
                                cm.minimum_duration / 60,
                            )
                            % {"min": cm.minimum_duration / 60},
                        )
            except KeyError:
                cleaned_data["duration"] = 0
        return cleaned_data

    def has_changed(self, *args, **kwargs):
        return True

    class Meta:
        model = models.Trip
        fields = (
            "commute_mode",
            "distance",
            "duration",
            "direction",
            "user_attendance",
            "date",
        )
        widgets = {
            "user_attendance": forms.HiddenInput(),
            "commute_mode": CommuteModeSelect(),
        }


class TrackTripForm(FormWithTrackMixin, SubmitMixin, TripForm):
    initial_fields = ("user_attendance", "direction", "date")
    origin = forms.CharField(required=False)

    class Meta(TripForm.Meta):
        fields = (
            "commute_mode",
            "distance",
            "duration",
            "direction",
            "user_attendance",
            "date",
            "track",
            "gpx_file",
            "origin",
        )
        widgets = {
            **TripForm.Meta.widgets,
            **{
                "date": forms.TextInput(
                    attrs={"readonly": "readonly", "disabled": "disabled"}
                ),
                "direction": forms.Select(
                    attrs={"readonly": "readonly", "disabled": "disabled"}
                ),
            },
        }

    def clean(self):
        self.cleaned_data["user_attendance"] = (
            self.instance.user_attendance or self.initial["user_attendance"]
        )
        self.clean_parse_and_calculate_track()
        super().clean()

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = "track-trip-form"
        super().__init__(*args, **kwargs)
        self.user_attendance = self.initial["user_attendance"]
        self.date = (
            self.instance.date
            or datetime.datetime.strptime(self.initial["date"], "%Y-%m-%d").date()
        )

        self.fields["track"].widget = UserLeafletWidget(
            user_attendance=self.user_attendance
        )
        self.fields["track"].widget.attrs["geom_type"] = "MULTILINESTRING"
        self.fields["origin"].widget = forms.HiddenInput()


class FullTripForm(forms.ModelForm):
    class Meta:
        model = models.Trip
        fields = (
            "commute_mode",
            "distance",
            "direction",
            "user_attendance",
            "date",
            "track",
            "gpx_file",
            "duration",
            "source_application",
            "source_id",
            "from_application",
        )
