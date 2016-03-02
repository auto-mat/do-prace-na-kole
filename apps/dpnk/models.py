# -*- coding: utf-8 -*-

# Author: Hynek Hanke <hynek.hanke@auto-mat.cz>
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2012 o.s. Auto*Mat
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

"""Modely pro Do práce na kole"""

# Django imports
import random
import string
from . import parcel_batch
from . import avfull
from unidecode import unidecode
from author.decorators import with_author
from django import forms
from django.db.models import Q, Max
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.db.models.signals import post_save, pre_save, post_delete, pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from composite_field import CompositeField
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.files.temp import NamedTemporaryFile
from django.core.files import File
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.conf import settings
from polymorphic.models import PolymorphicModel
from denorm import denormalized, depend_on_related
from django.db import transaction
from modulus11 import mod11
from bulk_update.manager import BulkUpdateManager
from redactor.widgets import RedactorEditor
# Python library imports
import datetime
# Local imports
from . import util
from django_gpxpy import gpx_parse
from . import mailing
from dpnk.email import (
    payment_confirmation_mail, company_admin_rejected_mail,
    company_admin_approval_mail, payment_confirmation_company_mail)
from dpnk import invoice_pdf
import logging
logger = logging.getLogger(__name__)


def get_address_string(address):
    return ", ".join(filter(lambda x: x != "", [address.recipient, "%s %s" % (address.street, address.street_number), "%s %s" % (util.format_psc(address.psc), address.city)]))


class Address(CompositeField):
    street = models.CharField(
        verbose_name=_(u"Ulice"),
        help_text=_(u"Např. „Šeříková“ nebo „Nám. W. Churchilla“"),
        default="",
        max_length=50,
        null=False,
    )
    street_number = models.CharField(
        verbose_name=_(u"Číslo domu"),
        help_text=_(u"Např. „2965/12“ nebo „156“"),
        default="",
        max_length=10,
        null=False,
        blank=False,
    )
    recipient = models.CharField(
        verbose_name=_(u"Název pobočky (celé společnosti, závodu, kanceláře, fakulty) na adrese"),
        help_text=_(u"Např. „odštěpný závod Brno“, „oblastní pobočka Liberec“, „Přírodovědecká fakulta“ atp."),
        default="",
        max_length=50,
        null=True,
        blank=True,
    )
    district = models.CharField(
        verbose_name=_(u"Městská část"),
        default="",
        max_length=50,
        null=True,
        blank=True,
    )
    psc = models.IntegerField(
        verbose_name=_(u"PSČ"),
        help_text=_(u"Např.: „130 00“"),
        validators=[
            MaxValueValidator(99999),
            MinValueValidator(10000)
        ],
        default=None,
        null=True,
        blank=False,
    )
    city = models.CharField(
        verbose_name=_(u"Město"),
        help_text=_(u"Např. „Jablonec n. N.“ nebo „Praha 3, Žižkov“"),
        default="",
        max_length=50,
        null=False,
        blank=False,
    )

    def __str__(self):
        return get_address_string(self)


class City(models.Model):
    """Město"""

    class Meta:
        verbose_name = _(u"Město")
        verbose_name_plural = _(u"Města")
        ordering = ('name',)

    name = models.CharField(
        verbose_name=_(u"Jméno"),
        unique=True,
        max_length=40,
        null=False)
    slug = models.SlugField(
        unique=True,
        verbose_name=u"Subdoména v URL",
        blank=False
    )
    cyklistesobe_slug = models.CharField(
        verbose_name=_(u"Jméno skupiny na webu Cyklisté sobě"),
        max_length=40,
        null=True)
    location = models.PointField(
        verbose_name=_(u"poloha města"),
        srid=4326,
        null=True,
        blank=False,
    )

    def __str__(self):
        return "%s" % self.name


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
        related_name="cityincampaign")
    campaign = models.ForeignKey(
        "Campaign",
        null=False,
        blank=False)
    allow_adding_rides = models.BooleanField(
        verbose_name=_(u"povolit zapisování jízd"),
        null=False,
        blank=False,
        default=True,
    )

    def __str__(self):
        return "%(city)s (%(campaign)s)" % {'campaign': self.campaign.name, 'city': self.city.name}


class Company(models.Model):
    """Firma"""

    class Meta:
        verbose_name = _(u"Firma")
        verbose_name_plural = _(u"Firmy")
        ordering = ('name',)

    name = models.CharField(
        unique=True,
        verbose_name=_(u"Název společnosti"),
        help_text=_(u"Např. „Výrobna, a.s.“, „Příspěvková, p.o.“, „Nevládka, z.s.“, „Univerzita Karlova“"),
        max_length=60, null=False)
    address = Address()
    ico = models.PositiveIntegerField(
        default=None,
        verbose_name=_(u"IČO"),
        null=True,
        blank=False,
    )
    dic = models.CharField(
        verbose_name=_(u"DIČ"),
        max_length=10,
        default="",
        null=True,
        blank=True,
    )
    active = models.BooleanField(
        verbose_name=_(u"Aktivní"),
        default=True,
        null=False)

    def has_filled_contact_information(self):
        address_complete = self.address.street and self.address.street_number and self.address.psc and self.address.city
        return self.name and address_complete and self.ico

    def __str__(self):
        return "%s" % self.name

    def company_address(self):
        return get_address_string(self.address)


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super(ActiveManager, self).get_queryset().filter(active=True)


class Subsidiary(models.Model):
    """Pobočka"""

    class Meta:
        verbose_name = _(u"Pobočka firmy")
        verbose_name_plural = _(u"Pobočky firem")

    address = Address()
    company = models.ForeignKey(
        Company,
        related_name="subsidiaries",
        null=False,
        blank=False)
    city = models.ForeignKey(
        City,
        verbose_name=_(u"Spádové město"),
        help_text=_(u"Rozhoduje o tom, do soutěží jakého města budete zařazeni a kde budete dostávat ceny - vizte <a href='%s' target='_blank'>pravidla soutěže</a>") %
        "http://www.dopracenakole.cz/pravidla",
        null=False,
        blank=False)
    active = models.BooleanField(
        verbose_name=_(u"Aktivní"),
        default=True,
        null=False)

    active_objects = ActiveManager()
    objects = models.Manager()

    def __str__(self):
        return get_address_string(self.address)

    def name(self):
        return get_address_string(self.address)


def validate_length(value, min_length=25):
    str_len = len(str(value))
    if str_len < min_length:
        raise ValidationError(_(u"Řetězec by neměl být kratší než %(min)s znaků a delší než %(max)s znaků") % {'min': min_length, 'max': str_len})


class Team(models.Model):
    """Profil týmu"""

    class Meta:
        verbose_name = _(u"Tým")
        verbose_name_plural = _(u"Týmy")
        ordering = ('name',)
        unique_together = (("name", "campaign"),)

    name = models.CharField(
        verbose_name=_(u"Název týmu"),
        max_length=50, null=False,
        unique=False)
    subsidiary = models.ForeignKey(
        Subsidiary,
        verbose_name=_(u"Pobočka"),
        related_name='teams',
        null=False,
        blank=False)
    invitation_token = models.CharField(
        verbose_name=_(u"Token pro pozvánky"),
        default="",
        max_length=100,
        null=False,
        blank=False,
        unique=True,
        validators=[validate_length],
    )
    campaign = models.ForeignKey(
        "Campaign",
        verbose_name=_(u"Kampaň"),
        null=False,
        blank=False)

    @denormalized(
        models.IntegerField,
        verbose_name=_(u"Počet právoplatných členů týmu"),
        null=True,
        blank=False,
        db_index=True,
        default=None,
        skip={'invitation_token'})
    @depend_on_related('UserAttendance')
    def member_count(self):
        member_count = self.members().count()
        if member_count > settings.MAX_TEAM_MEMBERS:
            logger.error(u"Too many members in team %s" % self)
        return member_count

    def unapproved_members(self):
        return UserAttendance.objects.filter(campaign=self.campaign, team=self, userprofile__user__is_active=True, approved_for_team='undecided')

    def all_members(self):
        return UserAttendance.objects.filter(campaign=self.campaign, team=self, userprofile__user__is_active=True)

    def members(self):
        return self.users.filter(approved_for_team='approved', userprofile__user__is_active=True)

    @denormalized(models.IntegerField, null=True, skip={'invitation_token'})
    @depend_on_related('UserAttendance', skip={'created', 'updated'})
    def get_rides_count_denorm(self):
        rides_count = 0
        for member in self.members():
            rides_count += member.get_rides_count()
        return rides_count

    def get_frequency(self):
        return results.get_team_frequency(self.members())

    def get_length(self):
        return results.get_team_length(self)

    @denormalized(models.TextField, null=True, skip={'invitation_token'})
    @depend_on_related('UserAttendance', skip={'created', 'updated'})
    def name_with_members(self):
        return u"%s (%s)" % (self.name, u", ".join([u.userprofile.name() for u in self.members()]))

    def __str__(self):
        return "%s" % self.name_with_members

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self.invitation_token == "":
            while True:
                invitation_token = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(30))
                if not Team.objects.filter(invitation_token=invitation_token).exists():
                    self.invitation_token = invitation_token
                    break

        super(Team, self).save(force_insert, force_update, *args, **kwargs)


class TeamName(Team):
    class Meta:
        proxy = True

    def __str__(self):
        return self.name


