from django.db import models
from django.utils.translation import gettext_lazy as _

from dpnk.models import CompanyAdmin, Subsidiary


class BoxRequest(models.Model):
    company_admin = models.ForeignKey(
        CompanyAdmin, on_delete=models.CASCADE, related_name="box_requests"
    )
    subsidiary = models.ForeignKey(
        Subsidiary,
        on_delete=models.CASCADE,
        related_name="box_requests",
        verbose_name=_("Pobočka"),
    )

    class Meta:
        unique_together = ("company_admin", "subsidiary")
