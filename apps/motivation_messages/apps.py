from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MotivationMessagesConfig(AppConfig):
    name = "motivation_messages"
    verbose_name = _("Motivační hlášky")