class Campaign(models.Model):
    """kampaň"""

    class Meta:
        verbose_name = _(u"kampaň")
        verbose_name_plural = _(u"kampaně")

    name = models.CharField(
        unique=True,
        verbose_name=_(u"Jméno kampaně"),
        max_length=60,
        null=False)
    slug = models.SlugField(
        unique=True,
        default="",
        verbose_name=u"Doména v URL",
        blank=False
    )
    previous_campaign = models.ForeignKey(
        'Campaign',
        verbose_name=_(u"Předchozí kampaň"),
        null=True,
        blank=True)
    email_footer = models.TextField(
        verbose_name=_(u"Patička uživatelských emailů"),
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
        null=False)
    mailing_list_enabled = models.BooleanField(
        verbose_name=_(u"Povolit mailing list"),
        default=False,
        null=False)
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
    package_weight = models.FloatField(
        verbose_name=_(u"Váha balíku"),
        null=True,
        blank=True,
        default=0.25,
        validators=[
            MaxValueValidator(1000),
            MinValueValidator(0)
        ],
    )
    invoice_sequence_number_first = models.PositiveIntegerField(
        verbose_name=_(u"První číslo řady pro faktury"),
        default=0,
        blank=False,
        null=False,
    )
    invoice_sequence_number_last = models.PositiveIntegerField(
        verbose_name=_(u"Poslední číslo řady pro faktury"),
        default=999999999,
        blank=False,
        null=False,
    )
    admission_fee = models.FloatField(
        verbose_name=_(u"Včasné startovné"),
        null=False,
        default=0)
    admission_fee_company = models.FloatField(
        verbose_name=_(u"Včasné startovné pro firmy"),
        null=False,
        default=0)
    late_admission_fee = models.FloatField(
        verbose_name=_(u"Pozdní startovné"),
        null=False,
        default=0)
    late_admission_fee_company = models.FloatField(
        verbose_name=_(u"Pozdní startovné pro firmy"),
        null=False,
        default=0)
    benefitial_admission_fee = models.FloatField(
        verbose_name=_(u"Benefiční startovné"),
        null=False,
        default=0)
    benefitial_admission_fee_company = models.FloatField(
        verbose_name=_(u"Benefiční startovné pro firmy"),
        null=False,
        default=0)
    free_entry_cases_html = models.TextField(
        verbose_name=_(u"Případy, kdy je startovné zdarma"),
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name

    @denormalized(models.NullBooleanField, default=None)
    @depend_on_related('Phase')
    def late_admission_phase(self):
        late_admission_phase = self.phase("late_admission")
        return not late_admission_phase or late_admission_phase.is_actual()

    def user_attendances_for_delivery(self):
        return UserAttendance.objects.filter(
            campaign=self,
            transactions__payment__status__in=Payment.done_statuses,
            t_shirt_size__ship=True,
        ).exclude(transactions__packagetransaction__status__in=PackageTransaction.shipped_statuses).\
            exclude(team=None).\
            annotate(payment_created=Max('transactions__payment__created')).\
            order_by('payment_created').\
            distinct()

    def phase(self, phase_type):
        try:
            return self.phase_set.get(type=phase_type)
        except Phase.DoesNotExist:
            return None


def get_team_in_campaign_manager(campaign_slug):
    class TeamInCampaignManager(models.Manager):
        def get_queryset(self):
            return super(TeamInCampaignManager, self).get_queryset().filter(campaign__slug=campaign_slug)

    class TeamInCampaign(Team):
        objects = TeamInCampaignManager()

        class Meta:
            proxy = True

    return TeamInCampaign


class Phase(models.Model):
    """fáze kampaně"""

    class Meta:
        verbose_name = _(u"fáze kampaně")
        verbose_name_plural = _(u"fáze kampaně")
        unique_together = (("type", "campaign"),)

    TYPE = [('registration', _(u"registrační")),
            ('late_admission', _(u"pozdní startovné")),
            ('compet_entry', _(u"vstup do soutěže (zastaralé)")),
            ('payment', _(u"placení startovného")),
            ('competition', _(u"soutěžní")),
            ('results', _(u"výsledková")),
            ('admissions', _(u"přihlašovací do soutěží")),
            ('invoices', _(u"vytváření faktur")),
            ]

    TYPE_DICT = dict(TYPE)

    campaign = models.ForeignKey(
        Campaign,
        verbose_name=_(u"Kampaň"),
        null=False,
        blank=False)
    type = models.CharField(
        verbose_name=_(u"Typ fáze"),
        choices=TYPE,
        max_length=16,
        null=False,
        default='registration')
    date_from = models.DateField(
        verbose_name=_(u"Datum začátku fáze"),
        default=None,
        null=True, blank=True)
    date_to = models.DateField(
        verbose_name=_(u"Datum konce fáze"),
        default=None,
        null=True, blank=True)

    def has_started(self):
        if not self.date_from:
            return True
        return self.date_from <= util.today()

    def has_finished(self):
        if not self.date_to:
            return False
        return not self.date_to >= util.today()

    def is_actual(self):
        return self.has_started() and not self.has_finished()


class TShirtSize(models.Model):
    """Velikost trička"""

    name = models.CharField(
        verbose_name=_(u"Velikost trička"),
        max_length=40, null=False)
    campaign = models.ForeignKey(
        Campaign,
        verbose_name=_(u"Kampaň"),
        null=False,
        blank=False)
    order = models.PositiveIntegerField(
        default=0,
        blank=False,
        null=False,
    )
    ship = models.BooleanField(
        verbose_name=_(u"Posílá se?"),
        default=True,
        null=False)
    available = models.BooleanField(
        verbose_name=_(u"Je dostupné?"),
        help_text=_(u"Zobrazuje se v nabídce trik"),
        default=True,
        null=False)
    t_shirt_preview = models.FileField(
        verbose_name=_(u"Náhled trika"),
        upload_to=u't_shirt_preview',
        blank=True, null=True)
    price = models.IntegerField(
        verbose_name=_(u"Cena"),
        default=0,
        blank=False,
        null=False,
    )

    class Meta:
        verbose_name = _(u"Velikost trička")
        verbose_name_plural = _(u"Velikosti trička")
        unique_together = (("name", "campaign"),)
        ordering = ["order"]

    def __str__(self):
        if self.price == 0:
            return self.name
        else:
            return "%s (%s Kč navíc)" % (self.name, self.price)


class UserAttendanceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserAttendanceForm, self).__init__(*args, **kwargs)
        self.fields['t_shirt_size'].queryset = TShirtSize.objects.filter(campaign=self.instance.campaign, available=True)


