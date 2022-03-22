from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class DonationChooserConfig(AppConfig):
    name = "donation_chooser"
    verbose_name = _("Charitativní organizace")
