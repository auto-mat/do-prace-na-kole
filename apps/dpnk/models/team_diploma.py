from django.db import models
from django.utils.translation import ugettext_lazy as _

from smmapdfs.model_abcs import PdfSandwichABC, PdfSandwichFieldABC


class TeamDiplomaField(PdfSandwichFieldABC):
    fields = {
        _("Název"): (lambda team: team.name),
        _("Pravidelnost"): (lambda team: '%d%%' % team.get_frequency_percentage()),
        _("Újetych kilometrů"): (lambda team: str(round(team.get_length()))),
        _("Název firmy"): (lambda team: team.subsidiary.company.name if team else ""),
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