class UserAttendance(models.Model):
    """Účast uživatele v kampani"""

    class Meta:
        verbose_name = _(u"Účastník kampaně")
        verbose_name_plural = _(u"Účastníci kampaně")
        unique_together = (("userprofile", "campaign"),)

    TEAMAPPROVAL = (
        ('approved', _(u"Odsouhlasený")),
        ('undecided', _(u"Nerozhodnuto")),
        ('denied', _(u"Zamítnutý")),
    )

    campaign = models.ForeignKey(
        Campaign,
        verbose_name=_(u"Kampaň"),
        null=False,
        blank=False)
    userprofile = models.ForeignKey(
        "UserProfile",
        verbose_name=_(u"Uživatelský profil"),
        related_name="userattendance_set",
        unique=False,
        null=False,
        blank=False)
    distance = models.FloatField(
        verbose_name=_(u"Vzdálenost"),
        help_text=_(u"Průměrná ujetá vzdálenost z domova do práce (v km v jednom směru)"),
        default=None,
        blank=True,
        null=True)
    track = models.MultiLineStringField(
        verbose_name=_(u"trasa"),
        help_text=_(u"""
<ul>
   <li><strong>Zadávání trasy zahájíte kliknutím na tlačítko "Nakreslit trasu".</strong></li>
   <li>Změnu trasy provedete po přepnutí do režimu úprav kliknutím na trasu.</li>
   <li>Trasu stačí zadat tak, že bude zřejmé, kterými ulicemi vede.</li>
   <li>Zadání přesnějšího průběhu nám však může pomoci lépe zjistit jak se lidé na kole pohybují.</li>
   <li>Trasu bude možné změnit nebo upřesnit i později v průběhu soutěže.</li>
   <li>Polohu začátku a konce trasy stačí zadávat s přesností 100m.</li>
</ul>
Trasa slouží k výpočtu vzdálenosti a pomůže nám lépe určit potřeby lidí pohybuících se ve městě na kole. Vaše cesta se zobrazí vašim týmovým kolegům.
<br/>Trasy všech účastníků budou v anonymizované podobě zobrazené na úvodní stránce.
"""),
        srid=4326,
        null=True,
        blank=True,
        geography=True,
    )
    dont_want_insert_track = models.BooleanField(
        verbose_name=_(u"Nepřeji si zadávat svoji trasu."),
        default=False,
        null=False)
    objects = models.GeoManager()
    team = models.ForeignKey(
        Team,
        related_name='users',
        verbose_name=_(u"Tým"),
        null=True,
        blank=True,
        default=None)
    approved_for_team = models.CharField(
        verbose_name=_(u"Souhlas týmu"),
        choices=TEAMAPPROVAL,
        max_length=16,
        null=False,
        default='undecided')
    t_shirt_size = models.ForeignKey(
        TShirtSize,
        verbose_name=_(u"Velikost trička"),
        null=True,
        blank=True,
    )
    created = models.DateTimeField(
        verbose_name=_(u"Datum vytvoření"),
        auto_now_add=True,
        null=True,
    )
    updated = models.DateTimeField(
        verbose_name=_(u"Datum poslední změny"),
        auto_now=True,
        null=True,
    )

    def payments(self):
        return self.transactions.instance_of(Payment)

    def first_name(self):
        return self.userprofile.user.first_name

    def last_name(self):
        return self.userprofile.user.last_name

    def name(self):
        return self.userprofile.name()
    name.admin_order_field = 'userprofile__user__last_name'
    name.short_description = _(u"Jméno")

    def name_for_trusted(self):
        return self.userprofile.name_for_trusted()
    name_for_trusted.admin_order_field = 'userprofile__user__last_name'
    name_for_trusted.short_description = _(u"Jméno")

    def __str__(self):
        return self.userprofile.name()

    def admission_fee(self):
        if self.t_shirt_size:
            t_shirt_price = self.t_shirt_size.price
        else:
            t_shirt_price = 0
        if self.campaign.late_admission_phase:
            return self.campaign.late_admission_fee + t_shirt_price
        else:
            return self.campaign.admission_fee + t_shirt_price

    def beneficiary_admission_fee(self):
        if self.t_shirt_size:
            t_shirt_price = self.t_shirt_size.price
        else:
            t_shirt_price = 0
        return self.campaign.benefitial_admission_fee + t_shirt_price

    def company_admission_fee(self):
        if self.campaign.late_admission_phase:
            return self.campaign.late_admission_fee_company + self.t_shirt_size.price
        else:
            return self.campaign.admission_fee_company + self.t_shirt_size.price

    @denormalized(models.ForeignKey, to='Payment', null=True, on_delete=models.SET_NULL, skip={'updated', 'created'})
    @depend_on_related('Transaction', foreign_key='user_attendance')
    def representative_payment(self):
        if self.team and self.team.subsidiary and self.admission_fee() == 0:
            return None

        try:
            return self.payments().filter(status__in=Payment.done_statuses).latest('id')
        except Transaction.DoesNotExist:
            pass

        try:
            return self.payments().filter(status__in=Payment.waiting_statuses).latest('id')
        except Transaction.DoesNotExist:
            pass

        try:
            return self.payments().latest('id')
        except Transaction.DoesNotExist:
            pass

        return None

    PAYMENT_CHOICES = (
        ('no_admission', _(u'neplatí se')),
        ('none', _(u'žádné platby')),
        ('done', _(u'zaplaceno')),
        ('waiting', _(u'nepotvrzeno')),
        ('unknown', _(u'neznámý')),
    )

    @denormalized(models.CharField, choices=PAYMENT_CHOICES, max_length=20, null=True, skip={'updated', 'created'})
    @depend_on_related('Transaction', foreign_key='user_attendance')
    def payment_status(self):
        if self.team and self.team.subsidiary and self.admission_fee() == 0:
            return 'no_admission'
        payment = self.representative_payment
        if not payment:
            return 'none'
        if payment.status in Payment.done_statuses:
            return 'done'
        if payment.status in Payment.waiting_statuses:
            return 'waiting'
        return 'unknown'

    def payment_class(self):
        payment_classes = {
            'no_admission': 'success',
            'none': 'error',
            'done': 'success',
            'waiting': 'warning',
            'unknown': 'warning',
        }
        return payment_classes[self.payment_status]

    def payment_type_string(self):
        if self.representative_payment:
            return Payment.PAY_TYPES_DICT[self.representative_payment.pay_type].upper()

    def get_competitions(self):
        return results.get_competitions_with_info(self)

    def get_competitions_without_admission(self):
        return results.get_competitions_without_admission(self)

    def has_distance_competition(self):
        return results.has_distance_competition(self)

    def get_rides_count(self):
        return results.get_rides_count(self)

    @denormalized(models.IntegerField, null=True, skip={'updated', 'created'})
    @depend_on_related('Trip')
    @depend_on_related('Campaign')
    def get_rides_count_denorm(self):
        return results.get_rides_count(self)

    def get_frequency(self, day=None):
        return results.get_userprofile_frequency(self, day)

    @denormalized(models.FloatField, null=True, skip={'updated', 'created'})
    @depend_on_related('Trip')
    @depend_on_related('Campaign')
    def frequency(self):
        return self.get_frequency()

    def get_frequency_percentage(self, day=None):
        if day:
            return self.get_frequency(day) * 100
        else:
            return self.frequency * 100

    @denormalized(models.FloatField, null=True, skip={'updated', 'created'})
    @depend_on_related('Trip')
    @depend_on_related('Campaign')
    def trip_length_total(self):
        return results.get_userprofile_length(self)

    def get_nonreduced_length(self):
        return results.get_userprofile_nonreduced_length(self)

    def get_distance(self, round_digits=2):
        if self.track:
            length = UserAttendance.objects.length().get(id=self.id).length
            if not length:
                logger.error("length not available for user %s" % self)
                return 0
            return round(length.km, round_digits)
        else:
            return self.distance

    def get_userprofile(self):
        return self.userprofile

    def is_libero(self):
        if self.team:
            return self.team.members().count() <= 1
        else:
            return False

    def package_shipped(self):
        return self.transactions.filter(instance_of=PackageTransaction, status__in=PackageTransaction.shipped_statuses).last()

    def package_delivered(self):
        return self.transactions.filter(instance_of=PackageTransaction, status=PackageTransaction.Status.PACKAGE_DELIVERY_CONFIRMED).last()

    def other_user_attendances(self, campaign):
        return self.userprofile.userattendance_set.exclude(campaign=campaign)

    def undenied_team_member_count(self):
        team = self.team
        return UserAttendance.objects.filter(team=team, userprofile__user__is_active=True).exclude(approved_for_team='denied').count()

    def can_enter_competition(self):
        if not self.distance:
            return 'no_personal_data'
        elif not self.team:
            return 'no_team'
        elif not self.approved_for_team == 'approved':
            return 'not_approved_for_team'
        elif not self.t_shirt_size:
            return 'not_t_shirt'
        elif self.team.unapproved_members().count() > 0:
            return 'unapproved_team_members'
        elif self.team.members().count() < 2:
            return 'not_enough_team_members'
        elif self.payment()['status'] != 'done':
            return 'not_paid'
        else:
            return True

    def company(self):
        if self.team:
            try:
                return self.team.subsidiary.company
            except UserProfile.DoesNotExist:
                pass

        try:
            return self.userprofile.user.company_admin.get(campaign=self.campaign).administrated_company
        except CompanyAdmin.DoesNotExist:
            return None

    def entered_competition(self):
        return self.tshirt_complete() and\
            self.team_complete() and\
            self.payment_complete() and\
            self.userprofile.profile_complete()

    def team_member_count(self):
        if self.team:
            return self.team.member_count

    def tshirt_complete(self):
        return self.t_shirt_size

    def track_complete(self):
        return self.track or self.distance

    def team_complete(self):
        return self.team

    def payment_complete(self):
        return self.payments().exists()

    def get_emissions(self, distance=None):
        return util.get_emissions(self.get_nonreduced_length())

    def get_active_trips(self):
        days = util.days_active(self.campaign)
        return self.get_trips(days)

    def get_all_trips(self):
        days = util.days(self.campaign)
        return self.get_trips(days)

    def get_trips(self, days):
        """
        Return trips in given days, return days without any trip
        @param days
        @return trips in those days
        @return days without trip
        """
        trips = Trip.objects.filter(user_attendance=self, date__in=days)
        trip_days = trips.values_list('date', 'direction')
        expected_trip_days = [(day, direction) for day in days for direction in ('trip_from', 'trip_to')]
        uncreated_trips = sorted(list(set(expected_trip_days) - set(trip_days)))
        return trips, uncreated_trips

    @denormalized(models.ForeignKey, to='CompanyAdmin', null=True, on_delete=models.SET_NULL, skip={'updated', 'created'})
    def related_company_admin(self):
        try:
            ca = CompanyAdmin.objects.get(user=self.userprofile.user, campaign=self.campaign)
            return ca
        except CompanyAdmin.DoesNotExist:
            return None

    def unanswered_questionnaires(self):
        return results.get_competitions_without_admission(self).filter(type='questionnaire')

    @denormalized(models.NullBooleanField, default=None, skip={'created', 'updated'})
    @depend_on_related('Team')
    @depend_on_related('Competition')
    def has_unanswered_questionnaires(self):
        return self.unanswered_questionnaires().exists()

    def get_asociated_company_admin(self):
        if not self.team:
            return None
        try:
            ca = self.team.subsidiary.company.company_admin.get(campaign=self.campaign)
            if ca.company_admin_approved == 'approved':
                return ca
            else:
                return None
        except CompanyAdmin.DoesNotExist:
            return None

    def previous_user_attendance(self):
        previous_campaign = self.campaign.previous_campaign
        try:
            return self.userprofile.userattendance_set.get(campaign=previous_campaign)
        except UserAttendance.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        if self.pk is None:
            previous_user_attendance = self.previous_user_attendance()
            if previous_user_attendance:
                if previous_user_attendance.track:
                    self.distance = previous_user_attendance.distance
                    self.track = previous_user_attendance.track
                if previous_user_attendance.t_shirt_size:
                    t_shirt_size = self.campaign.tshirtsize_set.filter(name=previous_user_attendance.t_shirt_size.name)
                    if t_shirt_size.count() == 1:
                        self.t_shirt_size = t_shirt_size.first()
        return super(UserAttendance, self).save(*args, **kwargs)


class UserAttendanceRelated(UserAttendance):
    class Meta:
        proxy = True

    def __str__(self):
        return "%s - %s" % (self.userprofile.name(), self.campaign.slug)


