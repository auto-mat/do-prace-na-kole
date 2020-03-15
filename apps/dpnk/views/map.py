import datetime
import json

# Django imports
from braces.views import LoginRequiredMixin

from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import BooleanField, Case, Q, When
from django.forms.models import BaseModelFormSet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import cache_control, never_cache
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import CreateView, UpdateView

from extra_views import ModelFormSetView

# Local imports
from .. import calendar
from .. import exceptions
from .. import forms
from .. import models
from .. import results
from .. import util
from ..forms import (
    UserProfileRidesUpdateForm,
)
from ..models import Trip
from ..rest import TripSerializer
from ..views_mixins import (
    RegistrationMessagesMixin,
    RegistrationViewMixin,
    TitleViewMixin,
    UserAttendanceParameterMixin,
)
from ..views_permission_mixins import (
    RegistrationCompleteMixin,
    registration_complete_gate,
)


class MapView(RegistrationCompleteMixin, TemplateView):
    template_name = 'registration/map.html'

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data["leaflet_config"] = settings.LEAFLET_CONFIG
        return context_data
