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
import django
import random
import string
import results
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db.models import Q
from django.core.exceptions import ValidationError
from composite_field import CompositeField
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator
# Python library imports
import datetime
# Local imports
import util
from dpnk.email import payment_confirmation_mail

class Address(CompositeField):
    street = models.CharField(
        verbose_name=_(u"Ulice"),
        help_text=_(u"Např. Šeříková nebo Nám. W. Churchilla"),
        default="",
        max_length=50,
        null=False,
        )
    street_number = models.CharField(
        verbose_name=_(u"Číslo domu"),
        help_text=_(u"Např. 2965/12 nebo 156"),
        default="",
        max_length=10,
        null=False,
        blank=False,
        )
    recipient = models.CharField(
        verbose_name=_(u"Název pobočky (závodu, kanceláře, fakulty)"),
        help_text=_(u"Např. odštěpný závod Brno, oblastní pobočka Liberec, Přírodovědecká fakulta atp."),
        default="",
        max_length=50,
        null=False,
        blank=False,
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
        help_text=_(u"Např.: 13000"),
        validators=[
            MaxValueValidator(99999),
            MinValueValidator(10000)
        ],
        default=0,
        null=False,
        blank=False,
        )
    city = models.CharField(
        verbose_name=_(u"Město"),
        help_text=_(u"Např. Jablonec n.N. nebo Praha 3-Žižkov"),
        default="",
        max_length=50,
        null=False,
        blank=False,
        )

    def __unicode__(self):
        return "%s, %s %s, %s, %s" % (self.recipient, self.street, self.street_number, self.psc, self.city)

class City(models.Model):
    """Město"""

    class Meta:
        verbose_name = _(u"Město")
        verbose_name_plural = _(u"Města")
    name = models.CharField(
        verbose_name=_(u"Jméno"),
        unique=True,
        max_length=40, null=False)
    slug = models.SlugField(
        unique=True,
        verbose_name=u"Subdoména v URL",
        blank=False
        )
    city_admins = models.ManyToManyField(
        'UserProfile',
        related_name = "administrated_cities",
        null=True,
        blank=True)
    admission_fee = models.PositiveIntegerField(
        verbose_name=_(u"Startovné"),
        null=False,
        default=160)

    def __unicode__(self):
        return "%s" % self.name

class Company(models.Model):
    """Firma"""

    class Meta:
        verbose_name = _(u"Firma")
        verbose_name_plural = _(u"Firmy")
        ordering = ('name',)

    name = models.CharField(
        unique=True,
        verbose_name=_(u"Název organizace"),
        help_text=_(u"Např. Výrobna, a.s., Příspěvková, p.o., Nevládka, o.s., Univerzita Karlova"),
        max_length=60, null=False)
    company_admin = models.OneToOneField(
        "UserProfile", 
        related_name = "administrated_company",
        verbose_name = _(u"Firemní správce"),
        null=True,
        blank=True)
    invoice_address = Address()
    ico = models.PositiveIntegerField(
        default=0,
        verbose_name=_(u"IČO"),
        null=False)

    def __unicode__(self):
        return "%s" % self.name

class Subsidiary(models.Model):
    """Pobočka"""

    class Meta:
        verbose_name = _(u"Pobočka")
        verbose_name_plural = _(u"Pobočky")

    address = Address()
    company = models.ForeignKey(
          Company, 
          related_name="subsidiaries",
          null=False, 
          blank=False)
    city = models.ForeignKey(
          City, 
          verbose_name=_(u"Soutěžní město"),
          help_text=_(u"Rozhoduje o tom, kde budete soutěžit - vizte <a href='http://www.dopracenakole.net/chci-slapat/pravidla-souteze/' target='_blank'>pravidla soutěže</a>"),
          null=False, blank=False)

    def __unicode__(self):
        return "%s, %s %s, %s, %s" % (self.address.recipient, self.address.street, self.address.street_number, self.address.psc, self.address.city)

def validate_length(value,min_length=25):
    str_len = len(str(value))
    if str_len<min_length:
        raise ValidationError(_(u"The string should be longer than %(min)s, but is %(max)s characters long") % {'min': min_length, 'max': str_len})