class UserProfile(models.Model):
    """Uživatelský profil"""

    class Meta:
        verbose_name = _(u"Uživatelský profil")
        verbose_name_plural = _(u"Uživatelské profily")
        ordering = ["user__last_name", "user__first_name"]

    GENDER = (
        ('unknown', _(u'-------')),
        ('male', _(u'Muž')),
        ('female', _(u'Žena')),
    )

    LANGUAGE = [
        ('cs', _(u"Čeština")),
        ('en', _(u"Angličtna")),
    ]

    user = models.OneToOneField(
        User,
        related_name='userprofile',
        unique=True,
        null=False,
        blank=False,
    )
    nickname = models.CharField(
        _(u'Zobrazené jméno'),
        help_text=_(u'Zobrazí se ve všech veřejných výpisech místo vašeho jména. Zadávejte takové jméno, podle kterého vás vaši kolegové poznají'),
        max_length=60,
        blank=True,
        null=True,
    )
    telephone = models.CharField(
        verbose_name=_(u"Telefon"),
        max_length=30, null=False)
    language = models.CharField(
        verbose_name=_(u"Jazyk emailů"),
        help_text=_(u"Jazyk, ve kterém vám budou docházet emaily z registračního systému"),
        choices=LANGUAGE,
        max_length=16,
        null=False,
        default='cs')
    mailing_id = models.CharField(
        verbose_name=_(u"ID uživatele v mailing listu"),
        max_length=128,
        db_index=True,
        default=None,
        # TODO:
        # unique=True,
        null=True,
        blank=True
    )
    mailing_hash = models.BigIntegerField(
        verbose_name=_(u"Hash poslední synchronizace s mailingem"),
        default=None,
        null=True,
        blank=True
    )
    sex = models.CharField(
        verbose_name=_(u"Pohlaví"),
        help_text=_(u"Slouží k zařazení do výkonnostních kategorií"),
        choices=GENDER,
        default='unknown',
        max_length=50,
    )
    note = models.TextField(
        verbose_name=_(u"Interní poznámka"),
        null=True,
        blank=True,
    )
    administrated_cities = models.ManyToManyField(
        'City',
        related_name="city_admins",
        blank=True)
    mailing_opt_in = models.NullBooleanField(
        verbose_name=_(u"Přeji si dostávat emailem informace o akcích, událostech a dalších informacích souvisejících se soutěží."),
        help_text=_(u"Odběr emailů můžete kdykoliv v průběhu soutěže zrušit."),
        default=None)
    personal_data_opt_in = models.BooleanField(
        verbose_name=_(u"Souhlas se zpracováním osobních údajů."),
        blank=False,
        default=False)

    def first_name(self):
        return self.user.first_name

    def last_name(self):
        return self.user.last_name

    def name(self):
        if self.nickname:
            return self.nickname
        else:
            full_name = self.user.get_full_name()
            email = self.user.email
            if full_name:
                return full_name
            elif email:
                return email
            else:
                return self.user.username

    def name_for_trusted(self):
        if self.nickname:
            full_name = self.user.get_full_name()
            if full_name:
                return u"%s (%s)" % (full_name, self.nickname)
            else:
                return u"%s (%s)" % (self.user.username, self.nickname)
        else:
            full_name = self.user.get_full_name()
            if full_name:
                return full_name
            else:
                return self.user.username

    def __str__(self):
        return self.name()

    def competition_edition_allowed(self, competition):
        return not competition.city.exists() or not self.administrated_cities.filter(pk__in=competition.city.values_list("pk", flat=True)).exists()

    def profile_complete(self):
        return self.sex and self.first_name() and self.last_name() and self.user.email and self.personal_data_opt_in

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self.mailing_id and UserProfile.objects.exclude(pk=self.pk).filter(mailing_id=self.mailing_id).count() > 0:
            logger.error(u"Mailing id %s is already used" % self.mailing_id)
        super(UserProfile, self).save(force_insert, force_update, *args, **kwargs)


class CompanyAdmin(models.Model):
    """Profil firemního administrátora"""

    COMPANY_APPROVAL = (
        ('approved', _(u"Odsouhlasený")),
        ('undecided', _(u"Nerozhodnuto")),
        ('denied', _(u"Zamítnutý")),
    )

    class Meta:
        verbose_name = _(u"Firemní koordinátor")
        verbose_name_plural = _(u"Firemní koordinátoři")
        unique_together = (
            ("user", "campaign"),
            ("administrated_company", "campaign"),
        )

    user = models.ForeignKey(
        User,
        verbose_name=_(u"User"),
        related_name='company_admin',
        null=False,
        blank=False,
    )

    company_admin_approved = models.CharField(
        verbose_name=_(u"Správcovství organizace schváleno"),
        choices=COMPANY_APPROVAL,
        max_length=16,
        null=False,
        default='undecided')

    motivation_company_admin = models.TextField(
        verbose_name=_(u"Zaměstnanecká pozice"),
        help_text=_(u"Napište nám prosím, jakou zastáváte u Vašeho zaměstnavatele pozici"),
        default="",
        max_length=5000,
        null=True,
        blank=True,
    )

    administrated_company = models.ForeignKey(
        "Company",
        related_name="company_admin",
        verbose_name=_(u"Administrovaná společnost"),
        null=True,
        blank=False)

    campaign = models.ForeignKey(
        Campaign,
        null=False,
        blank=False)

    note = models.TextField(
        verbose_name=_(u"Interní poznámka"),
        max_length=500,
        null=True,
        blank=True,
    )

    can_confirm_payments = models.BooleanField(
        verbose_name=_(u"Může potvrzovat platby"),
        default=False,
        null=False)
    will_pay_opt_in = models.BooleanField(
        verbose_name=_(u"Souhlas s platbou za zaměstnance."),
        blank=False,
        default=False)

    def company_has_invoices(self):
        return self.administrated_company.invoice_set.filter(campaign=self.campaign).exists()

    def user_attendance(self):
        try:
            return self.user.userprofile.userattendance_set.get(campaign=self.campaign)
        except UserAttendance.DoesNotExist:
            return None

    def get_userprofile(self):
        return self.user.userprofile

    def __str__(self):
        return self.user.get_full_name()

    def save(self, *args, **kwargs):
        status_before_update = None
        if self.id:
            status_before_update = CompanyAdmin.objects.get(pk=self.id).company_admin_approved
        super(CompanyAdmin, self).save(*args, **kwargs)

        if status_before_update != self.company_admin_approved:
            if self.company_admin_approved == 'approved':
                company_admin_approval_mail(self)
            elif self.company_admin_approved == 'denied':
                company_admin_rejected_mail(self)


@with_author
class DeliveryBatch(models.Model):
    """Dávka objednávek"""

    created = models.DateTimeField(
        verbose_name=_(u"Datum vytvoření"),
        default=datetime.datetime.now,
        null=False)
    campaign = models.ForeignKey(
        Campaign,
        verbose_name=_(u"Kampaň"),
        null=False,
        blank=False)
    customer_sheets = models.FileField(
        verbose_name=_(u"Zákaznické listy"),
        upload_to=u'customer_sheets',
        blank=True, null=True)
    tnt_order = models.FileField(
        verbose_name=_(u"Objednávka pro TNT"),
        upload_to=u'tnt_order',
        blank=True, null=True)

    class Meta:
        verbose_name = _(u"Dávka objednávek")
        verbose_name_plural = _(u"Dávky objednávek")

    def __str__(self):
        return str(self.created)

    @transaction.atomic
    def add_packages(self, user_attendances=None):
        if not user_attendances:
            user_attendances = self.campaign.user_attendances_for_delivery()
        for user_attendance in user_attendances:
            pt = PackageTransaction(
                user_attendance=user_attendance,
                delivery_batch=self,
                status=PackageTransaction.Status.PACKAGE_ACCEPTED_FOR_ASSEMBLY,
            )
            pt.save()


@receiver(post_save, sender=DeliveryBatch)
def create_delivery_files(sender, instance, created, **kwargs):
    if created and getattr(instance, 'add_packages_on_save', True):
        instance.add_packages()

    if not instance.customer_sheets and getattr(instance, 'add_packages_on_save', True):
        temp = NamedTemporaryFile()
        parcel_batch.make_customer_sheets_pdf(temp, instance)
        instance.customer_sheets.save("customer_sheets_%s_%s.pdf" % (instance.pk, instance.created.strftime("%Y-%m-%d")), File(temp))
        instance.save()

    if not instance.tnt_order and getattr(instance, 'add_packages_on_save', True):
        temp = NamedTemporaryFile()
        avfull.make_avfull(temp, instance)
        instance.tnt_order.save("delivery_batch_%s_%s.txt" % (instance.pk, instance.created.strftime("%Y-%m-%d")), File(temp))
        instance.save()


@with_author
class Invoice(models.Model):
    """Faktura"""
    class Meta:
        verbose_name = _(u"Faktura")
        verbose_name_plural = _(u"Faktury")
        unique_together = (("sequence_number", "campaign"),)

    created = models.DateTimeField(
        verbose_name=_(u"Datum vytvoření"),
        default=datetime.datetime.now,
        null=False)
    exposure_date = models.DateField(
        verbose_name=_(u"Den vystavení daňového dokladu"),
        default=datetime.date.today,
        null=True,
    )
    taxable_date = models.DateField(
        verbose_name=_(u"Den uskutečnění zdanitelného plnění"),
        default=datetime.date.today,
        null=True,
    )
    paid_date = models.DateField(
        verbose_name=_(u"Datum zaplacení"),
        default=None,
        null=True,
        blank=True,
    )
    company_pais_benefitial_fee = models.BooleanField(
        verbose_name=_(u"Moje firma si přeje podpořit Auto*Mat a zaplatit benefiční startovné."),
        default=False,
    )
    total_amount = models.FloatField(
        verbose_name=_(u"Celková částka"),
        null=False,
        default=0)
    invoice_pdf = models.FileField(
        verbose_name=_(u"PDF faktury"),
        upload_to=u'invoices',
        blank=True,
        null=True,
    )
    company = models.ForeignKey(
        Company,
        verbose_name=_(u"Společnost"),
        null=False,
        blank=False,
    )
    campaign = models.ForeignKey(
        Campaign,
        verbose_name=_(u"Kampaň"),
        null=False,
        blank=False)
    sequence_number = models.PositiveIntegerField(
        verbose_name=_(u"Pořadové číslo faktury"),
        null=False)
    order_number = models.BigIntegerField(
        verbose_name=_(u"Číslo objednávky (nepovinné)"),
        null=True,
        blank=True,
    )

    def __str__(self):
        return "%s" % self.sequence_number

    def paid(self):
        if not self.paid_date:
            return False
        return self.paid_date <= util.today()

    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.sequence_number:
            campaign = self.campaign
            first = campaign.invoice_sequence_number_first
            last = campaign.invoice_sequence_number_last
            last_transaction = Invoice.objects.filter(campaign=campaign, sequence_number__gte=first, sequence_number__lte=last).order_by("sequence_number").last()
            if last_transaction:
                if last_transaction.sequence_number == last:
                    raise Exception(_(u"Došla číselná řada faktury"))
                self.sequence_number = last_transaction.sequence_number + 1
            else:
                self.sequence_number = first

            self.taxable_date = min(datetime.date.today(), self.campaign.phase("competition").date_from)
        super(Invoice, self).save(*args, **kwargs)

    def payments_to_add(self):
        if hasattr(self, 'campaign'):
            return payments_to_invoice(self.company, self.campaign)

    @transaction.atomic
    def add_payments(self):
        payments = self.payments_to_add()
        self.payment_set = payments
        for payment in payments:
            payment.status = Status.INVOICE_MADE
            payment.save()

    def clean(self):
        if not self.pk and hasattr(self, 'campaign') and not self.payments_to_add().exists():
            raise ValidationError(_(u"Neexistuje žádná nefakturovaná platba"))


