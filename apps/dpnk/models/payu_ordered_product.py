"""PayU ordered product(s) model class"""

from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _


class PayUOrderedProduct(models.Model):
    """PayU orderer product(s)

    Products:

    1. RTWBB challenge entry fee
    2. RTWBB donation
    """

    class Meta:
        verbose_name = _("Objednávaný produkt")
        verbose_name_plural = _("Objednávané produkty")

    name = models.CharField(
        verbose_name=_("Jméno objednávaného produktu"),
        max_length=60,
        null=False,
        blank=False,
    )
    unit_price = models.PositiveIntegerField(
        verbose_name=_("Jednotková cena"),
        null=False,
        blank=False,
    )
    quantity = models.PositiveIntegerField(
        verbose_name=_("Množství"),
        null=False,
        blank=False,
    )

    def __str__(self):
        return f"{self.name} {self.unit_price} Kč"
