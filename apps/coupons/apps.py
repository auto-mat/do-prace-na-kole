from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class CouponsConfig(AppConfig):
    name = "coupons"
    verbose_name = _("Kupóny")
