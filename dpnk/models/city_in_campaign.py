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
from django.utils.translation import ugettext_lazy as _

from .city import City


class CityInCampaign(models.Model):
    """Město v kampani"""

    class Meta:
        verbose_name = _(u"Město v kampani")
        verbose_name_plural = _(u"Města v kampani")
        unique_together = (("city", "campaign"),)
        ordering = ('campaign', 'city__name',)
    city = models.ForeignKey(
        City,
        null=False,
        blank=False,
        related_name="cityincampaign",
        on_delete=models.CASCADE,
    )
    campaign = models.ForeignKey(
        "Campaign",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    allow_adding_rides = models.BooleanField(
        verbose_name=_(u"povolit zapisování jízd"),
        null=False,
        blank=False,
        default=True,
    )

    def __str__(self):
        return "%(city)s (%(campaign)s)" % {'campaign': self.campaign.name, 'city': self.city.name}
