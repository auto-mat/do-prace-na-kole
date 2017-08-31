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

from denorm import denormalized, depend_on_related

from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Max
from django.utils.translation import ugettext_lazy as _

from price_level.models import Pricable

from .user_attendance import UserAttendance


class Campaign(Pricable, models.Model):
    """kampaň"""

    class Meta:
        verbose_name = _(u"kampaň")
        verbose_name_plural = _(u"kampaně")

    name = models.CharField(
        unique=True,
        verbose_name=_(u"Jméno kampaně"),
        max_length=60,
        null=False,
    )
    slug = models.SlugField(
        unique=True,
        verbose_name=u"Doména v URL",
        blank=False,
    )
    previous_campaign = models.ForeignKey(
        'Campaign',
        verbose_name=_(u"Předchozí kampaň"),
        null=True,
        blank=True,
    )
    email_footer = models.TextField(
        verbose_name=_(u"Patička uživatelských e-mailů"),
        default="",
        max_length=5000,
        null=True,
        blank=True,
    )
    mailing_list_id = models.CharField(
        verbose_name=_(u"ID mailing listu"),
        max_length=60,
        default="",
        blank=True,
        null=False,
    )
    mailing_list_enabled = models.BooleanField(
        verbose_name=_(u"Povolit mailing list"),
        default=False,
        null=False,
    )
    days_active = models.PositiveIntegerField(
        verbose_name=_("Počet minulých dní, které jdou zapisovat"),
        default=7,
        blank=False,
        null=False,
    )
    minimum_rides_base = models.PositiveIntegerField(
        verbose_name=_(u"Minimální základ počtu jízd"),
        help_text=_(u"Minimální počet jízd, které je nutné si zapsat, aby bylo možné dosáhnout 100% jízd"),
        default=25,
        blank=False,
        null=False,
    )
    minimum_percentage = models.PositiveIntegerField(
        verbose_name=_(u"Minimální procento pro kvalifikaci do pravidelnostní soutěže"),
        default=66,
        blank=False,
        null=False,
    )
    trip_plus_distance = models.PositiveIntegerField(
        verbose_name=_(u"Maximální navýšení vzdálenosti"),
        help_text=_(u"Počet kilometrů, o které je možné prodloužit si jednu jízdu"),
        default=5,
        blank=True,
        null=True,
    )
    tracking_number_first = models.PositiveIntegerField(
        verbose_name=_(u"První číslo řady pro doručování balíčků"),
        default=0,
        blank=False,
        null=False,
    )
    tracking_number_last = models.PositiveIntegerField(
        verbose_name=_(u"Poslední číslo řady pro doručování balíčků"),
        default=999999999,
        blank=False,
        null=False,
    )
    package_height = models.PositiveIntegerField(
        verbose_name=_(u"Výška balíku"),
        default=1,
        blank=True,
        null=True,
    )
    package_width = models.PositiveIntegerField(
        verbose_name=_(u"Šířka balíku"),
        default=26,
        blank=True,
        null=True,
    )
    package_depth = models.PositiveIntegerField(
        verbose_name=_(u"Hloubka balíku"),
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
        verbose_name=_(u"Váha balíku"),
        null=True,
        blank=True,
        default=0.25,
        validators=[
            MaxValueValidator(1000),
            MinValueValidator(0),
        ],
    )
    invoice_sequence_number_first = models.PositiveIntegerField(
        verbose_name=_(u"První číslo řady pro faktury"),
        default=1,
        blank=False,
        null=False,
    )
    invoice_sequence_number_last = models.PositiveIntegerField(
        verbose_name=_(u"Poslední číslo řady pro faktury"),
        default=999999999,
        blank=False,
        null=False,
    )
    benefitial_admission_fee = models.FloatField(
        verbose_name=_(u"Benefiční startovné"),
        null=False,
        default=0,
    )
    benefitial_admission_fee_company = models.FloatField(
        verbose_name=_(u"Benefiční startovné pro organizace"),
        null=False,
        default=0,
    )
    free_entry_cases_html = models.TextField(
        verbose_name=_(u"Případy, kdy je startovné zdarma"),
        null=True,
        blank=True,
    )
    track_required = models.BooleanField(
        verbose_name=_("Je povinné zadávat trasu"),
        default=True,
        null=False,
    )
    wp_api_url = models.URLField(
        default="http://www.dopracenakole.cz",
        verbose_name=_("Adresa pro Wordpress API se články"),
        null=True,
        blank=True,
    )
    wp_api_date_from = models.DateField(
        verbose_name=_("Datum, od kterého se zobrazují příspěvky z Wordpress API se články"),
        null=True,
        blank=True,
    )

    LANGUAGE_PREFIXES = [
        ('dpnk', _("Do práce na kole")),
        ('dsnk', _("Do školy na kole")),
    ]
    language_prefixes = models.CharField(
        verbose_name=_("Jazyková sada"),
        choices=LANGUAGE_PREFIXES,
        max_length=16,
        null=False,
        blank=False,
        default='dpnk',
    )
    max_team_members = models.PositiveIntegerField(
        verbose_name=_("Počet lidí v týmu"),
        default=5,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name

    def competitors_choose_team(self):
        return self.max_team_members > 1

    def too_much_members(self, member_count):
        if self.max_team_members is None:
            return False
        return member_count > self.max_team_members

    def user_attendances_for_delivery(self):
        from t_shirt_delivery.models import PackageTransaction
        return UserAttendance.objects.filter(
            campaign=self,
            payment_status__in=('done', 'no_admission'),
            t_shirt_size__ship=True,
        ).exclude(
            transactions__packagetransaction__status__in=PackageTransaction.shipped_statuses,
        ).exclude(
            team=None,
        ).annotate(
            payment_created=Max('transactions__payment__created'),
        ).order_by(
            'payment_created',
        ).distinct()

    @depend_on_related('TShirtSize', foreign_key='tshirtsize_set')
    @denormalized(models.BooleanField, default=True)
    def has_any_tshirt(self):
        return self.tshirtsize_set.exists()

    @cached(60)
    def phase(self, phase_type):
        """
        Return phase of given type from this campaign.
        @phase_type Type of phase.
        """
        return self.phase_set.get(phase_type=phase_type)

    @cached(60)
    def competition_phase(self):
        return self.phase('competition')
