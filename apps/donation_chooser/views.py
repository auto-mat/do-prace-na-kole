
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView

from dpnk.views_mixins import CampaignFormKwargsMixin, UserAttendanceViewMixin

from .forms import CharitativeOrganizationChooserForm
from .models import UserChoice


class CharitativeOrganizationChooserView(CampaignFormKwargsMixin, UserAttendanceViewMixin, UpdateView):
    template_name = 'base_generic_registration_form.html'
    model = UserChoice
    form_class = CharitativeOrganizationChooserForm
    success_url = reverse_lazy("choose_charitative_organization")

    def get_object(self):
        choice, created = UserChoice.objects.get_or_create(user_attendance=self.user_attendance)
        return choice
