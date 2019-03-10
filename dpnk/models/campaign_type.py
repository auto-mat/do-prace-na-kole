from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _


class CampaignType(models.Model):
    name = models.CharField(
        unique=True,
        verbose_name=_("Jméno typu kampaně"),
        max_length=60,
        null=False,
    )

    def __str__(self):
        return self.name
