# -*- coding: utf-8 -*-
# Author: Hynek Hanke <hynek.hanke@auto-mat.cz>
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
import django
import random
import string
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db.models import Q
from django.core.exceptions import ValidationError
from composite_field import CompositeField
from django.utils.translation import gettext_lazy as _
# Python library imports
import datetime
# Local imports
import util

class Address(CompositeField):
    street = models.CharField(
        verbose_name=_("Ulice"),
        default="",
        max_length=50,
        null=False,
        )
    street_number = models.CharField(
        verbose_name=_("Číslo domu"),
        default="",
        max_length=10,
        null=False,
        blank=False,
        )
    recipient = models.CharField(
        verbose_name=_("Adresát"),
        default="",
        max_length=50,
        null=False,
        blank=False,
        )
    district = models.CharField(
        verbose_name=_("Městská část"),
        default="",
        max_length=50,
        null=False,
        blank=False,
        )
    psc = models.IntegerField(
        verbose_name=_("PSČ"),
        default=0,
        null=False,
        blank=False,
        )
    city = models.CharField(
        verbose_name=_("Adresní město"),
        default="",
        max_length=50,
        null=False,
        blank=False,
        )

    def __unicode__(self):
        return "%s, %s %s, %s, %s, %s" % (self.recipient, self.street, self.street_number, self.district, self.psc, self.city)

class City(models.Model):
    """Město"""

    class Meta:
        verbose_name = _("Město")
        verbose_name_plural = _("Města")
    name = models.CharField(
        verbose_name=_("Jméno"),
        unique=True,
        max_length=40, null=False)
    city_admins = models.ManyToManyField(
        'UserProfile',
        related_name = "administrated_cities",
        null=True,
        blank=True)
    admission_fee = models.PositiveIntegerField(
        verbose_name=_("Poplatek"),
        null=False,
        default=160)

    def __unicode__(self):
        return "%s" % self.name

class Company(models.Model):
    """Firma"""

    class Meta:
        verbose_name = _("Firma")
        verbose_name_plural = _("Firmy")
        ordering = ('name',)

    name = models.CharField(
        unique=True,
        verbose_name=_("Jméno"),
        max_length=60, null=False)
    company_admin = models.OneToOneField(
        "UserProfile", 
        related_name = "administrated_company",
        verbose_name = _("Firemní admin"),
        null=True,
        blank=True)
    invoice_address = Address()
    ico = models.PositiveIntegerField(
        default=0,
        verbose_name=_("IČO"),
        null=False)

    def __unicode__(self):
        return "%s" % self.name

class Subsidiary(models.Model):
    """Pobočka"""

    class Meta:
        verbose_name = _("Pobočka")
        verbose_name_plural = _("Pobočky")

    address = Address()
    company = models.ForeignKey(
          Company, 
          related_name="subsidiaries",
          null=False, 
          blank=False)
    city = models.ForeignKey(
          City, 
          verbose_name=_("Soutěžní město"),
          null=False, blank=False)

    def __unicode__(self):
        return "%s, %s %s, %s, %s, %s" % (self.address.recipient, self.address.street, self.address.street_number, self.address.district, self.address.psc, self.address.city)

def validate_length(value,min_length=25):
    str_len = len(str(value))
    if str_len<min_length:
        raise ValidationError(_("The string should be longer than %(min)s, but is %(max)s characters long") % {'min': min_length, 'max': str_len})

class Team(models.Model):
    """Profil týmu"""

    class Meta:
        verbose_name = _("Tým")
        verbose_name_plural = _("Týmy")
        ordering = ('name',)

    name = models.CharField(
        verbose_name=_("Název týmu"),
        max_length=50, null=False,
        unique=True)
    subsidiary = models.ForeignKey(
        Subsidiary,
        verbose_name=_("Pobočka"),
        related_name='teams',
        null=False,
        blank=False)
    coordinator = models.OneToOneField(
        'UserProfile',
        related_name = "coordinated_team",
        verbose_name = _("Koordinátor"),
        null=True,
        blank=True,
        #TODO:
        #null=False,
        #blank=False,
        unique=True,
        )
    invitation_token = models.CharField(
        verbose_name=_("Token pro pozvánky"),
        default=''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(30)),
        max_length=100,
        null=False,
        blank=False,
        unique=True,
        validators = [validate_length],
        )

    def __unicode__(self):
        return "%s / %s" % (self.name, self.subsidiary.company)

    def save(self, force_insert=False, force_update=False):
        if self.coordinator_id is not None and self.coordinator is not None and self.coordinator.team.id != self.id:
            raise Exception(_("Nový koordinátor %(coordinator)s není členem týmu %(team)s") % {'coordinator': self.coordinator, 'team': self})
        super(Team, self).save(force_insert, force_update)

