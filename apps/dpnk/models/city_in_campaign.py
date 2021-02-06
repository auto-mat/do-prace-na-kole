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

from cache_utils.decorators import cached

from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import translation

from dpnk.util import get_emissions

from .city import City
from .city_in_campaign_diploma import CityInCampaignDiploma
from .trip import Trip, distance_all_modes
from .user_attendance import UserAttendance


class CityInCampaign(models.Model):
    """Město v kampani"""

    class Meta:
        verbose_name = _(u"Město v kampani")
        verbose_name_plural = _(u"Města v kampani")
        unique_together = (("city", "campaign"),)
        ordering = (
            "campaign",
            "city__name",
        )

    city = models.ForeignKey(
        City,
        null=False,
        blank=False,
        related_name="cityincampaign",
        on_delete=models.CASCADE,
    )
    campaign = models.ForeignKey(
        "Campaign", null=False, blank=False, on_delete=models.CASCADE,
    )
    allow_adding_rides = models.BooleanField(
        verbose_name=_(u"povolit zapisování jízd"),
        null=False,
        blank=False,
        default=True,
    )
    organizer = models.TextField(
        verbose_name=_(u"Jméno pořadatele"), default="", blank=True,
    )
    organizer_url = models.URLField(
        verbose_name=_(u"URL pořadatele"), default="", blank=True,
    )

    @property
    def name(self):
        return self.city.name

    def competitors(self):
        @cached(60)
        def actually_get_competitors(pk):
            return UserAttendance.objects.filter(
                campaign=self.campaign,
                team__subsidiary__city=self.city,
                payment_status__in=("done", "no_admission"),
            )

        return actually_get_competitors(self.pk)

    def competitor_count(self):
        return len(self.competitors())

    def distances(self):
        @cached(60)
        def actually_get_distances(pk):
            return distance_all_modes(
                Trip.objects.filter(user_attendance__in=self.competitors())
            )

        return actually_get_distances(self.pk)

    def eco_trip_count(self):
        return self.distances()["count__sum"]

    def distance(self):
        return self.distances()["distance__sum"]

    def emissions(self):
        return get_emissions(self.distances()["distance__sum"])

    def __str__(self):
        return "%(city)s (%(campaign)s)" % {
            "campaign": self.campaign.name,
            "city": self.city.name,
        }

    def description(self, language="cs"):
        with translation.override(language):
            return _("Do práce na kole v tomto městě pořádá %s") % (self.organizer)

    sandwich_model = CityInCampaignDiploma

    def get_sandwich_type(self):
        return self.campaign.city_in_campaign_diploma_sandwich_type
