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
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db.models import Q
# Python library imports
import datetime
# Local imports
import util

class City(models.Model):
    """Město"""

    class Meta:
        verbose_name = "Město"
        verbose_name_plural = "Města"
    name = models.CharField(
        verbose_name="Jméno",
        unique=True,
        max_length=40, null=False)
    city_admins = models.ManyToManyField(
        'UserProfile',
        related_name = "administrated_cities",
        null=True,
        blank=True)
    admission_fee = models.PositiveIntegerField(
        verbose_name="Poplatek",
        null=False,
        default=160)

    def __unicode__(self):
        return "%s" % self.name

class Company(models.Model):
    """Firma"""

    class Meta:
        verbose_name = "Firma"
        verbose_name_plural = "Firmy"
        ordering = ('name',)

    name = models.CharField(
        unique=True,
        verbose_name="Jméno",
        max_length=60, null=False)
    company_admin = models.OneToOneField(
        "UserProfile", 
        related_name = "administrated_company",
        verbose_name = "Firemní admin",
        null=True,
        blank=True)

    def __unicode__(self):
        return "%s" % self.name

class Subsidiary(models.Model):
    """Pobočka"""

    class Meta:
        verbose_name = "Pobočka"
        verbose_name_plural = "Pobočky"

    street = models.CharField(
        verbose_name="Ulice",
        max_length=50, null=False)
    street_number = models.CharField(
        verbose_name="Číslo domu",
        max_length=10, null=False, blank=False)
    recipient = models.CharField(
        verbose_name="Adresát",
        max_length=50, null=False, blank=False)
    district = models.CharField(
        verbose_name="Městská část",
        max_length=50, null=False, blank=False)
    PSC = models.IntegerField(
        verbose_name="PSČ",
        null=False, blank=False)
    company = models.ForeignKey(
          Company, null=False, blank=False)
    city = models.ForeignKey(
          City, null=False, blank=False)
    def address(self):
        return "%s, %s %s, %s, %s, %s" % (self.recipient, self.street, self.street_number, self.district, self.PSC, self.city)

    def __unicode__(self):
        return "%s" % self.address()

class Team(models.Model):
    """Profil týmu"""

    class Meta:
        verbose_name = "Tým"
        verbose_name_plural = "Týmy"
        ordering = ('name',)

    name = models.CharField(
        verbose_name="Název týmu",
        max_length=50, null=False,
        unique=True)
    subsidiary = models.ForeignKey(
        Subsidiary,
        verbose_name="Pobočka",
        null=False,
        blank=False)
    coordinator = models.OneToOneField(
        'UserProfile',
        related_name = "coordinated_team",
        verbose_name = 'Koordinátor',
        null=True, blank=True)

    def team_subsidiary_city(self):
        return self.subsidiary.city

    def team_subsidiary_company(self):
        return self.subsidiary.company

    def __unicode__(self):
        return "%s / %s" % (self.name, self.subsidiary.company)