class UserProfile(models.Model):
    """Uživatelský profil"""

    class Meta:
        verbose_name = u"Uživatel"
        verbose_name_plural = u"Uživatelé"

    TSHIRTSIZE = [
              ('wXXS', u"dámské XXS"),
              ('wXS', u"dámské XS"),
              ('wS', u"dámské S"),
              ('wM', u"dámské M"),
              ('wL', u"dámské L"),
              ('wXL', u"dámské XL"),
              ('wXXL', u"dámské XXL"),

              ('mS', u"pánské S"),
              ('mM', u"pánské M"),
              ('mL', u"pánské L"),
              ('mXL', u"pánské XL"),
              ('mXXL', u"pánské XXL"),
              ]

    TEAMAPPROVAL = (('approved', _("Odsouhlasený")),
              ('undecided', _("Nerozhodnuto")),
              ('denied', _("Zamítnutý")),
              )

    LANGUAGE = [
            ('cs', _("Čeština")),
            ('en', _("Angličtna")),
              ]

    user = models.OneToOneField(
        User,
        related_name='userprofile',
        unique=True,
        null=False,
        blank=False,
        )
    distance = models.PositiveIntegerField(
        verbose_name=_("Vzdálenost"),
        null=False)
    # -- Contacts
    telephone = models.CharField(
        verbose_name=_("Telefon"),
        max_length=30, null=False)
    team = models.ForeignKey(
        Team,
        verbose_name=_("Tým"),
        null=False, blank=False)

    trips = models.PositiveIntegerField(
        verbose_name=_("Počet cest"),
        default=0, null=False, blank=False)
    company_admin_unapproved = models.BooleanField(
        verbose_name=_("Správcovství organizace není schváleno"),
        default=True)
    approved_for_team = models.CharField(
        verbose_name=_("Souhlas týmu"),
        choices=TEAMAPPROVAL,
        max_length=16,
        null=False,
        default='undecided')
    language = models.CharField(
        verbose_name=_("Jazyk komunikace"),
        choices=LANGUAGE,
        max_length=16,
        null=False,
        default='cs')
    t_shirt_size = models.CharField(
        verbose_name=_("Velikost trička"),
        choices=TSHIRTSIZE,
        max_length=16,
        null=False,
        default='L')
    motivation_company_admin = models.TextField(
        verbose_name=_("Motivační text aspiranta na firemního admina"),
        default="",
        max_length=5000,
        null=True,
        blank=True,
        )

    def first_name(self):
        return user.first_name

    def last_name(self):
        return user.last_name

    def __unicode__(self):
        return self.user.get_full_name()

    def payment_status(self):
        if self.team.subsidiary.city.admission_fee == 0:
            return 'no_admission'

        # Check payment status for this user
        payments = Payment.objects.filter(user=self)
        p_status = [p.status for p in payments]
        if (99 in p_status) or (1005 in p_status) or (1006 in p_status) or (1007 in p_status):
            # Payment done
            status = 'done'
        elif (1 in p_status) or (4 in p_status) or (5 in p_status):
            # A payment is still waiting
            status = 'waiting'
        else:
            # No payment done and no waiting
            status = None
        return status

    def payment_type(self):
        try:
            payment = Payment.objects.filter(user=self).latest('id')
        except Payment.DoesNotExist:
            return None
        return payment.pay_type

class UserProfileUnpaidManager(models.Manager):
    def get_query_set(self):
        paying_or_prospective_user_ids = [p.user_id for p in Payment.objects.filter(
                Q(status='99') | Q (
                    # Bank transfer less than 5 days old
                    status='1', pay_type='bt',
                    created__gt=datetime.datetime.now() - datetime.timedelta(days=5))
                )]
        return super(UserProfileUnpaidManager,self).get_query_set().filter(
            active=True).exclude(id__in=paying_or_prospective_user_ids)

    

class UserProfileUnpaid(UserProfile):
    objects = UserProfileUnpaidManager()
    class Meta:
        proxy = True
        verbose_name = _("Uživatel s nezaplaceným startovným")
        verbose_name_plural = _("Uživatelé s nezaplaceným startovným")