class Team(models.Model):
    """Profil týmu"""

    class Meta:
        verbose_name = _(u"Tým")
        verbose_name_plural = _(u"Týmy")
        ordering = ('name',)

    name = models.CharField(
        verbose_name=_(u"Název týmu"),
        max_length=50, null=False,
        unique=True)
    subsidiary = models.ForeignKey(
        Subsidiary,
        verbose_name=_(u"Pobočka"),
        related_name='teams',
        null=False,
        blank=False)
    coordinator = models.OneToOneField(
        'UserProfile',
        related_name = "coordinated_team",
        verbose_name = _(u"Koordinátor/ka týmu"),
        null=True,
        blank=True,
        #TODO:
        #null=False,
        #blank=False,
        unique=True,
        )
    invitation_token = models.CharField(
        verbose_name=_(u"Token pro pozvánky"),
        default="",
        max_length=100,
        null=False,
        blank=False,
        unique=True,
        validators = [validate_length],
        )
    def members(self):
        return UserProfile.objects.filter(approved_for_team='approved', team=self, user__is_active=True)

    def __unicode__(self):
        return "%s / %s" % (self.name, self.subsidiary.company)

    def save(self, force_insert=False, force_update=False):
        if self.coordinator_id is not None and self.coordinator is not None and self.coordinator.team.id != self.id:
            raise Exception(_(u"Nový koordinátor %(coordinator)s není členem týmu %(team)s") % {'coordinator': self.coordinator, 'team': self})

        if self.invitation_token == "":
            while True:
                invitation_token = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(30))
                if not Team.objects.filter(invitation_token = invitation_token).exists():
                    self.invitation_token = invitation_token
                    break

        super(Team, self).save(force_insert, force_update)

