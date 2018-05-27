from django.contrib.humanize.templatetags.humanize import intcomma
from django.db import models
from django.utils.translation import ugettext_lazy as _

from smmapdfs.model_abcs import PdfSandwichABC, PdfSandwichFieldABC


class DiplomaField(PdfSandwichFieldABC):
    fields = {
        _("Jméno"): (lambda ua: ua.name()),
        _("Pravidelnost"): (lambda ua: intcomma(round(ua.get_frequency_percentage(), 2)) + '%'),
        _("Újetych kilometrů"): (lambda ua: intcomma(round(ua.trip_length_total_rounded(), 2)) + " Km"),
        _("Ušetřené oxidu uhličitého"): (lambda ua: intcomma(ua.get_emissions()["co2"]) + " CO2"),
        _("Počet eko cest"): (lambda ua: intcomma(ua.get_rides_count_denorm)),
        _("Pravidelnost týmu"): (lambda ua: (intcomma(round(ua.team.get_frequency_percentage(), 2)) + '%') if ua.team else ""),
        _("Nazev týmu"): (lambda ua: ua.team.name if ua.team else ""),
        _("Nazev firmy"): (lambda ua: ua.team.subsidiary.company.name if ua.team else ""),
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

    def get_name(self):
        return self.obj.name()

    def get_language(self):
        return self.obj.userprofile.language
