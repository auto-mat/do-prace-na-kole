import logging

# Django imports
from braces.views import LoginRequiredMixin

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_control, never_cache
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import UpdateView

# Local imports
from ..email import (
    team_membership_approval_mail,
    team_membership_denial_mail,
)
from ..forms import (
    PhotoForm,
    TeamSettingsForm,
)
from ..models import UserAttendance
from ..views_mixins import (
    CampaignParameterMixin,
    TitleViewMixin,
    UserAttendanceParameterMixin,
    UserAttendanceViewMixin,
)
from ..views_permission_mixins import (
    MustBeApprovedForTeamMixin,
    MustBeInRegistrationPhaseMixin,
)

logger = logging.getLogger(__name__)


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
    template_name = "dpnk/edit_team.html"
    form_class = TeamSettingsForm
    success_url = reverse_lazy("team_members")
    title = _("Upravit údaje týmu")
    registration_phase = "zmenit_tym"
    success_message = _("Hurá! Povedlo se.")

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data["registration_phase"] = self.registration_phase
        context_data["team"] = self.user_attendance.team
        return context_data

    def get_object(self):
        return self.user_attendance.team

    def get_initial(self):
        return {"campaign": self.campaign}


class UploadTeamPhoto(
    UserAttendanceViewMixin,
    View,
):
    def post(self, *args, **kwargs):
        slug = "team_%s_photo_%s" % (
            self.user_attendance.team.pk,
            self.user_attendance.team.get_gallery().photo_count(public=False),
        )
        form_data = {
            "galleries": [self.user_attendance.team.get_gallery()],
            "slug": slug,
            "title": slug,
            "is_public": False,
        }
        form = PhotoForm(form_data, self.request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponse("Success")
        else:
            return HttpResponse(form.errors, status=400)


class TeamMembers(
    TitleViewMixin,
    LoginRequiredMixin,
    UserAttendanceViewMixin,
    MustBeInRegistrationPhaseMixin,
    MustBeApprovedForTeamMixin,
    TemplateView,
):
    template_name = "dpnk/team_admin_members.html"
    registration_phase = "zmenit_tym"

    def get_title(self, *args, **kwargs):
        return _("Tým %s") % self.user_attendance.team.name

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if "approve" in request.POST:
            approve_id = None
            try:
                action, approve_id = request.POST["approve"].split("-")
            except ValueError:
                logger.exception(
                    "Can't split POST approve parameter", extra={"request": request}
                )
                messages.add_message(
                    request,
                    messages.ERROR,
                    _(
                        "Nastala chyba při přijímání uživatele, patrně používáte zastaralý internetový prohlížeč."
                    ),
                )

            if approve_id:
                approved_user = UserAttendance.objects.get(id=approve_id)
                userprofile = approved_user.userprofile
                if (
                    approved_user.approved_for_team not in ("undecided", "denied")
                    or not userprofile.user.is_active
                    or approved_user.team != self.user_attendance.team
                ):
                    logger.error(
                        "Approving user with wrong parameters.",
                        extra={
                            "request": request,
                            "user": userprofile.user,
                            "username": userprofile.user.username,
                            "approval": approved_user.approved_for_team,
                            "team": approved_user.team,
                            "active": userprofile.user.is_active,
                        },
                    )
                    messages.add_message(
                        request,
                        messages.ERROR,
                        _(
                            "Tento uživatel již byl přijat do týmu. Pravděpodobně jste dvakrát odeslali formulář."
                        ),
                        extra_tags="user_attendance_%s" % approved_user.pk,
                        fail_silently=True,
                    )
                else:
                    approve_for_team(
                        request,
                        approved_user,
                        request.POST.get("reason-" + str(approved_user.id), ""),
                        action == "approve",
                        action == "deny",
                    )
        return render(request, self.template_name, self.get_context_data())

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        team = self.user_attendance.team
        if not team:
            return {
                "fullpage_error_message": _(
                    "Další členové Vašeho týmu se zobrazí, jakmile budete mít vybraný tým"
                ),
                "title": _("Není vybraný tým"),
            }

        context_data["team_members"] = UserAttendance.objects.filter(
            team=team, userprofile__user__is_active=True
        )
        context_data["registration_phase"] = self.registration_phase
        context_data["team"] = team
        return context_data


class OtherTeamMembers(
    UserAttendanceViewMixin,
    TitleViewMixin,
    MustBeApprovedForTeamMixin,
    LoginRequiredMixin,
    TemplateView,
):
    template_name = "dpnk/team_members.html"
    title = ""

    @method_decorator(never_cache)
    @method_decorator(cache_control(max_age=0, no_cache=True, no_store=True))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        team_members = []
        if self.user_attendance.team:
            team_members = self.user_attendance.team.all_members()
            team_members = team_members.select_related(
                "userprofile__user",
                "team__subsidiary__city",
                "team__subsidiary__company",
                "campaign",
            )
        context_data["team_members"] = team_members
        context_data["registration_phase"] = "other_team_members"
        return context_data

    # This is here for NewRelic to distinguish from TemplateView.get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class Company(
    UserAttendanceViewMixin,
    MustBeApprovedForTeamMixin,
    LoginRequiredMixin,
    TemplateView,
):
    template_name = "dpnk/company.html"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data[
            "company"
        ] = self.user_attendance.team.subsidiary.company.company_in_campaign(
            self.user_attendance.campaign
        )
        return context_data


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
        user_attendance.approved_for_team = "denied"
        user_attendance.save()
        team_membership_denial_mail(user_attendance, request.user, reason)
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Členství uživatele %s ve Vašem týmu bylo zamítnuto" % user_attendance),
            extra_tags="user_attendance_%s" % user_attendance.pk,
            fail_silently=True,
        )
        return
    elif approve:
        if user_attendance.campaign.too_much_members(
            user_attendance.team.members.count() + 1
        ):
            messages.add_message(
                request,
                messages.ERROR,
                _("Tým je již plný, další člen již nemůže být potvrzen."),
                extra_tags="user_attendance_%s" % user_attendance.pk,
                fail_silently=True,
            )
            return
        user_attendance.approved_for_team = "approved"
        user_attendance.save()
        team_membership_approval_mail(user_attendance)
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Členství uživatele %(user)s v týmu %(team)s bylo odsouhlaseno.")
            % {"user": user_attendance, "team": user_attendance.team.name},
            extra_tags="user_attendance_%s" % user_attendance.pk,
            fail_silently=True,
        )
        return