def change_invoice_payments_status(sender, instance, changed_fields=None, **kwargs):
    field, (old, new) = next(iter(changed_fields.items()))
    if new is not None:
        for payment in instance.payment_set.all():
            payment.status = Status.INVOICE_PAID
            payment.save()


def payments_to_invoice(company, campaign):
    return Payment.objects.filter(pay_type='fc', status=Status.COMPANY_ACCEPTS, user_attendance__team__subsidiary__company=company, user_attendance__campaign=campaign)


@receiver(post_save, sender=Invoice)
def create_invoice_files(sender, instance, created, **kwargs):
    if created:
        instance.add_payments()

    if not instance.invoice_pdf:
        temp = NamedTemporaryFile()
        invoice_pdf.make_invoice_sheet_pdf(temp, instance)
        filename = "invoice_%s_%s_%s.pdf" % (unidecode(instance.company.name[0:40]), instance.exposure_date.strftime("%Y-%m-%d"), hash(str(instance.pk) + settings.SECRET_KEY))
        instance.invoice_pdf.save(filename, File(temp))
        instance.save()


class Status (object):
    NEW = 1
    CANCELED = 2
    REJECTED = 3
    COMMENCED = 4
    WAITING_CONFIRMATION = 5
    REJECTED = 7
    DONE = 99
    WRONG_STATUS = 888
    COMPANY_ACCEPTS = 1005
    INVOICE_MADE = 1006
    INVOICE_PAID = 1007

    PACKAGE_NEW = 20001
    PACKAGE_ACCEPTED_FOR_ASSEMBLY = 20002
    PACKAGE_ASSEMBLED = 20003
    PACKAGE_SENT = 20004
    PACKAGE_DELIVERY_CONFIRMED = 20005
    PACKAGE_DELIVERY_DENIED = 20006
    PACKAGE_RECLAIM = 20007

    BIKE_REPAIR = 40001

    COMPETITION_START_CONFIRMED = 30002

STATUS = (
    (Status.NEW, _(u'Nová')),
    (Status.CANCELED, _(u'Zrušena')),
    (Status.REJECTED, _(u'Odmítnuta')),
    (Status.COMMENCED, _(u'Zahájena')),
    (Status.WAITING_CONFIRMATION, _(u'Očekává potvrzení')),
    (Status.REJECTED, _(u'Platba zamítnuta, prostředky nemožno vrátit, řeší PayU')),
    (Status.DONE, _(u'Platba přijata')),
    (Status.WRONG_STATUS, _(u'Nesprávný status -- kontaktovat PayU')),
    (Status.COMPANY_ACCEPTS, _(u'Platba akceptována firmou')),
    (Status.INVOICE_MADE, _(u'Faktura vystavena')),
    (Status.INVOICE_PAID, _(u'Faktura zaplacena')),

    (Status.PACKAGE_NEW, 'Nový'),
    (Status.PACKAGE_ACCEPTED_FOR_ASSEMBLY, 'Přijat k sestavení'),
    (Status.PACKAGE_ASSEMBLED, 'Sestaven'),
    (Status.PACKAGE_SENT, 'Odeslán'),
    (Status.PACKAGE_DELIVERY_CONFIRMED, 'Doručení potvrzeno'),
    (Status.PACKAGE_DELIVERY_DENIED, 'Dosud nedoručeno'),
    (Status.PACKAGE_RECLAIM, 'Reklamován'),

    (Status.BIKE_REPAIR, 'Oprava v cykloservisu'),

    (Status.COMPETITION_START_CONFIRMED, 'Potvrzen vstup do soutěže'),
)


@with_author
class Transaction(PolymorphicModel):
    """Transakce"""
    status = models.PositiveIntegerField(
        verbose_name=_(u"Status"),
        default=0,
        choices=STATUS,
        null=False, blank=False)
    user_attendance = models.ForeignKey(
        UserAttendance,
        related_name="transactions",
        null=True,
        blank=False,
        default=None)
    created = models.DateTimeField(
        verbose_name=_(u"Vytvoření"),
        default=datetime.datetime.now,
        null=False)
    description = models.TextField(
        verbose_name=_(u"Popis"),
        null=True,
        blank=True,
        default="")
    realized = models.DateTimeField(
        verbose_name=_(u"Realizace"),
        null=True, blank=True)

    class Meta:
        verbose_name = _(u"Transakce")
        verbose_name_plural = _(u"Transakce")


class CommonTransaction(Transaction):
    """Obecná transakce"""

    class Meta:
        verbose_name = _(u"Obecná transakce")
        verbose_name_plural = _(u"Obecné transakce")


class CommonTransactionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CommonTransactionForm, self).__init__(*args, **kwargs)
        self.fields['status'] = forms.ChoiceField(choices=CommonTransaction.STATUS)

    class Meta:
        model = CommonTransaction
        fields = "__all__"


class UserActionTransaction(Transaction):
    """Uživatelská akce"""

    class Meta:
        verbose_name = _(u"Uživatelská akce")
        verbose_name_plural = _(u"Uživatelské akce")


class UserActionTransactionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserActionTransactionForm, self).__init__(*args, **kwargs)
        self.fields['status'] = forms.ChoiceField(choices=STATUS)

    class Meta:
        model = UserActionTransaction
        fields = "__all__"


class PackageTransaction(Transaction):
    """Transakce balíku"""

    t_shirt_size = models.ForeignKey(
        TShirtSize,
        verbose_name=_(u"Velikost trička"),
        null=True,
        blank=False,
    )
    tracking_number = models.PositiveIntegerField(
        verbose_name=_(u"Tracking number TNT"),
        unique=True,
        null=False)
    delivery_batch = models.ForeignKey(
        DeliveryBatch,
        verbose_name=_(u"Dávka objednávek"),
        null=False,
        blank=False)

    shipped_statuses = [
        Status.PACKAGE_ACCEPTED_FOR_ASSEMBLY,
        Status.PACKAGE_ASSEMBLED,
        Status.PACKAGE_SENT,
        Status.PACKAGE_DELIVERY_CONFIRMED,
        Status.PACKAGE_DELIVERY_DENIED,
    ]

    class Meta:
        verbose_name = _(u"Transakce balíku")
        verbose_name_plural = _(u"Transakce balíku")

    def tracking_number_cnc(self):
        str_tn = str(self.tracking_number)
        return str_tn + str(mod11.calc_check_digit(str_tn))

    def tnt_con_reference(self):
        batch_date = self.delivery_batch.created.strftime("%y%m%d")
        return "{:s}-{:s}-{:0>6.0f}".format(str(self.delivery_batch.pk), batch_date, self.pk)

    def tracking_link(self):
        return mark_safe(
            "<a href='http://www.tnt.com/webtracker/tracking.do?"
            "requestType=GEN&searchType=REF&respLang=cs&respCountry=cz&sourceID=1&sourceCountry=ww&cons=%(number)s&navigation=1&genericSiteIdent='>%(number)s</a>" %
            {'number': self.tnt_con_reference()}
        )

    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.t_shirt_size:
            self.t_shirt_size = self.user_attendance.t_shirt_size
        if not self.tracking_number:
            campaign = self.user_attendance.campaign
            first = campaign.tracking_number_first
            last = campaign.tracking_number_last
            last_transaction = PackageTransaction.objects.filter(tracking_number__gte=first, tracking_number__lte=last).order_by("tracking_number").last()
            if last_transaction:
                if last_transaction.tracking_number == last:
                    raise Exception(_(u"Došla číselná řada pro balíčkové transakce"))
                self.tracking_number = last_transaction.tracking_number + 1
            else:
                self.tracking_number = first
        super(PackageTransaction, self).save(*args, **kwargs)


class PackageTransactionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PackageTransactionForm, self).__init__(*args, **kwargs)
        self.fields['status'] = forms.ChoiceField(choices=STATUS)

    class Meta:
        model = PackageTransaction
        fields = "__all__"


class Payment(Transaction):
    """Platba"""

    done_statuses = [
        Status.DONE,
        Status.COMPANY_ACCEPTS,
        Status.INVOICE_MADE,
        Status.INVOICE_PAID]
    waiting_statuses = [
        Status.NEW,
        Status.COMMENCED,
        Status.WAITING_CONFIRMATION]

    PAY_TYPES = (
        ('mp', _(u'mPenize - mBank')),
        ('kb', _(u'MojePlatba')),
        ('rf', _(u'ePlatby pro eKonto')),
        ('pg', _(u'GE Money Bank')),
        ('pv', _(u'Sberbank (Volksbank)')),
        ('pf', _(u'Fio banka')),
        ('cs', _(u'PLATBA 24 – Česká spořitelna')),
        ('era', _(u'Era - Poštovní spořitelna')),
        ('cb', _(u'ČSOB')),
        ('c', _(u'Kreditní karta přes GPE')),
        ('bt', _(u'bankovní převod')),
        ('pt', _(u'převod přes poštu')),
        ('sc', _(u'superCASH')),  # Deprecated
        ('psc', _(u'PaySec')),
        ('mo', _(u'Mobito')),
        ('t', _(u'testovací platba')),

        ('fa', _(u'faktura mimo PayU')),
        ('fc', _(u'firma platí fakturou')),
        ('am', _(u'člen Klubu přátel Auto*Matu')),
        ('amw', _(u'kandidát na členství v Klubu přátel Auto*Matu')),
        ('fe', _(u'neplatí startovné')),
    )
    PAY_TYPES_DICT = dict(PAY_TYPES)

    NOT_PAYING_TYPES = [
        'am',
        'amw',
        'fe',
    ]

    PAYU_PAYING_TYPES = [
        'mp',
        'kb',
        'rf',
        'pg',
        'pv',
        'pf',
        'cs',
        'era',
        'cb',
        'c',
        'bt',
        'pt',
        'sc',
        'psc',
        'mo',
        't',
    ]

    class Meta:
        verbose_name = _(u"Platební transakce")
        verbose_name_plural = _(u"Platební transakce")

    order_id = models.CharField(
        verbose_name="Order ID",
        max_length=50,
        null=True,
        blank=True,
        default="")
    session_id = models.CharField(
        verbose_name="Session ID",
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        default=None)
    trans_id = models.CharField(
        verbose_name="Transaction ID",
        max_length=50, null=True, blank=True)
    amount = models.PositiveIntegerField(
        verbose_name=_(u"Částka"),
        null=False)
    pay_type = models.CharField(
        verbose_name=_(u"Typ platby"),
        choices=PAY_TYPES,
        max_length=50,
        null=True, blank=True)
    error = models.PositiveIntegerField(
        verbose_name=_(u"Chyba"),
        null=True, blank=True)
    invoice = models.ForeignKey(
        Invoice,
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,
        related_name=("payment_set"),
    )

    def save(self, *args, **kwargs):
        status_before_update = None
        if self.id:
            status_before_update = Payment.objects.get(pk=self.id).status
            logger.info(u"Saving payment (before): %s" % Payment.objects.get(pk=self.id).full_string())
        super(Payment, self).save(*args, **kwargs)

        statuses_company_ok = (Status.COMPANY_ACCEPTS, Status.INVOICE_MADE, Status.INVOICE_PAID)
        if (
                self.user_attendance and
                (status_before_update != Status.DONE) and
                self.status == Status.DONE):
            payment_confirmation_mail(self.user_attendance)
        elif (self.user_attendance and
                (status_before_update not in statuses_company_ok) and
                self.status in statuses_company_ok):
            payment_confirmation_company_mail(self.user_attendance)

        logger.info(u"Saving payment (after):  %s" % Payment.objects.get(pk=self.id).full_string())

    def full_string(self):
        if self.user_attendance:
            user = self.user_attendance
            username = self.user_attendance.userprofile.user.username
        else:
            user = None
            username = None
        return u"id: %s, user: %s (%s), order_id: %s, session_id: %s, trans_id: %s, amount: %s, description: %s, created: %s, realized: %s, pay_type: %s, status: %s, error: %s" % (
            self.pk,
            user,
            username,
            self.order_id,
            getattr(self, "session_id", ""),
            self.trans_id,
            self.amount,
            self.description,
            self.created,
            self.realized,
            self.pay_type,
            self.status,
            self.error)


class PaymentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        self.fields['status'] = forms.ChoiceField(choices=STATUS)

    class Meta:
        model = Payment
        fields = "__all__"


class Trip(models.Model):
    """Cesty"""
    DIRECTIONS = [
        ('trip_to', _(u"Tam")),
        ('trip_from', _(u"Zpět")),
    ]
    DIRECTIONS_DICT = dict(DIRECTIONS)
    MODES = [
        ('bicycle', _("Na kole")),
        ('by_foot', _("Pěšky/běh")),
        ('no_work', _("Nepracoval")),
        ('by_other_vehicle', _("Jiný dopravní prostředek")),
    ]

    class Meta:
        verbose_name = _(u"Cesta")
        verbose_name_plural = _(u"Cesty")
        unique_together = (("user_attendance", "date", "direction"),)
        ordering = ('date', '-direction')
    objects = BulkUpdateManager()

    user_attendance = models.ForeignKey(
        UserAttendance,
        related_name="user_trips",
        null=True,
        blank=False,
        default=None)
    direction = models.CharField(
        verbose_name=_(u"Směr cesty"),
        choices=DIRECTIONS,
        max_length=20,
        null=True, blank=True)
    date = models.DateField(
        verbose_name=_(u"Datum cesty"),
        default=datetime.date.today,
        null=False)
    commute_mode = models.CharField(
        verbose_name=_(u"Mód dopravy"),
        choices=MODES,
        max_length=20,
        default=None,
        null=True,
        blank=True,
    )
    distance = models.FloatField(
        verbose_name=_(u"Ujetá vzdálenost"),
        null=True,
        blank=False,
        default=None,
        validators=[
            MaxValueValidator(1000),
            MinValueValidator(0)
        ],
    )

    def distance_from_cutted(self):
        if self.trip_from and self.is_working_ride_from:
            plus_distance = self.user_attendance.campaign.trip_plus_distance
            max_distance = (self.user_attendance.get_distance() or 0) + plus_distance
            ridden_distance = self.distance_from or 0
            if ridden_distance > max_distance:
                return (True, max_distance)
            else:
                return (False, ridden_distance)
        else:
            return (False, 0)

    def distance_to_cutted(self):
        if self.trip_to and self.is_working_ride_to:
            plus_distance = self.user_attendance.campaign.trip_plus_distance
            max_distance = (self.user_attendance.get_distance() or 0) + plus_distance
            ridden_distance = self.distance_to or 0
            if ridden_distance > max_distance:
                return (True, max_distance)
            else:
                return (False, ridden_distance)
        else:
            return (False, 0)

    def working_day(self):
        return util.working_day(self.date)

    def active(self):
        return util.day_active(self.date)


class Competition(models.Model):
    """Soutěžní kategorie"""

    CTYPES = (
        ('length', _(u"Ujetá vzdálenost")),
        ('frequency', _(u"Pravidelnost jízd na kole")),
        ('questionnaire', _(u"Dotazník")),
    )

    CCOMPETITORTYPES = (
        ('single_user', _(u"Jednotliví soutěžící")),
        ('liberos', _(u"Liberos")),
        ('team', _(u"Týmy")),
        ('company', _(u"Soutěž firem")),
    )

    class Meta:
        verbose_name = _(u"Soutěžní kategorie")
        verbose_name_plural = _(u"Soutěžní kategorie")
        ordering = ('-campaign', 'type', 'name')

    name = models.CharField(
        unique=False,
        verbose_name=_(u"Jméno soutěže"),
        max_length=160, null=False)
    campaign = models.ForeignKey(
        Campaign,
        verbose_name=_(u"Kampaň"),
        null=False,
        blank=False)
    slug = models.SlugField(
        unique=True,
        default="",
        verbose_name=u"Doména v URL",
        blank=False
    )
    url = models.URLField(
        default="",
        verbose_name=u"Odkaz na stránku soutěže",
        help_text=_(u"Odkaz na stránku, kde budou pravidla a podrobné informace o soutěži"),
        null=True,
        blank=True,
    )
    date_from = models.DateField(
        verbose_name=_(u"Datum začátku soutěže"),
        help_text=_(u"Od tohoto data se počítají jízdy"),
        default=None,
        null=True, blank=True)
    date_to = models.DateField(
        verbose_name=_(u"Datum konce soutěže"),
        help_text=_(u"Po tomto datu nebude možné soutěžit (vyplňovat dotazník)"),
        default=None,
        null=True, blank=True)
    type = models.CharField(
        verbose_name=_(u"Typ"),
        help_text=_(
            u"Určuje, zdali bude soutěž výkonnostní (na ujetou vzdálenost),"
            u" nebo na pravidelnost. Volba \"Dotazník\" slouží pro kreativní soutěže,"
            u" cyklozaměstnavatele roku a další dotazníky; je nutné definovat otázky."),
        choices=CTYPES,
        max_length=16,
        null=False)
    competitor_type = models.CharField(
        verbose_name=_(u"Typ soutěžícího"),
        help_text=_(u"Určuje, zdali bude soutěž týmová, nebo pro jednotlivce. Ostatní volby vybírejte jen pokud víte, k čemu slouží."),
        choices=CCOMPETITORTYPES,
        max_length=16,
        null=False)
    user_attendance_competitors = models.ManyToManyField(
        UserAttendance,
        verbose_name=_(u"Přihlášení soutěžící jednotlivci"),
        related_name="competitions",
        blank=True)
    team_competitors = models.ManyToManyField(
        Team,
        verbose_name=_(u"Přihlášené soutěžící týmy"),
        related_name="competitions",
        blank=True)
    company_competitors = models.ManyToManyField(
        Company,
        verbose_name=_(u"Přihlášené soutěžící firmy"),
        related_name="competitions",
        blank=True)
    city = models.ManyToManyField(
        City,
        verbose_name=_(u"Soutěž pouze pro města"),
        help_text=_(u"Soutěž bude probíhat ve vybraných městech. Pokud zůstane prázdné, soutěž probíhá ve všech městech."),
        blank=True)
    company = models.ForeignKey(
        Company,
        verbose_name=_(u"Soutěž pouze pro firmu"),
        null=True,
        blank=True)
    sex = models.CharField(
        verbose_name=_(u"Soutěž pouze pro pohlaví"),
        help_text=_(u"Pokud chcete oddělit výsledky pro muže a ženy, je potřeba vypsat dvě soutěže - jednu pro muže a druhou pro ženy. Jinak nechte prázdné."),
        choices=UserProfile.GENDER,
        default=None,
        max_length=50,
        null=True,
        blank=True,
    )
    without_admission = models.BooleanField(
        verbose_name=_(u"Soutěž bez přihlášek (pro všechny)"),
        help_text=_(u"Dotazník je obvykle na přihlášky, výkonnost také a pravidelnost bez nich."),
        default=True,
        null=False)
    public_answers = models.BooleanField(
        verbose_name=_(u"Zveřejňovat soutěžní odpovědi"),
        default=False,
        null=False)
    is_public = models.BooleanField(
        verbose_name=_(u"Soutěž je veřejná"),
        default=True,
        null=False)
    entry_after_beginning_days = models.IntegerField(
        verbose_name=_(u"Prodloužené přihlášky"),
        help_text=_(u"Počet dní po začátku soutěže, kdy je ještě možné se přihlásit"),
        default=7,
        blank=False,
        null=False,
    )
    rules = models.TextField(
        verbose_name=_(u"Pravidla soutěže"),
        default=None,
        blank=True,
        null=True,
    )

    def get_competitors(self, potencial_competitors=False):
        return results.get_competitors(self, potencial_competitors)

    def get_competitors_count(self):
        return self.get_competitors().count()

    def get_results(self):
        return results.get_results(self)

    def has_started(self):
        if self.date_from:
            return self.date_from <= util.today()
        else:
            return True

    def has_entry_opened(self):
        return self.date_from + datetime.timedelta(self.entry_after_beginning_days) <= util.today()

    def has_finished(self):
        if self.date_to:
            return not self.date_to >= util.today()
        else:
            return False

    def is_actual(self):
        return self.has_started() and not self.has_finished()

    def recalculate_results(self):
        return results.recalculate_result_competition(self)

    def can_admit(self, user_attendance):
        if self.without_admission:
            return 'without_admission'
        if not util.get_company_admin(user_attendance.userprofile.user, self.campaign) and self.competitor_type == 'company':
            return 'not_company_admin'
        if self.type == 'questionnaire' and not self.has_started():
            return 'before_beginning'
        if self.type == 'questionnaire' and self.has_finished():
            return 'after_end'
        if self.type != 'questionnaire' and self.has_entry_opened():
            return 'after_beginning'

        if not user_attendance.is_libero() == (self.competitor_type == 'liberos'):
            return 'not_libero'
        if self.company and self.company != user_attendance.team.subsidiary.company:
            return 'not_for_company'
        if self.city.exists() and not self.city.filter(pk=user_attendance.team.subsidiary.city.pk).exists():
            return 'not_for_city'

        return True

    def has_admission(self, userprofile):
        if not userprofile.entered_competition():
            return False
        if not userprofile.is_libero() == (self.competitor_type == 'liberos'):
            return False
        if self.company and userprofile.team and self.company != userprofile.team.subsidiary.company:
            return False
        if userprofile.team and self.city.exists() and not self.city.filter(pk=userprofile.team.subsidiary.city.pk).exists():
            return False

        if self.without_admission:
            return True
        else:
            if self.competitor_type == 'single_user' or self.competitor_type == 'liberos':
                return self.user_attendance_competitors.filter(pk=userprofile.pk).exists()
            elif self.competitor_type == 'team' and userprofile.team:
                return self.team_competitors.filter(pk=userprofile.team.pk).exists()
            elif self.competitor_type == 'company' and userprofile.company():
                return self.company_competitors.filter(pk=userprofile.company().pk).exists()
            return True

    def make_admission(self, userprofile, admission=True):
        if not self.without_admission and self.can_admit(userprofile):
            if self.competitor_type == 'single_user' or self.competitor_type == 'liberos':
                if admission:
                    self.user_attendance_competitors.add(userprofile)
                else:
                    self.user_attendance_competitors.remove(userprofile)
            elif self.competitor_type == 'team':
                if admission:
                    self.team_competitors.add(userprofile.team)
                else:
                    self.team_competitors.remove(userprofile.team)
            elif self.competitor_type == 'company':
                if admission:
                    self.company_competitors.add(userprofile.company())
                else:
                    self.company_competitors.remove(userprofile.company())
        results.recalculate_result_competitor_nothread(userprofile)

    def type_string(self):
        CTYPES_STRINGS = {
            'questionnaire': _('do&shy;ta&shy;zník'),
            'frequency': _('soutěž na pravidelnost'),
            'length': _('soutěž na vzdálenost'),
        }
        CCOMPETITORTYPES_STRINGS = {
            'single_user': _('jed&shy;not&shy;liv&shy;ců'),
            'liberos': _('li&shy;be&shy;ros'),
            'team': _('tý&shy;mů'),
            'company': _('spo&shy;le&shy;čno&shy;stí'),
        }
        if self.company:
            company_string_before = "vnitrofiremní"
            company_string_after = "společnosti %s" % escape(self.company)
        else:
            company_string_before = ""
            company_string_after = ""

        return string_concat(company_string_before, " ", CTYPES_STRINGS[self.type], " ", CCOMPETITORTYPES_STRINGS[self.competitor_type], " ", company_string_after)

    def __str__(self):
        return "%s" % self.name


