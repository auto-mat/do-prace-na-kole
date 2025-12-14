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
import datetime
import babel

from babel.dates import format_date
from cache_utils.decorators import cached
from colorfield.fields import ColorField
from denorm import denormalized, depend_on_related

from django.conf import settings
from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Max
from django.utils.html import escape
from django.utils.translation import get_language, ugettext_lazy as _

from price_level.models import Pricable

from smmapdfs.models import PdfSandwichType

from .phase import Phase
from .user_attendance import UserAttendance
from .. import util


class Campaign(Pricable, models.Model):
    """kampaň"""

    class Meta:
        verbose_name = _("kampaň")
        verbose_name_plural = _("kampaně")
        permissions = (("can_see_application_links", "Can see application links"),)
        ordering = ("-id",)
        unique_together = [
            ("mailing_list_type", "mailing_list_id"),
            ("campaign_type", "year"),
        ]

    campaign_type = models.ForeignKey(
        "CampaignType",
        verbose_name=_("Typ kampaně"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="campaigns",
    )
    year = models.CharField(
        unique=False,
        verbose_name=_("Ročník kampaně"),
        max_length=60,
        null=False,
        default=datetime.datetime.now().year,
    )
    slug = models.SlugField(
        unique=True,
        verbose_name="Doména v URL",
        blank=False,
    )
    slug_identifier = models.SlugField(
        unique=True,
        verbose_name="Identifikátor kampaně",
        blank=True,
        null=True,
    )
    previous_campaign = models.ForeignKey(
        "Campaign",
        verbose_name=_("Předchozí kampaň"),
        help_text=_(
            "Kampaň, ze které se přebírá velikost trička, nazev týmu atd... při vytváření nové účasti v kampani"
        ),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    email_footer = models.TextField(
        verbose_name=_("Patička uživatelských e-mailů"),
        default="",
        max_length=5000,
        null=True,
        blank=True,
    )
    mailing_list_id = models.CharField(
        verbose_name=_("ID mailing listu"),
        max_length=60,
        default="",
        blank=True,
        null=False,
    )
    mailing_list_type = models.CharField(
        verbose_name=_("ID mailing listu"),
        choices=[
            (None, _("Disabled")),
            ("campaign_monitor", _("Campaign monitor")),
            ("ecomail", _("EcoMail")),
        ],
        max_length=60,
        default=None,
        blank=True,
        null=True,
    )
    show_application_links = models.BooleanField(
        verbose_name=_("Ukázat odkazy na aplikace"),
        default=False,
        null=False,
    )
    mailing_list_enabled = models.NullBooleanField(
        verbose_name=_("Povolit mailing list"),
        default=None,
        null=True,
        blank=True,
        unique=True,  # Enabling mailing lists on more campaigns cause problems. This prevents it until it is fixed.
    )
    extra_agreement_text = models.TextField(
        verbose_name=_("Další text pro uživatelské souhlas"),
        blank=True,
        default="",
    )
    days_active = models.PositiveIntegerField(
        verbose_name=_("Počet minulých dní, které jdou zapisovat"),
        default=7,
        blank=False,
        null=False,
    )
    minimum_rides_base = models.PositiveIntegerField(
        verbose_name=_("Minimální základ počtu jízd"),
        help_text=_(
            "Minimální počet jízd, které je nutné si zapsat, aby bylo možné dosáhnout 100% jízd"
        ),
        default=25,
        blank=False,
        null=False,
    )
    minimum_percentage = models.FloatField(
        verbose_name=_("Minimální procento pro kvalifikaci do pravidelnostní soutěže"),
        default=66.6,
        blank=False,
        null=False,
    )
    trip_plus_distance = models.PositiveIntegerField(
        verbose_name=_("Maximální navýšení vzdálenosti"),
        help_text=_("Počet kilometrů, o které je možné prodloužit si jednu jízdu"),
        default=5,
        blank=True,
        null=True,
    )
    tracking_number_first = models.PositiveIntegerField(
        verbose_name=_("První číslo řady pro doručování balíčků"),
        default=0,
        blank=False,
        null=False,
    )
    tracking_number_last = models.PositiveIntegerField(
        verbose_name=_("Poslední číslo řady pro doručování balíčků"),
        default=999999999,
        blank=False,
        null=False,
    )
    package_height = models.PositiveIntegerField(
        verbose_name=_("Výška balíku"),
        default=1,
        blank=True,
        null=True,
    )
    package_width = models.PositiveIntegerField(
        verbose_name=_("Šířka balíku"),
        default=26,
        blank=True,
        null=True,
    )
    package_depth = models.PositiveIntegerField(
        verbose_name=_("Hloubka balíku"),
        default=35,
        blank=True,
        null=True,
    )
    package_max_count = models.PositiveIntegerField(
        verbose_name=_("Maximální počet triček v krabici"),
        default=50,
        blank=True,
        null=True,
    )
    package_weight = models.FloatField(
        verbose_name=_("Váha balíku"),
        null=True,
        blank=True,
        default=0.25,
        validators=[
            MaxValueValidator(1000),
            MinValueValidator(0),
        ],
    )
    invoice_sequence_number_first = models.PositiveIntegerField(
        verbose_name=_("První číslo řady pro faktury"),
        default=1,
        blank=False,
        null=False,
    )
    invoice_sequence_number_last = models.PositiveIntegerField(
        verbose_name=_("Poslední číslo řady pro faktury"),
        default=999999999,
        blank=False,
        null=False,
    )
    benefitial_admission_fee = models.FloatField(
        verbose_name=_("Benefiční startovné"),
        null=False,
        default=0,
    )
    benefitial_admission_fee_company = models.FloatField(
        verbose_name=_("Benefiční startovné pro organizace"),
        null=False,
        default=0,
    )
    free_entry_cases_html = models.TextField(
        verbose_name=_("Případy, kdy je startovné zdarma"),
        null=True,
        blank=True,
    )
    club_membership_integration = models.BooleanField(
        verbose_name=_("Povolit integraci s klubem přátel?"),
        default=True,
    )
    track_required = models.BooleanField(
        verbose_name=_("DEPRECATED"),
        default=False,
        null=False,
    )
    tracks = models.BooleanField(
        verbose_name=_("Umožnit soutěžícím uložit trasu?"),
        default=True,
    )
    recreational = models.BooleanField(
        verbose_name=_("Lze zadávat i výlety"),
        default=False,
    )
    wp_api_date_from = models.DateField(
        verbose_name=_(
            "Datum, od kterého se zobrazují příspěvky z Wordpress API se články"
        ),
        null=True,
        blank=True,
    )
    max_team_members = models.PositiveIntegerField(
        verbose_name=_("Počet lidí v týmu"),
        default=5,
        blank=True,
        null=True,
    )

    sandwich_type = models.ForeignKey(
        PdfSandwichType,
        null=True,
        blank=True,
        default="",
        on_delete=models.SET_NULL,
    )
    team_diploma_sandwich_type = models.ForeignKey(
        PdfSandwichType,
        related_name="team_diploma_campaign",
        null=True,
        blank=True,
        default="",
        on_delete=models.SET_NULL,
    )
    city_in_campaign_diploma_sandwich_type = models.ForeignKey(
        PdfSandwichType,
        related_name="city_in_campaign_diploma_campaign",
        null=True,
        blank=True,
        default="",
        on_delete=models.SET_NULL,
    )

    def display_name(self):
        if self.name:
            return self.name
        if self.campaign_type is None:
            return "No campaign type " + str(self.year)
        return self.campaign_type.name + " " + str(self.year)

    def __str__(self):
        return self.display_name()

    def tagline(self):
        return self.campaign_type.tagline % str(self.year)

    def competitors_choose_team(self):
        return self.max_team_members > 1

    def too_much_members(self, member_count):
        if self.max_team_members is None:
            return False
        return member_count > self.max_team_members

    def active(self):
        return self.day_active(util.today())

    def entry_enabled_end(self):
        return self.phase("entry_enabled").date_to

    def day_active(self, day, day_today=None):
        """Return if this day can be changed by user"""
        try:
            entry_phase = self.phase("entry_enabled")
            if not entry_phase.is_actual():
                return False
        except Phase.DoesNotExist:
            pass
        competition_phase = self.phase("competition")
        return self.day_recent(day, day_today) and competition_phase.day_in_phase(day)

    def day_recent(self, day, day_today=None):
        """
        Returns true if the current day is today or in the recent past. Recent beting defined by "campaign.days_active".
        """
        if day_today is None:
            day_today = util.today()
        return (day <= day_today) and (
            day > self._first_possibly_active_day(day_today=day_today)
        )

    def _first_possibly_active_day(self, day_today=None):
        if day_today is None:
            day_today = util.today()
        return day_today - datetime.timedelta(days=self.days_active)

    def vacation_day_active(self, day):
        """Return if this day can be added as vacation"""
        day_today = util.today()
        last_day = self.competition_phase().date_to
        return (day <= last_day) and (day > day_today)

    def possible_vacation_days(self):
        """Return days, that can be added as vacation"""

        @cached(60)
        def get_days(pk):
            competition_phase = self.competition_phase()
            return [
                d
                for d in util.daterange(
                    competition_phase.date_from, competition_phase.date_to
                )
                if self.vacation_day_active(d)
            ]

        return get_days(self.pk)

    def user_attendances_for_delivery(self):
        from t_shirt_delivery.models import PackageTransaction

        return (
            UserAttendance.objects.filter(
                campaign=self,
                payment_status__in=("done", "no_admission"),
                t_shirt_size__ship=True,
            )
            .exclude(
                transactions__packagetransaction__status__in=PackageTransaction.shipped_statuses,
            )
            .exclude(
                team=None,
            )
            .annotate(
                payment_created=Max("transactions__payment__created"),
            )
            .order_by(
                "payment_created",
            )
            .distinct()
        )

    def get_complementary_school_campaign(self):
        @cached(60)
        def get_campaign(pk):
            try:
                return Campaign.objects.get(year=self.year, campaign_type__slug="skoly")
            except Campaign.DoesNotExist:
                return None

        return get_campaign(self.pk)

    def get_complementary_main_campaign(self):
        try:
            return Campaign.objects.get(year=self.year, campaign_type__slug="dpnk")
        except Campaign.DoesNotExist:
            return None

    def get_base_url(self, request=None):
        return util.get_base_url(request, self.slug)

    def get_directions(self):
        if self.recreational:
            return ("trip_to", "trip_from", "recreational")
        else:
            return ("trip_to", "trip_from")

    @denormalized(models.BooleanField, default=True)
    @depend_on_related(
        "t_shirt_delivery.TShirtSize", type="backward", foreign_key="campaign"
    )
    def has_any_tshirt(self):
        return self.tshirtsize_set.exists()

    def phase(self, phase_type):
        """
        Return phase of given type from this campaign.
        @phase_type Type of phase.
        """

        @cached(60)
        def get_phase(pk, phase_type):
            try:
                return self.phase_set.get(phase_type=phase_type)
            except Phase.DoesNotExist:
                return False

        result = get_phase(self.pk, phase_type)
        if not result:
            get_phase.invalidate(self.pk, phase_type)
            raise Phase.DoesNotExist
        return result

    def competition_phase(self):
        return self.phase("competition")

    #############################################
    # DEPRECATED ################################
    #############################################
    name = models.CharField(
        unique=False,
        verbose_name=_("Deprecated: Jméno kampaně"),
        max_length=60,
        null=True,
    )
    wp_api_url = models.URLField(
        default="http://www.dopracenakole.cz",
        verbose_name=_("Deprecated: Adresa pro Wordpress API se články"),
        null=True,
        blank=True,
    )
    web = models.URLField(
        verbose_name=_("Deprecated: Web kampáně"),
        default="http://www.dopracenakole.cz",
        blank=True,
        null=True,
    )
    contact_email = models.CharField(
        verbose_name=_("Deprecated: Kontaktní e-mail"),
        default="kontakt@dopracenakole.cz",
        max_length=80,
        blank=True,
        null=True,
    )
    sitetree_postfix = models.CharField(
        verbose_name=_("Deprecated: Postfix pro menu"),
        max_length=60,
        null=True,
        blank=True,
        default="",
    )

    LANGUAGE_PREFIXES = [
        ("dpnk", _("Do práce na kole")),
        ("dsnk", _("Do školy na kole")),
    ]
    language_prefixes = models.CharField(
        verbose_name=_("Deprecated: Jazyková sada"),
        choices=LANGUAGE_PREFIXES,
        max_length=16,
        null=False,
        blank=False,
        default="dpnk",
    )
    main_color = ColorField(
        default="#1EA04F",
        verbose_name="Deprecated: Hlavní barva kampaně",
    )
    description = models.TextField(
        verbose_name=_("Popis"),
        max_length=5000,
        help_text=escape(
            "<h1>Chystáme pro vás Lednovou výzvu Do práce na kole, pěšky či poklusem <YEAR>.</h1>"
            "<p>Výzva jednotlivců se uskuteční v termínu <COMPETITION_PHASE_INTERVAL_DATE>.</p>"
            "<p>Účast je zdarma, registraci otevíráme <REGISTRATION_PHASE_START_DATE> zde.</p>"
        ),
        null=True,
        blank=True,
    )

    def interpolate_description(self):
        """Interpolate description field value"""
        registration_phase = self.phase(phase_type="registration")
        competition_phase = self.phase(phase_type="competition")
        locale = get_language()[-2:]
        competition_phase_interval_date = babel.dates.format_interval(
            start=competition_phase.date_from,
            end=competition_phase.date_to,
            locale=locale,
            skeleton="yMd",
        )
        registration_phase_start_date = babel.dates.format_date(
            date=registration_phase.date_from,
            locale=locale,
            format="medium",
        )
        value = getattr(self, f"description_{locale}")
        if value is None:
            return ""
        value = value.replace(
            "<YEAR>",
            f"{competition_phase.date_from.year}",
        )
        value = value.replace(
            "<COMPETITION_PHASE_INTERVAL_DATE>",
            competition_phase_interval_date,
        )
        value = value.replace(
            "<REGISTRATION_PHASE_START_DATE>",
            registration_phase_start_date,
        )
        return value