class UserProfile(models.Model):
    """Uživatelský profil"""

    class Meta:
        verbose_name = "Uživatel"
        verbose_name_plural = "Uživatelé"

    GENDER = (('man', "Muž"),
              ('woman', "Žena"))

    TSHIRTSIZE = (('S', "S"),
              ('M', "M"),
              ('L', "L"),
              ('XL', "XL"),
              ('XXL', "XXL"))

    firstname = models.CharField(
        verbose_name="Jméno",
        max_length=30, null=False)
    surname = models.CharField(
        verbose_name="Příjmení",
        max_length=30, null=False)
    user = models.OneToOneField(
        User, unique=True)
    distance = models.PositiveIntegerField(
        verbose_name="Vzdálenost",
        null=False)
    # -- Contacts
    telephone = models.CharField(
        verbose_name="Telefon",
        max_length=30, null=False)
    team = models.ForeignKey(
        Team,
        verbose_name='Tým',
        null=False, blank=False)
    active = models.BooleanField(
        verbose_name="Aktivní",
        default=True)

    trips = models.PositiveIntegerField(
        verbose_name="Počet cest",
        default=0, null=False, blank=False)
    company_admin_unapproved = models.BooleanField(
        verbose_name="Správcovství organizace není schváleno",
        default=True)
    libero = models.BooleanField(
        verbose_name="Libero",
        default=False)
    t_shirt_size = models.CharField(
        verbose_name="Velikost trička",
        choices=TSHIRTSIZE,
        max_length=16,
        null=False,
        default='L')

    def person_name(self):
        return "%s %s" % (self.firstname, self.surname)
    person_name.short_description = 'Jméno'

    def __unicode__(self):
        return self.person_name()

    def email(self):
        return self.user.email
    email.admin_order_field  = 'user__email'

    def date_joined(self):
        return self.user.date_joined
    date_joined.admin_order_field  = 'user__date_joined'
    date_joined.short_description = 'Registrace'

    def city(self):
        return self.team.city
    city.short_description = u'Město'

    def payment_status(self):
        # Check payment status for this user
        payments = Payment.objects.filter(user=self)
        p_status = [p.status for p in payments]
        if 99 in p_status:
            # Payment done
            status = 'done'
        elif (1 in p_status) or (4 in p_status) or (5 in p_status):
            # A payment is still waiting
            status = 'waiting'
        else:
            # No payment done and no waiting
            status = None
        return status

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
        verbose_name = "Uživatel s nezaplaceným startovným"
        verbose_name_plural = "Uživatelé s nezaplaceným startovným"

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
        (888, 'Nesprávný status -- kontaktovat PayU')
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
        )

    class Meta:
        verbose_name = "Platba"
        verbose_name_plural = "Platby"

    user = models.ForeignKey(UserProfile, null=False)
    order_id = models.CharField(
        verbose_name="Order ID",
        max_length=50, null=False)
    session_id = models.CharField(
        verbose_name="Session ID",
        max_length=50, null=False)
    trans_id = models.CharField(
        verbose_name="Transaction ID",
        max_length=50, null=True, blank=True)
    amount = models.PositiveIntegerField(
        verbose_name="Částka",
        null=False)
    description = models.CharField(
        verbose_name="Popis",
        max_length=500,
        null=True)
    created = models.DateTimeField(
        verbose_name="Zadání platby",
        default=datetime.datetime.now,
        null=False)
    realized = models.DateTimeField(
        verbose_name="Realizace",
        null=True, blank=True)
    pay_type = models.CharField(
        verbose_name="Typ platby",
        choices=PAY_TYPES,
        max_length=50,
        null=True, blank=True)
    status = models.PositiveIntegerField(
        verbose_name="Status",
        choices=STATUS,
        max_length=50,
        null=True, blank=True)
    error = models.PositiveIntegerField(
        verbose_name="Chyba",
        null=True, blank=True)
    company_wants_to_pay = models.BooleanField(
        verbose_name="Firma chce zaplatit",
        default=False)

    def __unicode__(self):
        if self.trans_id:
            return self.trans_id
        else:
            return self.session_id

class Voucher(models.Model):
    """Slevove kupony"""

    class Meta:
        verbose_name = "Kupon"
        verbose_name_plural = "Kupony"

    code = models.CharField(
        verbose_name="Kód",
        max_length=20, null=False)
    user = models.ForeignKey(UserProfile, null=True, blank=True)

class Trip(models.Model):
    """Cesty"""

    class Meta:
        verbose_name = "Cesta"
        verbose_name_plural = "Cesty"

    user = models.ForeignKey(UserProfile, null=True, blank=True)
    date = models.DateField(
        verbose_name="Datum cesty",
        default=datetime.datetime.now,
        null=False)
    trip_to = models.BooleanField(
        verbose_name="Cesta do práce",
        null=False)
    trip_from = models.BooleanField(
        verbose_name="Cesta z práce",
        null=False)
    distance_to = models.IntegerField(
        verbose_name="Ujetá vzdálenost do práce",
        null=True, blank=True)
    distance_from = models.IntegerField(
        verbose_name="Ujetá vzdálenost z práce",
        null=True, blank=True)

