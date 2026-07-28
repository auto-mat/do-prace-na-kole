# Django imports
from braces.views import LoginRequiredMixin
from django.conf import settings
from django.utils.translation import gettext_lazy as _  # noqa
from django.views.generic.base import TemplateView

# Local imports
from ..views_permission_mixins import RegistrationCompleteMixin


class MapView(LoginRequiredMixin, RegistrationCompleteMixin, TemplateView):
    template_name = "dpnk/map.html"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data["leaflet_config"] = settings.LEAFLET_CONFIG
        return context_data
