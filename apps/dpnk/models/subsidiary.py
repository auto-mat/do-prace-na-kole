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
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from memoize import mproperty
from smart_selects.db_fields import ChainedForeignKey

from .address import Address, get_address_string
from .city import City
from .. import util
from ..model_mixins import WithGalleryMixin

from dpnk.cache_middleware import get_request_cache

from django.db.models import Sum, Avg, Count
from .user_attendance import UserAttendance


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(active=True)


class Subsidiary(WithGalleryMixin, models.Model):
    """Pobočka"""

    class Meta:
        verbose_name = _("Pobočka organizace")
        verbose_name_plural = _("Pobočky organizací")
        indexes = [models.Index(fields=["company"], name="subsidiary_company_idx")]

    address = Address()
    company = ChainedForeignKey(
        "Company",
        related_name="subsidiaries",
        null=False,
        blank=False,
    )
    city = models.ForeignKey(
        City,
        verbose_name=_("Soutěžní město"),
        help_text=_("Váš tým se zařadí do žebříčků za nejbližší soutěžní město."),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    active = models.BooleanField(
        verbose_name=_("Aktivní"),
        default=True,
        null=False,
    )

    box_addressee_name = models.CharField(
        verbose_name=_("Jméno adresáta krabice pro pobočku"),
        help_text=_(
            "Jmené osoby, která převezme krabici s tričky a zajistí jeich rozdělení na této pobočce. Nemusí se účastnit soutěže."
        ),
        max_length=30,
        null=True,
        blank=True,
    )
    box_addressee_telephone = models.CharField(
        verbose_name=_("Telefon adresáta krabice pro pobočku"),
        max_length=30,
        null=True,
        blank=True,
    )
    box_addressee_email = models.EmailField(
        verbose_name=_("Email adresáta krabice pro pobočku"),
        null=True,
        blank=True,
    )
    gallery = models.ForeignKey(
        "photologue.Gallery",
        verbose_name=_("Galerie fotek"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    icon = models.ForeignKey(
        "photologue.Photo",
        verbose_name=_("Ikona"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    def __str__(self):
        return "%s - %s" % (get_address_string(self.address), self.city)

    def name(self):
        return get_address_string(self.address)

    def get_recipient_string(self):
        """makes recipient from address_recipient and company name"""
        if self.address_recipient:
            if (
                self.address_recipient.lower().strip()
                == self.company.name.lower().strip()
            ):
                return self.address_recipient
            else:
                return "%s (%s)" % (self.address_recipient, self.company.name)
        else:
            return self.company.name

    def clean(self):
        Address.clean(self.address, self, Subsidiary)
        if (
            self.box_addressee_name
            or self.box_addressee_email
            or self.box_addressee_telephone
        ):
            if not self.box_addressee_name:
                raise ValidationError(
                    {
                        "box_addressee_name": _(
                            "Pokud vyplňujete adresáta krabice, vyplňte prosím i jeho jméno"
                        )
                    }
                )
            if not self.box_addressee_email:
                raise ValidationError(
                    {
                        "box_addressee_email": _(
                            "Pokud vyplňujete adresáta krabice, vyplňte prosím i jeho e-mail"
                        )
                    }
                )
            if not self.box_addressee_telephone:
                raise ValidationError(
                    {
                        "box_addressee_telephone": _(
                            "Pokud vyplňujete adresáta krabice, vyplňte prosím i jeho telefon"
                        )
                    }
                )


class SubsidiaryInCampaign:
    def __init__(self, subsidiary, campaign):
        self.subsidiary = subsidiary
        self.campaign = campaign

    @property
    def _subsidiary_metrics(self):

        cache = get_request_cache()
        cache_key = f"subsidiary_metrics_{self.subsidiary.id}_{self.campaign.id}"

        if cache_key in cache:
            return cache[cache_key]

        result = UserAttendance.objects.filter(
            team__subsidiary=self.subsidiary,
            team__campaign=self.campaign,
            payment_status__in=("done", "no_admission"),
            approved_for_team="approved",
            userprofile__user__is_active=True,
        ).aggregate(
            total_working_rides=Sum("working_rides_base_count"),
            total_distance=Sum("trip_length_total"),
            avg_frequency=Avg("frequency"),
            eco_trip_count=Sum("get_rides_count_denorm"),
        )

        subsidiary_metrics = {
            "working_rides_base_count": result["total_working_rides"] or 0,
            "distance": result["total_distance"] or 0,
            "frequency": result["avg_frequency"] or 0,
            "eco_trip_count": result["eco_trip_count"] or 0,
        }

        cache[cache_key] = subsidiary_metrics

        return subsidiary_metrics

    def calculate_team_metrics(self):

        result = (
            UserAttendance.objects.filter(
                team__subsidiary=self.subsidiary,
                team__campaign=self.campaign,
                payment_status__in=("done", "no_admission"),
                approved_for_team="approved",
                userprofile__user__is_active=True,
            )
            .values("team")
            .annotate(
                member_count=Count("id"),
                total_working_rides=Sum("working_rides_base_count"),
                total_distance=Sum("trip_length_total"),
                avg_frequency=Avg("frequency"),
                eco_trip_count=Sum("get_rides_count_denorm"),
            )
        )

        cache = get_request_cache()

        subsidiary_metrics = {
            "working_rides_base_count": 0,
            "distance": 0,
            "frequency": 0,
            "eco_trip_count": 0,
        }

        members_count = 0
        frequency_sum = 0

        for item in result:

            team_metrics = {
                "working_rides_base_count": item["total_working_rides"] or 0,
                "distance": item["total_distance"] or 0,
                "frequency": item["avg_frequency"] or 0,
                "eco_trip_count": item["eco_trip_count"] or 0,
            }
            subsidiary_metrics["working_rides_base_count"] += team_metrics[
                "working_rides_base_count"
            ]
            subsidiary_metrics["distance"] += team_metrics["distance"]
            frequency_sum += team_metrics["frequency"] * item["member_count"]
            members_count += item["member_count"]
            subsidiary_metrics["eco_trip_count"] += team_metrics["eco_trip_count"]

            cache_key = f"team_metrics_{item['team']}"
            cache[cache_key] = team_metrics

        subsidiary_metrics["frequency"] = (
            frequency_sum / members_count if members_count > 0 else 0
        )

        cache_key = f"subsidiary_metrics_{self.subsidiary.id}_{self.campaign.id}"
        cache[cache_key] = subsidiary_metrics

    @mproperty
    def teams(self):
        return self.subsidiary.teams.filter(campaign=self.campaign)

    @property
    def eco_trip_count(self):
        return self._subsidiary_metrics.get("eco_trip_count")

    @property
    def working_rides_base_count(self):

        return self._subsidiary_metrics.get("working_rides_base_count")

    @property
    def frequency(self):
        return self._subsidiary_metrics.get("frequency")

    @property
    def distance(self):

        return self._subsidiary_metrics.get("distance")

    @mproperty
    def emissions(self):
        return util.get_emissions(self.distance)

    @mproperty
    def __str__prop__(self):
        return str(self.subsidiary)

    def __str__(self):
        return self.__str__prop__