class Competition(models.Model):
    """Závod"""

    CTYPES = (
        ('length', 'Ujetá vzdálenost'),
        ('frequency', 'Pravidelnost dojíždění'),
        ('questionnaire', 'Dotazník'),
        )

    CCOMPETITORTYPES = (
        ('single_user', 'Jednotlivý uživatelé'),
        ('team', 'Týmy'),
        ('company', 'Soutěž firem'),
        )

    class Meta:
        verbose_name = "Závod"
        verbose_name_plural = "Závody"
    name = models.CharField(
        unique=True,
        verbose_name="Jméno",
        max_length=40, null=False)
    type = models.CharField(
        verbose_name="Typ",
        choices=CTYPES,
        max_length=16,
        null=False)
    competitor_type = models.CharField(
        verbose_name="Typ závodníků",
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
        verbose_name = "Soutěž pouze pro město",
        null=True, 
        blank=True)
    company = models.ForeignKey(
        Company,
        verbose_name = "Soutěž pouze pro firmu",
        null=True, 
        blank=True)
    without_admission = models.BooleanField(
        verbose_name = "Soutěž bez přihlášek (pro všechny)",
        default=False,
        null=False)

    def __unicode__(self):
        return "%s" % self.name

class ChoiceType(models.Model):
    """Typ volby"""
    class Meta:
        verbose_name = "Typ volby"
        verbose_name_plural = "Typ volby"

    competition = models.ForeignKey(Competition,
        null=False,
        blank=False)
    name = models.CharField(
        verbose_name="Jméno",
        unique = True,
        max_length=40, null=True)
    universal = models.BooleanField(
        verbose_name="Typ volby je použitelný pro víc otázek",
        default=False)

    def __unicode__(self):
        return "%s" % self.name

class Question(models.Model):

    class Meta:
        verbose_name = "Anketní otázka"
        verbose_name_plural = "Anketní otázky"

    QTYPES = (
        ('text', 'Text'),
        ('choice', 'Výběr odpovědi'),
        ('multiple-choice', 'Výběr z více odpovědí'),
        )

    text = models.TextField(
        verbose_name="Otázka",
        max_length=500,
        null=False)
    date = models.DateField(
        verbose_name="Den",
        null=True, blank=True)
    type = models.CharField(
        verbose_name="Typ",
        choices=QTYPES,
        max_length=16,
        null=False)
    with_comment = models.BooleanField(
        verbose_name = "Povolit komentář",
        default=True,
        null=False)
    with_attachment = models.BooleanField(
        verbose_name = "Povolit přílohu",
        default=True,
        null=False)
    order = models.IntegerField(
        verbose_name="Pořadí",
        null=True, blank=True)
    competition = models.ForeignKey(
        Competition,
        verbose_name = "Soutěž",
        null=False, 
        blank=False)
    choice_type = models.ForeignKey(ChoiceType,
        null=False,
        blank=False)

    def __unicode__(self):
        return "%s" % self.text

class Choice(models.Model):
    
    class Meta:
        verbose_name = "Nabídka k anketním otázce"
        verbose_name_plural = "Nabídky k anketním otázkám"

    choice_type = models.ForeignKey(ChoiceType,
        verbose_name="Typ volby",
        related_name="choices",
        null=False,
        blank=False)
    text = models.CharField(
        verbose_name="Nabídka",
        max_length=300,
        null=False)
    points = models.IntegerField(
        verbose_name="Body",
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
        verbose_name="Komentář",
        max_length=600,
        null=True, blank=True)
    points_given = models.IntegerField(
        null=True, blank=True, default=0)

    def str_choices(self):
        return ", ".join([choice.text for choice in self.choices.all()])

    def __unicode__(self):
        return "%s" % self.str_choices()