class Payment(models.Model):
    """Platba"""

    STATUS = (
        (1, 'Nová'),
        (2, 'Zrušena'),
        (3, 'Odmítnuta'),
        (4, 'Zahájena'),
        (5, 'Očekává potvrzení'),
        (7, 'Platba zamítnuta, prostředky nemožno vrátit, řeší PayU'),
        (99, 'Přijata'),
        (888, 'Nesprávný status -- kontaktovat PayU'),
        (1005, 'Firma akceptuje platbu'),
        (1006, 'Faktura vystavena'),
        (1007, 'Faktura zaplacena'),
        )

    PAY_TYPES = (
        ('mp', 'mPenize'),
        ('kb', 'MojePlatba'),
        ('rf', 'ePlatby pro eKonto'),
        ('pg', 'GE Money Bank'),
        ('pv', 'Volksbank'),
        ('pf', 'Fio banka'),
        ('c', 'Kreditní karta přes GPE'),
        ('bt', 'bankovní převod'),
        ('pt', 'převod přes poštu'),
        ('sc', 'superCASH'),
        ('t', 'testovací platba'),
        ('fa', 'faktura mimo PayU'),
        ('fc', 'firma platí fakturou'),
        ('am', 'člen klubu přátel Auto*matu'),
        )

    class Meta:
        verbose_name = _("Platba")
        verbose_name_plural = _("Platby")

    user = models.ForeignKey(UserProfile, 
        null=True, 
        blank=True, 
        default=None)
    order_id = models.CharField(
        verbose_name="Order ID",
        max_length=50,
        null=True,
        blank=True,
        default="")
    session_id = models.CharField(
        verbose_name="Session ID",
        max_length=50,
        null=True,
        blank=True,
        default="")
    trans_id = models.CharField(
        verbose_name="Transaction ID",
        max_length=50, null=True, blank=True)
    amount = models.PositiveIntegerField(
        verbose_name=_("Částka"),
        null=False)
    description = models.CharField(
        verbose_name=_("Popis"),
        max_length=500,
        null=True,
        blank=True,
        default="")
    created = models.DateTimeField(
        verbose_name=_("Zadání platby"),
        default=datetime.datetime.now,
        null=False)
    realized = models.DateTimeField(
        verbose_name=_("Realizace"),
        null=True, blank=True)
    pay_type = models.CharField(
        verbose_name=_("Typ platby"),
        choices=PAY_TYPES,
        max_length=50,
        null=True, blank=True)
    status = models.PositiveIntegerField(
        verbose_name=_("Status"),
        choices=STATUS,
        max_length=50,
        null=True, blank=True)
    error = models.PositiveIntegerField(
        verbose_name=_("Chyba"),
        null=True, blank=True)
    company_wants_to_pay = models.BooleanField(
        verbose_name=_("Firma chce zaplatit"),
        default=False)

    def __unicode__(self):
        if self.trans_id:
            return self.trans_id
        else:
            return self.session_id

class Voucher(models.Model):
    """Slevove kupony"""

    class Meta:
        verbose_name = _("Kupon")
        verbose_name_plural = _("Kupony")

    code = models.CharField(
        verbose_name=_("Kód"),
        max_length=20, null=False)
    user = models.ForeignKey(UserProfile, null=True, blank=True)

class Trip(models.Model):
    """Cesty"""

    class Meta:
        verbose_name = _("Cesta")
        verbose_name_plural = _("Cesty")

    user = models.ForeignKey(UserProfile, null=True, blank=True)
    date = models.DateField(
        verbose_name=_("Datum cesty"),
        default=datetime.datetime.now,
        null=False)
    trip_to = models.BooleanField(
        verbose_name=_("Cesta do práce"),
        null=False)
    trip_from = models.BooleanField(
        verbose_name=_("Cesta z práce"),
        null=False)
    distance_to = models.IntegerField(
        verbose_name=_("Ujetá vzdálenost do práce"),
        null=True, blank=True)
    distance_from = models.IntegerField(
        verbose_name=_("Ujetá vzdálenost z práce"),
        null=True, blank=True)