class CompetitionForm(forms.ModelForm):
    class Meta:
        model = Competition
        exclude = ()
        widgets = {
            'rules': RedactorEditor(),
        }

    def set_fields_queryset_on_update(self):
        if hasattr(self.instance, 'campaign') and 'user_attendance_competitors' in self.fields:
            if self.instance.competitor_type in ['liberos', 'single_user']:
                self.fields['user_attendance_competitors'].queryset = self.instance.get_competitors(potencial_competitors=True).select_related('userprofile__user', 'campaign')
            else:
                self.fields['user_attendance_competitors'].queryset = self.instance.user_attendance_competitors.select_related('userprofile__user', 'campaign')

        if 'team_competitors' in self.fields:
            if self.instance.competitor_type == 'team':
                self.fields['team_competitors'].queryset = TeamName.objects.all()
            else:
                self.fields['team_competitors'].queryset = self.instance.team_competitors.all()

        if 'company_competitors' in self.fields:
            if self.instance.competitor_type == 'company':
                self.fields["company_competitors"].queryset = Company.objects.all()
            else:
                self.fields['company_competitors'].queryset = self.instance.company_competitors.all()

    def set_fields_queryset_on_create(self):
        if 'team_competitors' in self.fields:
            self.fields["team_competitors"].queryset = Team.objects.none()
        if 'user_attendance_competitors' in self.fields:
            self.fields["user_attendance_competitors"].queryset = UserAttendance.objects.none()
        if 'company_competitors' in self.fields:
            self.fields["company_competitors"].queryset = Company.objects.none()

    def __init__(self, *args, **kwargs):
        super(CompetitionForm, self).__init__(*args, **kwargs)
        if not hasattr(self.instance, 'campaign'):
            self.instance.campaign = Campaign.objects.get(slug=self.request.subdomain)

        if not self.request.user.is_superuser:
            self.fields["city"].queryset = self.request.user.userprofile.administrated_cities
            self.fields["city"].required = True

        if self.instance.id:
            self.set_fields_queryset_on_update()
        else:
            self.set_fields_queryset_on_create()


class CompetitionResult(models.Model):
    """Výsledek soutěže"""
    class Meta:
        verbose_name = _(u"Výsledek soutěže")
        verbose_name_plural = _(u"Výsledky soutěží")
        unique_together = (("user_attendance", "competition"), ("team", "competition"))

    user_attendance = models.ForeignKey(
        UserAttendance,
        related_name="competitions_results",
        null=True,
        blank=True,
        default=None,
    )
    team = models.ForeignKey(
        Team,
        related_name="competitions_results",
        null=True,
        blank=True,
        default=None,
    )
    company = models.ForeignKey(
        Company,
        related_name="company_results",
        null=True,
        blank=True,
        default=None,
    )
    competition = models.ForeignKey(
        Competition,
        related_name="results",
        null=False,
        blank=False,
    )
    result = models.FloatField(
        verbose_name=_(u"Výsledek"),
        null=True,
        blank=True,
        default=None,
        db_index=True,
    )

    def get_team(self):
        if self.competition.competitor_type in ['liberos', 'single_user']:
            return self.user_attendance.team
        if self.competition.competitor_type == 'team':
            return self.team

    def get_company(self):
        team = self.get_team()
        if team:
            return team.subsidiary.company

    def get_city(self):
        team = self.get_team()
        if team:
            return team.subsidiary.city

    def get_result(self):
        return round(self.result, 1)

    def get_result_percentage(self):
        if self.result:
            return round(self.result * 100, 1)
        else:
            return 0

    def get_total_result(self):
        # TODO: don't use this function, show rides table instead
        if self.competition.type == 'length':
            if self.user_attendance:
                return round(self.result, 1)
            if self.team:
                return round(self.result * self.team.member_count, 1)

        elif self.competition.type == 'frequency':
            if self.user_attendance:
                return self.user_attendance.get_rides_count_denorm or ""
            if self.team:
                return self.team.get_rides_count_denorm or ""

    def __str__(self):
        if self.competition.competitor_type == 'team':
            return "%s" % self.team.name
        elif self.competition.competitor_type == 'company':
            return "%s" % self.company.name
        else:
            if self.user_attendance:
                return "%s" % self.user_attendance.userprofile.name()

    def clean(self):
        if ((1 if self.user_attendance else 0) + (1 if self.team else 0) + (1 if self.company else 0)) != 1:
            raise ValidationError(_(u"Musí být zvolen právě jeden uživatel, tým nebo společnost"))

    def user_attendances(self):
        competition = self.competition
        if competition.competitor_type == 'single_user' or competition.competitor_type == 'libero':
            return [self.user_attendance]
        elif competition.competitor_type == 'team':
            return self.team.members()
        elif competition.competitor_type == 'company':
            return UserAttendance.objects.filter(team__subsidiary__company=self.company)


class ChoiceType(models.Model):
    """Typ volby"""
    class Meta:
        verbose_name = _(u"Typ volby")
        verbose_name_plural = _(u"Typ volby")
        unique_together = (("competition", "name"),)

    competition = models.ForeignKey(
        Competition,
        null=False,
        blank=False)
    name = models.CharField(
        verbose_name=_(u"Jméno"),
        unique=True,
        max_length=40, null=True)
    universal = models.BooleanField(
        verbose_name=_(u"Typ volby je použitelný pro víc otázek"),
        default=False)

    def __str__(self):
        return "%s" % self.name


class QuestionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        if hasattr(self, 'request') and not self.request.user.is_superuser:
            administrated_cities = self.request.user.userprofile.administrated_cities.all()
            campaign_slug = self.request.subdomain
            self.fields['competition'].queryset = Competition.objects.filter(city__in=administrated_cities, campaign__slug=campaign_slug).distinct()

        if hasattr(self.instance, 'competition'):
            self.fields['choice_type'].queryset = ChoiceType.objects.filter(Q(competition=self.instance.competition) | Q(universal=True))
        else:
            self.fields['choice_type'].queryset = ChoiceType.objects.filter(universal=True)


