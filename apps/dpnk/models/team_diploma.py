from django.contrib.humanize.templatetags.humanize import intcomma
from django.db import models
from django.utils.translation import ugettext_lazy as _

from smmapdfs.model_abcs import PdfSandwichABC, PdfSandwichFieldABC


class TeamDiplomaField(PdfSandwichFieldABC):
    fields = {
        _("Název"): (lambda team: team.name),
        _("Pravidelnost"): (lambda team: intcomma(round(team.get_frequency_percentage(), 0)) + '%'),
        _("Újetych kilometrů"): (lambda team: str(round(team.get_length()))),
    }


class TeamDiploma(PdfSandwichABC):
    field_model = TeamDiplomaField
    obj = models.ForeignKey(
        'Team',
        null=False,
        blank=False,
        default='',
        on_delete=models.CASCADE,
    )
