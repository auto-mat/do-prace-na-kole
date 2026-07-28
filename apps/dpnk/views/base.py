import datetime
import logging
import socket

# Django imports
from braces.views import LoginRequiredMixin

from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView, View
from django.utils.datastructures import MultiValueDictKeyError

# Local imports
from ..forms import UserProfileLanguageUpdateForm
from ..models import UserProfile
from ..views_mixins import (
    TitleViewMixin,
    UserAttendanceViewMixin,
)
from ..views_permission_mixins import RegistrationCompleteMixin

logger = logging.getLogger(__name__)


class UserAttendanceView(
    TitleViewMixin, LoginRequiredMixin, UserAttendanceViewMixin, TemplateView
):
    pass


class LandingView(RegistrationCompleteMixin, UserAttendanceView):
    template_name = "dpnk/landing.html"
    title = _("Vítejte v dalším ročníku soutěže!")

    def dispatch(self, request, *args, **kwargs):
        if self.request.session.get("source") in ("ios-app", "android-app"):
            return redirect(reverse("open-application-with-rest-token", args=["2"]))
        return super().dispatch(request, *args, **kwargs)


class VueView(UserAttendanceView):
    template_name = "dpnk/vue.html"
    title = _("Vítejte v dalším ročníku soutěže!")


def status(request):
    status_page = str(datetime.datetime.now()) + "\n"
    status_page += socket.gethostname()
    return HttpResponse(status_page)


class SwitchLang(LoginRequiredMixin, View):
    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_anonymous:
            user_profile = UserProfile.objects.get(user=self.request.user)
            form = UserProfileLanguageUpdateForm(
                data={"language": self.request.GET.get("lang", None)},
                instance=user_profile,
            )
            if form.is_valid():
                form.save()
        try:
            return redirect(self.request.GET["redirect"])
        except MultiValueDictKeyError:
            return redirect("/")


def test_errors(request):
    """
    This is for testing error logging. Go to the /test_errors/ url and then check sentry to make sure the error reporting is working.
    """
    logger.info("Testing info message", extra={"test": "foobar"})
    logger.debug("Testing debug message", extra={"test": "foobar"})
    logger.warning("Testing warning message", extra={"test": "foobar"})
    logger.exception("Testing exception message", extra={"test": "foobar"})
    logger.error("Testing error message", extra={"test": "foobar"})
    return HttpResponse("Errors send")


class LoggedInUsersListView(LoginRequiredMixin, TemplateView):
    """Logged in users list/count"""

    template_name = "admin/logged_in_user_list.html"
