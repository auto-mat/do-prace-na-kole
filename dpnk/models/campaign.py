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

from cache_utils.decorators import cached

from denorm import denormalized, depend_on_related

from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Max
from django.utils.translation import ugettext_lazy as _

from price_level.models import Pricable

from smmapdfs.models import PdfSandwichType

from .phase import Phase
from .user_attendance import UserAttendance
from .. import util


class Campaign(Pricable, models.Model):
    """kampaň"""

    class Meta:
        verbose_name = _(u"kampaň")
        verbose_name_plural = _(u"kampaně")
        permissions = (
            ("can_see_application_links", "Can see application links"),
        )
        ordering = ('-id', )

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
    slug_identifier = models.SlugField(
        unique=True,
        verbose_name="Identifikátor kampaně",
        blank=True,
        null=True,
    )
    previous_campaign = models.ForeignKey(
        'Campaign',
        verbose_name=_(u"Předchozí kampaň"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
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
    show_application_links = models.BooleanField(
        verbose_name=_("Ukázat odkazy na aplikace"),
        default=False,
        null=False,
    )
    mailing_list_enabled = models.NullBooleanField(
        verbose_name=_(u"Povolit mailing list"),
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
    club_membership_integration = models.BooleanField(
        verbose_name=_("Povolit integraci s klubem přátel?"),
        default=True,
    )
    track_required = models.BooleanField(
        verbose_name=_("Je povinné zadávat trasu"),
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
    web = models.URLField(
        verbose_name=_("Web kampáně"),
        default="http://www.dopracenakole.cz",
        blank=True,
    )
    contact_email = models.CharField(
        verbose_name=_("Kontaktní e-mail"),
        default="kontakt@dopracenakole.cz",
        max_length=80,
        blank=False,
    )
    sitetree_postfix = models.CharField(
        verbose_name=_("Postfix pro menu"),
        max_length=60,
        null=False,
        blank=True,
        default="",
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

    sandwich_type = models.ForeignKey(
        PdfSandwichType,
        null=True,
        blank=True,
        default='',
        on_delete=models.SET_NULL,
    )
    team_diploma_sandwich_type = models.ForeignKey(
        PdfSandwichType,
        related_name='team_diploma_campaign',
        null=True,
        blank=True,
        default='',
        on_delete=models.SET_NULL,
    )

    def sitetree_postfix_maintree(self):
        if self.sitetree_postfix:
            return "maintree_%s" % self.sitetree_postfix
        else:
            return "maintree"

    def __str__(self):
        return self.name

    def competitors_choose_team(self):
        return self.max_team_members > 1

    def too_much_members(self, member_count):
        if self.max_team_members is None:
            return False
        return member_count > self.max_team_members

    def day_active(self, day):
        """ Return if this day can be changed by user """
        day_today = util.today()
        try:
            entry_phase = self.phase('entry_enabled')
            if not entry_phase.is_actual():
                return False
        except Phase.DoesNotExist:
            pass
        return (
            (day <= day_today) and
            (day > day_today - datetime.timedelta(days=self.days_active))
        )

    def vacation_day_active(self, day):
        """ Return if this day can be added as vacation """
        day_today = util.today()
        last_day = self.competition_phase().date_to
        return (
            (day <= last_day) and
            (day > day_today)
        )

    def possible_vacation_days(self):
        """ Return days, that can be added as vacation """
        competition_phase = self.competition_phase()
        return [d for d in util.daterange(competition_phase.date_from, competition_phase.date_to) if self.vacation_day_active(d)]

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

    def get_directions(self):
        if self.recreational:
            return ('trip_to', 'trip_from', 'recreational')
        else:
            return ('trip_to', 'trip_from')

    @denormalized(models.BooleanField, default=True)
    @depend_on_related('t_shirt_delivery.TShirtSize', type='backward', foreign_key='campaign')
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
            raise Phase.DoesNotExist
        return result

    def competition_phase(self):
        return self.phase('competition')