class UserProfile(models.Model):
    """Uživatelský profil"""

    class Meta:
        verbose_name = _(u"Uživatel")
        verbose_name_plural = _(u"Uživatelé")

    TSHIRTSIZE = [
              ('wXXS', _(u"dámské XXS")),
              ('wXS', _(u"dámské XS")),
              ('wS', _(u"dámské S")),
              ('wM', _(u"dámské M")),
              ('wL', _(u"dámské L")),
              ('wXL', _(u"dámské XL")),
              ('wXXL', _(u"dámské XXL")),

              ('mS', _(u"pánské S")),
              ('mM', _(u"pánské M")),
              ('mL', _(u"pánské L")),
              ('mXL', _(u"pánské XL")),
              ('mXXL', _(u"pánské XXL")),
              ]

    TEAMAPPROVAL = (('approved', _(u"Odsouhlasený")),
              ('undecided', _(u"Nerozhodnuto")),
              ('denied', _(u"Zamítnutý")),
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
    distance = models.PositiveIntegerField(
        verbose_name=_(u"Vzdálenost"),
        null=False)
    # -- Contacts
    telephone = models.CharField(
        verbose_name=_(u"Telefon"),
        max_length=30, null=False)
    team = models.ForeignKey(
        Team,
        related_name='users',
        verbose_name=_(u"Tým"),
        null=True, blank=True)
    company_admin_unapproved = models.BooleanField(
        verbose_name=_(u"Správcovství organizace není schváleno"),
        default=True)
    approved_for_team = models.CharField(
        verbose_name=_(u"Souhlas týmu"),
        choices=TEAMAPPROVAL,
        max_length=16,
        null=False,
        default='undecided')
    language = models.CharField(
        verbose_name=_(u"Jazyk komunikace"),
        choices=LANGUAGE,
        max_length=16,
        null=False,
        default='cs')
    t_shirt_size = models.CharField(
        verbose_name=_(u"Velikost trička"),
        choices=TSHIRTSIZE,
        max_length=16,
        null=False,
        default='L')
    motivation_company_admin = models.TextField(
        verbose_name=_(u"Zaměstnanecká pozice"),
        help_text=_(u"Napište nám prosím, jakou zastáváte u Vašeho zaměstnavatele pozici"),
        default="",
        max_length=5000,
        null=True,
        blank=True,
        )
    mailing_id = models.TextField(
        verbose_name=_(u"ID uživatele v mailing listu"),
        default="",
        null=True,
        blank=True
        )

    def first_name(self):
        return user.first_name

    def last_name(self):
        return user.last_name

    def __unicode__(self):
        return self.user.get_full_name()

    def payment_status(self):
        if self.team and self.team.subsidiary and self.team.subsidiary.city.admission_fee == 0:
            return 'no_admission'

        # Check payment status for this user
        payments = Payment.objects.filter(user=self)
        p_status = [p.status for p in payments]
        if len(set([Payment.Status.DONE,
                   Payment.Status.COMPANY_ACCEPTS,
                   Payment.Status.INVOICE_MADE,
                   Payment.Status.INVOICE_PAID])
               & set(p_status)):
            # Payment done
            status = 'done'
        elif len(set([Payment.Status.NEW,
                     Payment.Status.COMMENCED,
                     Payment.Status.WAITING_CONFIRMATION])
                 & set(p_status)):
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

    def get_competitions(self):
        return results.get_competitions_with_info(self)

    def has_distance_dompetition(self):
        return results.has_distance_dompetition(self)

    def get_competitions_for_admission(self):
        return results.get_competitions_for_admission(self)
    
    def is_team_coordinator(self):
        return self.team and self.team.coordinator == self
    
    def is_company_admin(self):
        return not self.company_admin_unapproved

@receiver(pre_save, sender=UserProfile)
def set_team_coordinator_pre(sender, instance, **kwargs):
    if hasattr(instance, "coordinated_team") and instance.coordinated_team != instance.team:
        instance.coordinated_team.coordinator = None
        instance.coordinated_team.save()

@receiver(post_save, sender=UserProfile)
def set_team_coordinator_post(sender, instance, created, **kwargs):
    if instance.team and instance.team.coordinator == None:
        instance.team.coordinator = instance
        instance.team.save()

class UserProfileUnpaidManager(models.Manager):
    def get_query_set(self):
        paying_or_prospective_user_ids = [p.user_id for p in Payment.objects.filter(
                Q(status=Payment.Status.DONE) | Q (
                    # Bank transfer less than 5 days old
                    status=Payment.Status.NEW, pay_type='bt',
                    created__gt=datetime.datetime.now() - datetime.timedelta(days=5))
                )]
        return super(UserProfileUnpaidManager,self).get_query_set().filter(
            user__is_active=True).exclude(id__in=paying_or_prospective_user_ids)

    

class UserProfileUnpaid(UserProfile):
    objects = UserProfileUnpaidManager()
    class Meta:
        proxy = True
        verbose_name = _(u"Soutěžící, co dosud nezaplatil startovné")
        verbose_name_plural = _(u"Soutěžící, co dosud nezaplatili startovné")

class Payment(models.Model):
    """Platba"""

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
        
    STATUS = (
        (Status.NEW, 'Nová'),
        (Status.CANCELED, 'Zrušena'),
        (Status.REJECTED, 'Odmítnuta'),
        (Status.COMMENCED, 'Zahájena'),
        (Status.WAITING_CONFIRMATION, 'Očekává potvrzení'),
        (Status.REJECTED, 'Platba zamítnuta, prostředky nemožno vrátit, řeší PayU'),
        (Status.DONE, 'Přijata'),
        (Status.WRONG_STATUS, 'Nesprávný status -- kontaktovat PayU'),
        (Status.COMPANY_ACCEPTS, 'Firma akceptuje platbu'),
        (Status.INVOICE_MADE, 'Faktura vystavena'),
        (Status.INVOICE_PAID, 'Faktura zaplacena'),
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
        verbose_name = _(u"Platba")
        verbose_name_plural = _(u"Platby")

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
        verbose_name=_(u"Částka"),
        null=False)
    description = models.CharField(
        verbose_name=_(u"Popis"),
        max_length=500,
        null=True,
        blank=True,
        default="")
    created = models.DateTimeField(
        verbose_name=_(u"Zadání platby"),
        default=datetime.datetime.now,
        null=False)
    realized = models.DateTimeField(
        verbose_name=_(u"Realizace"),
        null=True, blank=True)
    pay_type = models.CharField(
        verbose_name=_(u"Typ platby"),
        choices=PAY_TYPES,
        max_length=50,
        null=True, blank=True)
    status = models.PositiveIntegerField(
        verbose_name=_(u"Status"),
        choices=STATUS,
        default=Status.NEW,
        max_length=50,
        null=True, blank=True)
    error = models.PositiveIntegerField(
        verbose_name=_(u"Chyba"),
        null=True, blank=True)
    company_wants_to_pay = models.BooleanField(
        verbose_name=_(u"Firma chce zaplatit"),
        default=False)

    def save(self, *args, **kwargs):
        status_before_update = None
        if self.id:
            status_before_update = Payment.objects.get(pk=self.id).status
        super(Payment, self).save(*args, **kwargs)

        if (self.user
            and (status_before_update != Payment.Status.DONE)
            and self.status == Payment.Status.DONE):
            payment_confirmation_mail(self.user.user)

    def __unicode__(self):
        if self.trans_id:
            return self.trans_id
        else:
            return self.session_id

class Voucher(models.Model):
    """Slevove kupony"""

    class Meta:
        verbose_name = _(u"Kupon")
        verbose_name_plural = _(u"Kupony")

    code = models.CharField(
        verbose_name=_(u"Kód"),
        max_length=20, null=False)
    user = models.ForeignKey(UserProfile, null=True, blank=True)

class Trip(models.Model):
    """Cesty"""

    class Meta:
        verbose_name = _(u"Cesta")
        verbose_name_plural = _(u"Cesty")

    user = models.ForeignKey(
        UserProfile, 
        related_name="user_trips",
        null=True,
        blank=True)
    date = models.DateField(
        verbose_name=_(u"Datum cesty"),
        default=datetime.datetime.now,
        null=False)
    trip_to = models.BooleanField(
        verbose_name=_(u"Cesta do práce"),
        null=False)
    trip_from = models.BooleanField(
        verbose_name=_(u"Cesta z práce"),
        null=False)
    distance_to = models.IntegerField(
        verbose_name=_(u"Ujetá vzdálenost do práce"),
        null=True, blank=True)
    distance_from = models.IntegerField(
        verbose_name=_(u"Ujetá vzdálenost z práce"),
        null=True, blank=True)

class Competition(models.Model):
    """Závod"""

    CTYPES = (
        ('length', _(u"Ujetá vzdálenost")),
        ('frequency', _(u"Pravidelnost jízd na kole")),
        ('questionnaire', _(u"Dotazník")),
        )

    CCOMPETITORTYPES = (
        ('single_user', _(u"Jednotliví soutěžící")),
        ('team', _(u"Týmy")),
        ('company', _(u"Soutěž firem")),
        )

    class Meta:
        verbose_name = _(u"Závod")
        verbose_name_plural = _(u"Závody")
    name = models.CharField(
        unique=True,
        verbose_name=_(u"Jméno"),
        max_length=40, null=False)
    slug = models.SlugField(
        unique=True,
        default="",
        verbose_name=u"Doména v URL",
        blank=False
        )
    url = models.URLField(
        default="",
        verbose_name=u"Odkaz na stránku závodu",
        null=True, 
        blank=True,
        )
    date_from = models.DateField(
        verbose_name=_(u"Datum začátku soutěže"),
        help_text=_(u"Po tomto datu nebude možné se do soutěže přihlásit"),
        default=datetime.date(2013, 5, 1),
        null=False, blank=False)
    date_to = models.DateField(
        verbose_name=_(u"Datum konce soutěže"),
        help_text=_(u"Po tomto datu nebude možné soutěžit (vyplňovat dotazník)"),
        default=datetime.date(2013, 5, 31),
        null=False, blank=False)
    type = models.CharField(
        verbose_name=_(u"Typ"),
        choices=CTYPES,
        max_length=16,
        null=False)
    competitor_type = models.CharField(
        verbose_name=_(u"Typ závodníků"),
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
        verbose_name = _(u"Soutěž pouze pro město"),
        null=True, 
        blank=True)
    company = models.ForeignKey(
        Company,
        verbose_name = _(u"Soutěž pouze pro firmu"),
        null=True, 
        blank=True)
    without_admission = models.BooleanField(
        verbose_name = _(u"Soutěž bez přihlášek (pro všechny)"),
        default=True,
        null=False)

    def get_competitors(self):
        return results.get_competitors(self)

    def get_results(self):
        return results.get_results(self)

    def has_admission(self, userprofile):
        if self.without_admission:
            return True
        else:
            if self.competitor_type == 'single_user':
                return self.user_competitors.filter(pk=userprofile.pk).count() > 0
            elif self.competitor_type == 'team':
                return self.team_competitors.filter(pk=userprofile.team.pk).count() > 0
            elif self.competitor_type == 'company':
                return self.company_competitors.filter(pk=userprofile.company.pk).count() > 0

    def make_admission(self, userprofile, admission=True):
        if not self.without_admission:
            if self.competitor_type == 'single_user':
                if admission:
                    self.user_competitors.add(userprofile)
                else:
                    self.user_competitors.remove(userprofile)
            elif self.competitor_type == 'team':
                if admission:
                    self.team_competitors.add(userprofile.team)
                else:
                    self.team_competitors.remove(userprofile.team)
            elif self.competitor_type == 'company':
                if admission:
                    self.company_competitors.add(userprofile.team.subsidiary.company)
                else:
                    self.company_competitors.remove(userprofile.team.subsidiary.company)

    def __unicode__(self):
        return "%s" % self.name

class ChoiceType(models.Model):
    """Typ volby"""
    class Meta:
        verbose_name = _(u"Typ volby")
        verbose_name_plural = _(u"Typ volby")
        unique_together = (("competition", "name"),)

    competition = models.ForeignKey(Competition,
        null=False,
        blank=False)
    name = models.CharField(
        verbose_name=_(u"Jméno"),
        unique = True,
        max_length=40, null=True)
    universal = models.BooleanField(
        verbose_name=_(u"Typ volby je použitelný pro víc otázek"),
        default=False)

    def __unicode__(self):
        return "%s" % self.name

class Question(models.Model):

    class Meta:
        verbose_name = _(u"Anketní otázka")
        verbose_name_plural = _(u"Anketní otázky")

    QTYPES = (
        ('text', _(u"Text")),
        ('choice', _(u"Výběr odpovědi")),
        ('multiple-choice', _(u"Výběr z více odpovědí")),
        )

    text = models.TextField(
        verbose_name=_(u"Otázka"),
        max_length=500,
        null=False)
    date = models.DateField(
        verbose_name=_(u"Den"),
        null=True, blank=True)
    type = models.CharField(
        verbose_name=_(u"Typ"),
        choices=QTYPES,
        max_length=16,
        null=False)
    with_comment = models.BooleanField(
        verbose_name = _(u"Povolit komentář"),
        default=True,
        null=False)
    with_attachment = models.BooleanField(
        verbose_name = _(u"Povolit přílohu"),
        default=True,
        null=False)
    order = models.IntegerField(
        verbose_name=_(u"Pořadí"),
        null=True, blank=True)
    competition = models.ForeignKey(
        Competition,
        verbose_name = _(u"Soutěž"),
        null=False, 
        blank=False)
    choice_type = models.ForeignKey(ChoiceType,
        null=False,
        blank=False)

    def __unicode__(self):
        return "%s" % self.text

class Choice(models.Model):
    
    class Meta:
        verbose_name = _(u"Nabídka k anketním otázce")
        verbose_name_plural = _(u"Nabídky k anketním otázkám")

    choice_type = models.ForeignKey(ChoiceType,
        verbose_name=_(u"Typ volby"),
        related_name="choices",
        null=False,
        blank=False)
    text = models.CharField(
        verbose_name=_(u"Nabídka"),
        max_length=300,
        null=False)
    points = models.IntegerField(
        verbose_name=_(u"Body"),
        null=True, 
        blank=True, 
        default=None,
        )

    def __unicode__(self):
        return "%s" % self.text

class Answer(models.Model):
    user = models.ForeignKey(UserProfile, null=True, blank=True)
    question = models.ForeignKey(Question, null=False)
    choices = models.ManyToManyField(Choice)
    comment = models.TextField(
        verbose_name=_(u"Komentář"),
        max_length=600,
        null=True, blank=True)
    points_given = models.IntegerField(
        null=True, blank=True, default=None)

    def str_choices(self):
        return ", ".join([choice.text for choice in self.choices.all()])

    def __unicode__(self):
        return "%s" % self.str_choices()
