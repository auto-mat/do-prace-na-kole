from django.contrib.humanize.templatetags.humanize import intcomma
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from smmapdfs.model_abcs import PdfSandwichABC, PdfSandwichFieldABC


class DiplomaField(PdfSandwichFieldABC):
    fields = {
        _("Jméno"): (lambda ua: ua.name()),
        _("Křestní jméno"): (lambda ua: ua.first_name()),
        _("Příjmení"): (lambda ua: ua.last_name()),
        _("Přezdívka"): (lambda ua: ua.userprofile.nickname),
        _("Jméno a příjmení"): (lambda ua: ua.userprofile.user.get_full_name()),
        _("Jméno v plném změní"): (lambda ua: ua.name_for_trusted()),
        _("Jméno vokativ"): (lambda ua: ua.name(cs_vokativ=True)),
        _("Pravidelnost"): (lambda ua: intcomma(round(ua.get_frequency_percentage(), 0)) + '%'),
        _("Újetých kilometrů"): (lambda ua: str(round(ua.trip_length_total_rounded()))),
        _("Újetych kilometrů vč. výlety"): (lambda ua: str(round(ua.trip_length_total_including_recreational_rounded()))),
        _("Ušetřeno oxidu uhličitého"): (lambda ua: intcomma(ua.get_emissions()["co2"]) + " CO2"),
        _("Počet eko cest"): (lambda ua: intcomma(ua.get_rides_count_denorm)),
        _("Pravidelnost týmu"): (lambda ua: (intcomma(round(ua.team.get_frequency_percentage(), 2)) + '%') if ua.team else ""),
        _("Název týmu"): (lambda ua: ua.team.name if ua.team else ""),
        _("Název firmy"): (lambda ua: ua.team.subsidiary.company.name if ua.team else ""),
    }


class Diploma(PdfSandwichABC):
    field_model = DiplomaField
    obj = models.ForeignKey(
        'UserAttendance',
        null=False,
        blank=False,
        default='',
        on_delete=models.CASCADE,
    )

    def get_email(self):
        return self.obj.userprofile.user.email

    def get_context(self, base_url=""):
        return {
            'name': self.obj.name(),
            'name_vocative': self.obj.name(cs_vokativ=True),
            'diplomas_page': base_url + reverse('diplomas'),
        }

    def get_language(self):
        return self.obj.userprofile.language
