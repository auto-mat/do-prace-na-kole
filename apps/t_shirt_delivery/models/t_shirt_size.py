# -*- coding: utf-8 -*-

# Author: Hynek Hanke <hynek.hanke@auto-mat.cz>
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2016 o.s. Auto*Mat
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from dpnk.models import Campaign


class TShirtSize(models.Model):
    """Velikost trička"""

    GENDER = [
        ("", _("---------")),
        ("male", _("Muž")),
        ("female", _("Žena")),
        ("unisex", _("Vhodné pro obě pohlaví")),
    ]

    name = models.CharField(
        verbose_name=_("Velikost trička"),
        max_length=40,
        null=False,
    )
    code = models.CharField(
        verbose_name=_("Kód v skladu"),
        max_length=80,
        null=True,
        default="",
        blank=False,
    )
    campaign = models.ForeignKey(
        Campaign,
        verbose_name=_("Kampaň"),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(
        default=0,
        blank=False,
        null=False,
    )
    ship = models.BooleanField(
        verbose_name=_("Posílá se?"),
        default=True,
        null=False,
    )
    available = models.BooleanField(
        verbose_name=_("Je dostupné?"),
        help_text=_("Zobrazuje se v nabídce trik"),
        default=True,
        null=False,
    )
    t_shirt_preview = models.FileField(
        verbose_name=_("Náhled trika"),
        upload_to="t_shirt_preview",
        blank=True,
        null=True,
        max_length=512,
    )
    price = models.IntegerField(
        verbose_name=_("Cena"),
        default=0,
        blank=False,
        null=False,
    )
    # Required for RTWBB frontend app
    name1 = models.CharField(
        verbose_name=_("Název trička"),
        help_text=_("Požadováno pro novou RTWBB frontend aplikaci"),
        max_length=40,
        null=False,
        blank=False,
        default="",
    )
    # Required for new RTWBB frontend app
    sex = models.CharField(
        verbose_name=_("Pohlaví"),
        help_text=_("Požadováno pro novou RTWBB frontend aplikaci"),
        choices=GENDER,
        max_length=10,
        null=False,
        blank=True,
        default="",
    )
    # Required for new RTWBB frontend app
    size = models.CharField(
        verbose_name=_("Velikost"),
        help_text=_("Požadováno pro novou RTWBB frontend aplikaci"),
        max_length=20,
        null=False,
        blank=True,
        default="",
    )
    # Required for new RTWBB frontend app
    author = models.CharField(
        verbose_name=_("Autor"),
        help_text=_("Požadováno pro novou RTWBB frontend aplikaci"),
        max_length=30,
        null=False,
        blank=True,
        default="",
    )
    # Required for new RTWBB frontend app
    material = models.CharField(
        verbose_name=_("Materiál"),
        help_text=_("Požadováno pro novou RTWBB frontend aplikaci"),
        max_length=40,
        null=False,
        blank=True,
        default="",
    )
    # Required for new RTWBB frontend app
    description = models.TextField(
        verbose_name=_("Popis"),
        help_text=_("Požadováno pro novou RTWBB frontend aplikaci"),
        max_length=512,
        null=False,
        blank=True,
        default="",
    )

    class Meta:
        verbose_name = _("Velikost trička")
        verbose_name_plural = _("Velikosti trička")
        unique_together = (("name", "campaign"),)
        db_table = "t_shirt_delivery_tshirtsize"
        ordering = ["order"]

    def user_string(self):
        if self.price == 0:
            return self.name
        else:
            return "%s (%s Kč navíc)" % (self.name, self.price)

    def __str__(self):
        if self.price == 0:
            return "%s (%s)" % (self.name, self.campaign.slug)
        else:
            return "%s (%s, %s Kč navíc)" % (self.name, self.campaign.slug, self.price)
