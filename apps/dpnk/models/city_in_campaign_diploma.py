from django.db import models
from django.utils.translation import gettext_lazy as _

from smmapdfs.model_abcs import PdfSandwichABC, PdfSandwichFieldABC


class CityInCampaignDiplomaField(PdfSandwichFieldABC):
    fields = {
        _("Název"): (lambda cic: cic.city.name),
        _("Počet soutěžících"): (lambda city: str(city.competitor_count())),
        _("Celková vzdálenost (km)"): (
            lambda city: str(round(city.distances()["distance__sum"]))
        ),
        _("Ušetřené emise CO2 (g)"): (lambda city: str(city.emissions["co2"])),
    }


class CityInCampaignDiploma(PdfSandwichABC):
    field_model = CityInCampaignDiplomaField
    obj = models.ForeignKey(
        "CityInCampaign",
        null=False,
        blank=False,
        default="",
        on_delete=models.CASCADE,
    )
