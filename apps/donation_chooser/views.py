from braces.views import LoginRequiredMixin

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import UpdateView

from dpnk.views_mixins import (
    CampaignFormKwargsMixin,
    TitleViewMixin,
    UserAttendanceViewMixin,
)

from .forms import CharitativeOrganizationChooserForm
from .models import UserChoice


class CharitativeOrganizationChooserView(
    TitleViewMixin,
    LoginRequiredMixin,
    CampaignFormKwargsMixin,
    UserAttendanceViewMixin,
    UpdateView,
):
    template_name = "donation_chooser.html"
    model = UserChoice
    form_class = CharitativeOrganizationChooserForm
    success_url = reverse_lazy("choose_charitative_organization")
    title = _("Vyberte charitativní organizaci")

    def get_object(self):
        choice, created = UserChoice.objects.get_or_create(
            user_attendance=self.user_attendance
        )
        return choice