class Competition(models.Model):
    """Závod"""

    CTYPES = (
        ('length', _("Ujetá vzdálenost")),
        ('frequency', _("Pravidelnost dojíždění")),
        ('questionnaire', _("Dotazník")),
        )

    CCOMPETITORTYPES = (
        ('single_user', _("Jednotlivý uživatelé")),
        ('team', _("Týmy")),
        ('company', _("Soutěž firem")),
        )

    class Meta:
        verbose_name = _("Závod")
        verbose_name_plural = _("Závody")
    name = models.CharField(
        unique=True,
        verbose_name=_("Jméno"),
        max_length=40, null=False)
    type = models.CharField(
        verbose_name=_("Typ"),
        choices=CTYPES,
        max_length=16,
        null=False)
    competitor_type = models.CharField(
        verbose_name=_("Typ závodníků"),
        choices=CCOMPETITORTYPES,
        max_length=16,
        null=False)
    user_competitors = models.ManyToManyField(
        UserProfile,
        related_name = "competitions",
        null=True, 
        blank=True)
    team_competitors = models.ManyToManyField(
        Team,
        related_name = "competitions",
        null=True, 
        blank=True)
    company_competitors = models.ManyToManyField(
        Company,
        related_name = "competitions",
        null=True, 
        blank=True)
    city = models.ForeignKey(
        City,
        verbose_name = _("Soutěž pouze pro město"),
        null=True, 
        blank=True)
    company = models.ForeignKey(
        Company,
        verbose_name = _("Soutěž pouze pro firmu"),
        null=True, 
        blank=True)
    without_admission = models.BooleanField(
        verbose_name = _("Soutěž bez přihlášek (pro všechny)"),
        default=False,
        null=False)

    def __unicode__(self):
        return "%s" % self.name

class ChoiceType(models.Model):
    """Typ volby"""
    class Meta:
        verbose_name = _("Typ volby")
        verbose_name_plural = _("Typ volby")
        unique_together = (("competition", "name"),)

    competition = models.ForeignKey(Competition,
        null=False,
        blank=False)
    name = models.CharField(
        verbose_name=_("Jméno"),
        unique = True,
        max_length=40, null=True)
    universal = models.BooleanField(
        verbose_name=_("Typ volby je použitelný pro víc otázek"),
        default=False)

    def __unicode__(self):
        return "%s" % self.name

class Question(models.Model):

    class Meta:
        verbose_name = _("Anketní otázka")
        verbose_name_plural = _("Anketní otázky")

    QTYPES = (
        ('text', _("Text")),
        ('choice', _("Výběr odpovědi")),
        ('multiple-choice', _("Výběr z více odpovědí")),
        )

    text = models.TextField(
        verbose_name=_("Otázka"),
        max_length=500,
        null=False)
    date = models.DateField(
        verbose_name=_("Den"),
        null=True, blank=True)
    type = models.CharField(
        verbose_name=_("Typ"),
        choices=QTYPES,
        max_length=16,
        null=False)
    with_comment = models.BooleanField(
        verbose_name = _("Povolit komentář"),
        default=True,
        null=False)
    with_attachment = models.BooleanField(
        verbose_name = _("Povolit přílohu"),
        default=True,
        null=False)
    order = models.IntegerField(
        verbose_name=_("Pořadí"),
        null=True, blank=True)
    competition = models.ForeignKey(
        Competition,
        verbose_name = _("Soutěž"),
        null=False, 
        blank=False)
    choice_type = models.ForeignKey(ChoiceType,
        null=False,
        blank=False)

    def __unicode__(self):
        return "%s" % self.text

class Choice(models.Model):
    
    class Meta:
        verbose_name = _("Nabídka k anketním otázce")
        verbose_name_plural = _("Nabídky k anketním otázkám")

    choice_type = models.ForeignKey(ChoiceType,
        verbose_name=_("Typ volby"),
        related_name="choices",
        null=False,
        blank=False)
    text = models.CharField(
        verbose_name=_("Nabídka"),
        max_length=300,
        null=False)
    points = models.IntegerField(
        verbose_name=_("Body"),
        null=True, blank=True)

    def __unicode__(self):
        return "%s" % self.text

class Answer(models.Model):
    user = models.ForeignKey(UserProfile, null=True)
    team = models.ForeignKey(Team, null=True)
    company = models.ForeignKey(Company, null=True)
    question = models.ForeignKey(Question, null=False)
    choices = models.ManyToManyField(Choice)
    comment = models.TextField(
        verbose_name=_("Komentář"),
        max_length=600,
        null=True, blank=True)
    points_given = models.IntegerField(
        null=True, blank=True, default=0)

    def str_choices(self):
        return ", ".join([choice.text for choice in self.choices.all()])

    def __unicode__(self):
        return "%s" % self.str_choices()