class Question(models.Model):

    class Meta:
        verbose_name = _(u"Anketní otázka")
        verbose_name_plural = _(u"Anketní otázky")
        ordering = ("order",)

    QTYPES = (
        ('text', _(u"Text")),
        ('choice', _(u"Výběr odpovědi")),
        ('multiple-choice', _(u"Výběr z více odpovědí")),
    )

    COMMENT_TYPES = (
        (None, _(u"Nic")),
        ('text', _(u"Text")),
        ('link', _(u"Odkaz")),
        ('one-liner', _(u"Jeden řádek textu")),
    )

    name = models.CharField(
        verbose_name=_(u"Jméno"),
        max_length=60,
        null=True,
        blank=True,
    )
    text = models.TextField(
        verbose_name=_(u"Otázka"),
        null=True,
        blank=True,
    )
    date = models.DateField(
        verbose_name=_(u"Den"),
        null=True, blank=True)
    type = models.CharField(
        verbose_name=_(u"Typ"),
        choices=QTYPES,
        default='text',
        max_length=16,
        null=False)
    comment_type = models.CharField(
        verbose_name=_(u"Typ komentáře"),
        choices=COMMENT_TYPES,
        default=None,
        max_length=16,
        blank=True,
        null=True)
    with_attachment = models.BooleanField(
        verbose_name=_(u"Povolit přílohu"),
        default=False,
        null=False)
    order = models.IntegerField(
        verbose_name=_(u"Pořadí"),
        null=True, blank=True)
    competition = models.ForeignKey(
        Competition,
        verbose_name=_(u"Soutěž"),
        null=False,
        blank=False)
    choice_type = models.ForeignKey(
        ChoiceType,
        verbose_name=_(u"Typ volby"),
        default=None,
        null=True,
        blank=True)
    required = models.BooleanField(
        verbose_name=_(u"Povinná otázka"),
        default=True,
        null=False)

    def __str__(self):
        return "%s" % (self.name or self.text)

    def with_answer(self):
        return self.comment_type or self.with_attachment or self.type != 'text' or self.choice_type is not None


class Choice(models.Model):

    class Meta:
        verbose_name = _(u"Nabídka k anketním otázce")
        verbose_name_plural = _(u"Nabídky k anketním otázkám")
        unique_together = (("choice_type", "text"),)

    choice_type = models.ForeignKey(
        ChoiceType,
        verbose_name=_(u"Typ volby"),
        related_name="choicetype_set",
        null=False,
        blank=False)
    text = models.CharField(
        verbose_name=_(u"Nabídka"),
        max_length=250,
        db_index=True,
        null=False)
    points = models.IntegerField(
        verbose_name=_(u"Body"),
        null=True,
        blank=True,
        default=None,
    )

    def __str__(self):
        return "%s" % self.text


class Answer(models.Model):
    """Odpověď"""
    class Meta:
        verbose_name = _(u"Odpověď")
        verbose_name_plural = _(u"Odpovědi")
        ordering = ('user_attendance__team__subsidiary__city', 'pk')
        unique_together = (("user_attendance", "question"),)

    user_attendance = models.ForeignKey(UserAttendance, null=True, blank=True)
    question = models.ForeignKey(Question, null=False)
    choices = models.ManyToManyField(
        Choice,
        blank=True,
    )
    comment = models.TextField(
        verbose_name=_(u"Komentář"),
        max_length=600,
        null=True, blank=True)
    points_given = models.IntegerField(
        null=True, blank=True, default=None)
    attachment = models.FileField(
        upload_to=u"questionaire/",
        max_length=600,
        blank=True,
    )

    def has_any_answer(self):
        return self.comment or self.choices.all() or self.attachment or self.points_given

    def str_choices(self):
        return ", ".join([choice.text for choice in self.choices.all()])

    # TODO: repair tests with this
    # def __str__(self):
    #      return "%s" % self.str_choices()


def get_company(campaign, user):
    return user.userprofile.userattendance_set.get(campaign=campaign).company()


class Voucher(models.Model):
    TYPES = [
        ('rekola', _(u"ReKola")),
    ]
    TYPE_DICT = dict(TYPES)
    type = models.CharField(
        verbose_name=_(u"typ voucheru"),
        choices=TYPES,
        max_length=10,
        null=False,
        blank=False,
        default='rekola',
    )
    token = models.TextField(
        verbose_name=_(u"token"),
        blank=False,
        null=True,
    )
    user_attendance = models.ForeignKey(
        UserAttendance,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _(u"Voucher")
        verbose_name_plural = _(u"Vouchery")

    def type_string(self):
        return self.TYPE_DICT[self.type]


def normalize_gpx_filename(instance, filename):
    return '-'.join(['gpx_tracks/track', datetime.datetime.now().strftime("%Y-%m-%d"), unidecode(filename)])


@with_author
class GpxFile(models.Model):
    file = models.FileField(
        verbose_name=_(u"GPX soubor"),
        help_text=_(u"Zadat trasu nahráním souboru GPX"),
        upload_to=normalize_gpx_filename,
        blank=True, null=True)
    DIRECTIONS = [
        ('trip_to', _(u"Tam")),
        ('trip_from', _(u"Zpět")),
    ]
    DIRECTIONS_DICT = dict(DIRECTIONS)
    trip_date = models.DateField(
        verbose_name=_(u"Datum vykonání cesty"),
        null=False,
        blank=False
    )
    direction = models.CharField(
        verbose_name=_(u"Směr cesty"),
        choices=DIRECTIONS,
        max_length=50,
        null=False, blank=False)
    trip = models.OneToOneField(
        Trip,
        null=True,
        blank=True)
    track = models.MultiLineStringField(
        verbose_name=_(u"trasa"),
        srid=4326,
        null=True,
        blank=True,
        geography=True,
    )
    user_attendance = models.ForeignKey(
        UserAttendance,
        null=False,
        blank=False)
    from_application = models.BooleanField(
        verbose_name=_(u"Nahráno z aplikace"),
        default=False,
        null=False,
    )
    created = models.DateTimeField(
        verbose_name=_(u"Datum vytvoření"),
        auto_now_add=True,
        null=True,
    )
    updated = models.DateTimeField(
        verbose_name=_(u"Datum poslední změny"),
        auto_now=True,
        null=True,
    )

    objects = models.GeoManager()

    class Meta:
        verbose_name = _(u"GPX soubor")
        verbose_name_plural = _(u"GPX soubory")
        unique_together = (
            ("user_attendance", "trip_date", "direction"),
            ("trip", "direction"),
        )
        ordering = ('trip_date', 'direction')

    def direction_string(self):
        return self.DIRECTIONS_DICT[self.direction]

    def length(self):
        length = GpxFile.objects.length().get(pk=self.pk).length
        if length:
            return round(length.km, 2)

    def clean(self):
        if self.file:
            self.track_clean = gpx_parse.parse_gpx(self.file.read().decode("utf-8"))


# Signals:
def pre_user_team_changed(sender, instance, changed_fields=None, **kwargs):
    field, (old, new) = next(iter(changed_fields.items()))
    new_team = Team.objects.get(pk=new) if new else None
    if new_team and new_team.campaign != instance.campaign:
        logger.error(u"UserAttendance %s campaign doesn't match team campaign" % instance)
    if instance.team and new_team.member_count == 0:
        instance.approved_for_team = 'approved'
    else:
        instance.approved_for_team = 'undecided'


def post_user_team_changed(sender, instance, changed_fields=None, **kwargs):
    field, (old, new) = next(iter(changed_fields.items()))
    old_team = Team.objects.get(pk=old) if old else None
    new_team = Team.objects.get(pk=new) if new else None
    if new_team:
        results.recalculate_results_team(new_team)

    if old_team:
        results.recalculate_results_team(old_team)

    results.recalculate_result_competitor(instance)


@receiver(post_save, sender=User)
def update_mailing_user(sender, instance, created, **kwargs):
    try:
        for user_attendance in instance.userprofile.userattendance_set.all():
            if not kwargs.get('raw', False) and user_attendance.campaign:
                mailing.add_or_update_user(user_attendance)
    except UserProfile.DoesNotExist:
        pass


@receiver(pre_save, sender=GpxFile)
def set_trip(sender, instance, *args, **kwargs):
    try:
        trip = Trip.objects.get(user_attendance=instance.user_attendance, date=instance.trip_date, direction=instance.direction)
    except Trip.DoesNotExist:
        trip = None
    instance.trip = trip


def set_track(sender, instance, changed_fields=None, **kwargs):
    if hasattr(instance, 'track_clean'):
        instance.track = instance.track_clean


@receiver(post_save, sender=GpxFile)
def set_trip_post(sender, instance, *args, **kwargs):
    if instance.trip and instance.trip.active():
        length = instance.length()
        if length:
            instance.trip.distance = length
            instance.trip.save()


@receiver(post_save, sender=UserActionTransaction)
@receiver(post_delete, sender=UserActionTransaction)
def update_user_attendance(sender, instance, *args, **kwargs):
    if not kwargs.get('raw', False):
        mailing.add_or_update_user(instance.user_attendance)


@receiver(pre_delete, sender=Invoice)
def user_attendance_pre_delete(sender, instance, *args, **kwargs):
    for payment in instance.payment_set.all():
        payment.status = Status.COMPANY_ACCEPTS
        payment.save()


@receiver(post_save, sender=UserAttendance)
def update_mailing_user_attendance(sender, instance, created, **kwargs):
    if not kwargs.get('raw', False):
        mailing.add_or_update_user(instance)


@receiver(post_save, sender=Payment)
def update_mailing_payment(sender, instance, created, **kwargs):
    if instance.user_attendance and kwargs.get('raw', False):
        mailing.add_or_update_user(instance.user_attendance)


@receiver(post_save, sender=Trip)
def trip_post_save(sender, instance, **kwargs):
    if instance.user_attendance and not hasattr(instance, "dont_recalculate"):
        results.recalculate_result_competitor(instance.user_attendance)


@receiver(post_save, sender=Competition)
def competition_post_save(sender, instance, **kwargs):
    instance.recalculate_results()


@receiver(post_save, sender=Answer)
def answer_post_save(sender, instance, **kwargs):
    competition = instance.question.competition
    if competition.competitor_type == 'team':
        results.recalculate_result(competition, instance.user_attendance.team)
    elif competition.competitor_type == 'single_user' or competition.competitor_type == 'liberos':
        results.recalculate_result(competition, instance.user_attendance)
    elif competition.competitor_type == 'company':
        results.recalculate_result(competition, instance.user_attendance.company())


@receiver(pre_save, sender=Payment)
def payment_set_realized_date(sender, instance, **kwargs):
    if instance.status in Payment.done_statuses and not instance.realized:
        instance.realized = datetime.datetime.now()

from . import results  # noqa
