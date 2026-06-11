from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DonationChooserConfig(AppConfig):
    name = "donation_chooser"
    verbose_name = _("Charitativní organizace")
