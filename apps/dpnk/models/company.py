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
from author.decorators import with_author

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from memoize import mproperty

from stdnumfield.models import StdNumField

from .address import CompanyAddress, get_address_string
from .subsidiary import SubsidiaryInCampaign
from .. import util
from ..model_mixins import WithGalleryMixin

from dpnk.cache_middleware import get_request_cache

from django.db.models import Sum, Avg, Count
from .user_attendance import UserAttendance

ICO_ERROR_MESSAGE = _(
    "IČO není zadáno ve správném formátu. Zkontrolujte že číslo má osm číslic a případně ho doplňte nulami zleva."
)
DIC_ERROR_MESSAGE = _(
    "DIČ není zadáno ve správném formátu. "
    "Zkontrolujte že číslo má 8 až 10 číslic a případně ho doplňte nulami zleva. "
    "Číslu musí předcházet dvě písmena identifikátoru země (např. CZ)",
)


@with_author
class Company(WithGalleryMixin, models.Model):
    """Organizace"""

    class Meta:
        verbose_name = _("Organizace")
        verbose_name_plural = _("Organizace")
        ordering = ("name",)

    ORGANIZATION_TYPE = [
        ("company", _("Organizace")),
        ("family", _("Rodina")),
        ("school", _("Škola")),
    ]

    name = models.CharField(
        unique=True,
        verbose_name=_("Název společnosti"),
        max_length=60,
        null=False,
    )
    type = models.ForeignKey(
        "dpnk.CompanyType",
        verbose_name=_("Company type"),
        related_name="company_type",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    address = CompanyAddress()
    dic = StdNumField(
        "cz.dic",
        verbose_name=_("DIČ"),
        max_length=15,
        default="",
        validators=[
            RegexValidator(
                r"^[a-zA-Z]{2}[0-9]*$",
                _("DIČ musí být číslo uvozené dvoupísmeným identifikátorem státu."),
            )
        ],
        error_messages={"stdnum_format": DIC_ERROR_MESSAGE},
        blank=True,
        null=True,
    )
    active = models.BooleanField(
        verbose_name=_("Aktivní"),
        default=True,
        null=False,
    )
    ico = StdNumField(
        "cz.dic",
        default=None,
        verbose_name=_("IČO"),
        validators=[RegexValidator(r"^[0-9]*$", _("IČO musí být číslo"))],
        error_messages={"stdnum_format": ICO_ERROR_MESSAGE},
        blank=True,
        null=True,
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
    note = models.TextField(
        verbose_name=_("Poznámka"),
        null=True,
        blank=True,
    )
    organization_type = models.CharField(
        verbose_name=_("Typ organizace"),
        choices=ORGANIZATION_TYPE,
        max_length=20,
        null=False,
        blank=True,
        default=ORGANIZATION_TYPE[0][0],
    )

    def has_filled_contact_information(self):
        address_complete = (
            self.address.street
            and self.address.street_number
            and self.address.psc
            and self.address.city
        )
        return bool(self.name and address_complete and self.ico)

    def __str__(self):
        return "%s" % self.name

    def company_address(self):
        return get_address_string(self.address)

    def admin_emails(self, campaign):
        admins = (
            self.company_admin.filter(campaign=campaign)
            .select_related("userprofile__user")
            .order_by("userprofile__user__email")
        )
        return ", ".join([a.userprofile.user.email for a in admins])

    def admin_telephones(self, campaign):
        admins = self.company_admin.filter(campaign=campaign)
        return ", ".join([a.userprofile.telephone for a in admins])

    def clean(self, *args, **kwargs):
        if (
            Company.objects.filter(name__unaccent__iexact=self.name)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                {
                    "name": _(
                        "Organizace s tímto názvem již existuje. Nemusíte tedy zakládat novou, vyberte tu stávající."
                    )
                }
            )

        allow_duplicate_ico = getattr(self, "allow_duplicate_ico", False)
        if (
            allow_duplicate_ico is not True
            and self.ico
            and not Company.objects.filter(pk=self.pk, ico=self.ico).exists()
            and Company.objects.filter(  # Don't throw validation error if nothing changed
                ico=self.ico, active=True
            )
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                {
                    "ico": "Organizace s tímto IČO již existuje, nezakládemte prosím novou, ale vyberte jí prosím ze seznamu"
                }
            )

    def get_related_competitions(self, campaign):
        """Get all competitions where this company is involved filtered by given campaign"""
        from .competition import Competition

        cities = self.subsidiaries.values("city")
        competitions = Competition.objects.filter(company__isnull=True).filter(
            Q(city__in=cities, campaign=campaign)
            | Q(city__isnull=True, campaign=campaign),
        )
        return competitions

    @classmethod
    def export_resource_classes(cls):
        from .. import resources

        return {
            "company_history": (
                "Company histories",
                resources.create_company_history_resource(),
            ),
        }

    def company_in_campaign(self, campaign):
        return CompanyInCampaign(self, campaign)

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self.pk:
            for subsidiary in self.subsidiaries.all():
                for team in subsidiary.teams.all():
                    for user in team.users.all():
                        if hasattr(user, "userprofile"):
                            # Delete REST API cache
                            cache = util.Cache(
                                key=f"{util.register_challenge_serializer_base_cache_key_name}"
                                f"{user.userprofile.id}"
                            )
                            if cache.data:
                                del cache.data
        super().save(force_insert, force_update, *args, **kwargs)


class CompanyInCampaign:
    def __init__(self, company, campaign):
        self.company = company
        self.campaign = campaign

    @mproperty
    def name(self):
        return self.company.name

    @mproperty
    def subsidiaries(self):
        subsidiaries = []
        for subsidiary in self.company.subsidiaries.all():
            subsidiaries.append(SubsidiaryInCampaign(subsidiary, self.campaign))
        return subsidiaries

    @property
    def eco_trip_count(self):
        return self._company_metrics.get("eco_trip_count")

    @property
    def _company_metrics(self):

        cache = get_request_cache()
        cache_key = f"company_metrics_{self.company.id}_{self.campaign.id}"

        if cache_key in cache:
            return cache[cache_key]

        result = UserAttendance.objects.filter(
            team__subsidiary__company=self.company,
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

        company_metrics = {
            "working_rides_base_count": result["total_working_rides"] or 0,
            "distance": result["total_distance"] or 0,
            "frequency": result["avg_frequency"] or 0,
            "eco_trip_count": result["eco_trip_count"] or 0,
        }

        cache[cache_key] = company_metrics

        return company_metrics

    def calculate_subsidiary_metrics(self):

        result = (
            UserAttendance.objects.filter(
                team__subsidiary__company=self.company,
                team__campaign=self.campaign,
                payment_status__in=("done", "no_admission"),
                approved_for_team="approved",
                userprofile__user__is_active=True,
            )
            .values("team__subsidiary")
            .annotate(
                member_count=Count("id"),
                total_working_rides=Sum("working_rides_base_count"),
                total_distance=Sum("trip_length_total"),
                avg_frequency=Avg("frequency"),
                eco_trip_count=Sum("get_rides_count_denorm"),
            )
        )

        cache = get_request_cache()

        company_metrics = {
            "working_rides_base_count": 0,
            "distance": 0,
            "frequency": 0,
            "eco_trip_count": 0,
        }

        members_count = 0
        frequency_sum = 0

        for item in result:

            subsidiary_metrics = {
                "working_rides_base_count": item["total_working_rides"] or 0,
                "distance": item["total_distance"] or 0,
                "frequency": item["avg_frequency"] or 0,
                "eco_trip_count": item["eco_trip_count"] or 0,
            }
            company_metrics["working_rides_base_count"] += subsidiary_metrics[
                "working_rides_base_count"
            ]
            company_metrics["distance"] += subsidiary_metrics["distance"]
            frequency_sum += subsidiary_metrics["frequency"] * item["member_count"]
            members_count += item["member_count"]
            company_metrics["eco_trip_count"] += subsidiary_metrics["eco_trip_count"]

            cache_key = (
                f"subsidiary_metrics_{item['team__subsidiary']}_{self.campaign.id}"
            )
            cache[cache_key] = subsidiary_metrics

        company_metrics["frequency"] = (
            frequency_sum / members_count if members_count > 0 else 0
        )

        cache_key = f"company_metrics_{self.company.id}_{self.campaign.id}"
        cache[cache_key] = company_metrics

    @property
    def working_rides_base_count(self):

        return self._company_metrics.get("working_rides_base_count")

    @property
    def frequency(self):
        return self._company_metrics.get("frequency")

    @property
    def distance(self):

        return self._company_metrics.get("distance")

    @property
    def emissions(self):
        return util.get_emissions(self.distance)


class CompanyType(models.Model):
    class Meta:
        verbose_name = _("Typ společnosti")
        verbose_name_plural = _("Typy společností")

    type = models.CharField(
        verbose_name=_("Typ"),
        max_length=255,
    )

    def __str__(self):
        return str(self.type)
