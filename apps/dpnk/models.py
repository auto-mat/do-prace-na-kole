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
from author.decorators import with_author
from django import forms
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from fieldsignals import post_save_changed, pre_save_changed
from django.dispatch import receiver
from django.db.models import Q, Sum
from django.core.exceptions import ValidationError
from composite_field import CompositeField
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator
from django.conf import settings
from polymorphic import PolymorphicModel
# Python library imports
import datetime
# Local imports
import util
import mailing
from dpnk.email import payment_confirmation_mail, company_admin_rejected_mail, company_admin_approval_mail, payment_confirmation_company_mail
from dpnk import email
from wp_urls import wp_reverse
import logging
logger = logging.getLogger(__name__)

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
        verbose_name=_(u"Název společnosti (pobočky, závodu, kanceláře, fakulty) na adrese"),
        help_text=_(u"Např. odštěpný závod Brno, oblastní pobočka Liberec, Přírodovědecká fakulta atp."),
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
        ordering = ('name',)

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

    def __unicode__(self):
        return "%s" % self.name


class CityInCampaign(models.Model):
    """Město v kampani"""

    class Meta:
        verbose_name = _(u"Město v kampani")
        verbose_name_plural = _(u"Města v kampani")
        unique_together = (("city", "campaign"),)
        ordering = ('city__name',)

    admission_fee = models.PositiveIntegerField(
        verbose_name=_(u"Startovné"),
        null=False,
        default=160)
    city = models.ForeignKey(
          City, 
          null=False, 
          blank=False)
    campaign = models.ForeignKey(
          "Campaign", 
          null=False, 
          blank=False)

    def __unicode__(self):
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
        help_text=_(u"Např. Výrobna, a.s., Příspěvková, p.o., Nevládka, o.s., Univerzita Karlova"),
        max_length=60, null=False)
    address = Address()
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
          help_text=_(u"Rozhoduje o tom, kde budete soutěžit - vizte <a href='%s' target='_blank'>pravidla soutěže</a>") % wp_reverse('pravidla'),
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
    coordinator_campaign = models.OneToOneField(
        'UserAttendance',
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
    campaign = models.ForeignKey(
          "Campaign", 
          verbose_name=_(u"Kampaň"),
          null=False, blank=False)

    #Auto fields:
    member_count = models.IntegerField(
        verbose_name=_(u"Počet právoplatných členů týmu"),
        null=False,
        blank=False,
        default=0,
        )

    def autoset_member_count(self):
        self.member_count = self.members().count()
    def all_members(self, campaign):
        return UserAttendance.objects.filter(campaign=campaign, team=self, userprofile__user__is_active=True)

    def members(self):
        return UserAttendance.objects.filter(approved_for_team='approved', team=self, userprofile__user__is_active=True)

    def get_frequency(self):
        return results.get_team_frequency(self)

    def get_length(self):
        return results.get_team_length(self)

    def __unicode__(self):
        return "%s / %s (%s)" % (self.name, self.subsidiary.company, self.member_count)

    def save(self, force_insert=False, force_update=False):
        if self.coordinator_campaign_id is not None and self.coordinator_campaign is not None and self.coordinator_campaign.team.id != self.id:
            raise Exception(_(u"Nový koordinátor %(coordinator)s není členem týmu %(team)s") % {'coordinator': self.coordinator_campaign, 'team': self})

        if self.invitation_token == "":
            while True:
                invitation_token = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(30))
                if not Team.objects.filter(invitation_token = invitation_token).exists():
                    self.invitation_token = invitation_token
                    break

        super(Team, self).save(force_insert, force_update)


class TeamForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TeamForm, self).__init__(*args, **kwargs)
        self.fields['coordinator_campaign'].queryset = UserAttendance.objects.filter(team=self.instance, approved_for_team='approved')


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

    def __unicode__(self):
        return self.name

class Phase(models.Model):
    """fáze kampaně"""

    class Meta:
        verbose_name = _(u"fáze kampaně")
        verbose_name_plural = _(u"fáze kampaně")
        unique_together = (("type", "campaign"),)

    TYPE = [('registration', _(u"registrační")),
            ('competition', _(u"soutěžní")),
            ('results', _(u"výsledková")),
            ]

    TYPE_DICT = dict(TYPE)

    campaign = models.ForeignKey(
       Campaign, 
       verbose_name = _(u"Kampaň"),
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
        if self.date_from == None:
            return True
        return self.date_from <= util.today()

    def has_finished(self):
        if self.date_to == None:
            return True
        return not self.date_to >= util.today()

    def is_actual(self):
        return self.has_started() and not self.has_finished()

    
class TShirtSize(models.Model):
    """Velikost trička"""

    name = models.CharField(
        verbose_name=_(u"Velikost"),
        max_length=40, null=False)
    campaign = models.ForeignKey(
       Campaign, 
       verbose_name = _(u"Kampaň"),
       null=False,
       blank=False)
    order = models.PositiveIntegerField(
            default=0,
            blank=False,
            null=False,
            )

    class Meta:
        verbose_name = _(u"Velikost trička")
        verbose_name_plural = _(u"Velikosti trička")
        unique_together = (("name", "campaign"),)
        ordering = [ "order" ]

    def __unicode__(self):
        return self.name

class UserAttendanceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserAttendanceForm, self).__init__(*args, **kwargs)
        self.fields['t_shirt_size'].queryset = TShirtSize.objects.filter(campaign=self.instance.campaign)


class UserAttendance(models.Model):
    """Účast uživatele v kampani"""

    class Meta:
        verbose_name = _(u"Účast v kampani")
        verbose_name_plural = _(u"Účasti v kampani")
        unique_together = (("userprofile", "campaign"),)

    TEAMAPPROVAL = (('approved', _(u"Odsouhlasený")),
              ('undecided', _(u"Nerozhodnuto")),
              ('denied', _(u"Zamítnutý")),
              )

    campaign = models.ForeignKey(
       Campaign, 
       verbose_name = _(u"Kampaň"),
       null=False,
       blank=False)
    userprofile = models.ForeignKey(
       "UserProfile", 
       verbose_name = _(u"Uživatelský profil"),
       unique=False,
       null=False,
       blank=False)
    distance = models.PositiveIntegerField(
        verbose_name=_(u"Vzdálenost"),
        help_text=_(u"Průměrná ujetá vzdálenost z domova do práce (v km v jednom směru)"),
        default=None,
        blank=True,
        null=True)
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
        blank=False,
        )

    def payments(self):
        return self.transactions.instance_of(Payment)

    def first_name(self):
        return self.userprofile.user.first_name

    def last_name(self):
        return self.userprofile.user.last_name

    def __unicode__(self):
        return self.userprofile.user.get_full_name()

    def admission_fee(self):
        return self.team.subsidiary.city.cityincampaign_set.get(campaign=self.campaign).admission_fee

    def payment(self):
        if self.team and self.team.subsidiary and self.admission_fee() == 0:
            return {'payment': None,
                    'status': 'no_admission',
                    'status_description': _(u'neplatí se'),
                    'class': _(u'success'),
                   }

        payments = self.payments().filter(status__in = Payment.done_statuses)
        if payments.exists():
            return {'payment': payments.latest('id'),
                    'status': 'done',
                    'status_description': _(u'zaplaceno'),
                    'class': _(u'success'),
                   }

        payments = self.payments().filter(status__in = Payment.waiting_statuses)
        if payments.exists():
            return {'payment': payments.latest('id'),
                    'status': 'waiting',
                    'status_description': _(u'nepotvrzeno'),
                    'class': _(u'warning'),
                   }

        payments = self.payments()
        if payments.exists():
            return {'payment': payments.latest('id'),
                    'status': 'unknown',
                    'status_description': _(u'neznámý'),
                    'class': _(u'warning'),
                   }

        return {'payment': None,
                'status': 'none',
                'status_description': _(u'žádné platby'),
                'class': _(u'error'),
               }

    def payment_status(self):
        return self.payment()['status']

    def payment_type(self):
        payment = self.payment()['payment']
        if payment:
            return payment.pay_type
        else:
            return None

    def get_competitions(self):
        return results.get_competitions_with_info(self)

    def has_distance_competition(self):
        return results.has_distance_competition(self)

    def get_frequency(self):
        return results.get_userprofile_frequency(self)

    def get_rough_length(self):
        return results.get_userprofile_frequency(self) * self.distance

    def get_length(self):
        return results.get_userprofile_length(self)

    def is_libero(self):
        if self.team:
            return self.team.members().count() <= 1
        else:
            return False

    def other_user_attendances(self, campaign):
        return self.userprofile.userattendance_set.exclude(campaign=campaign)


class UserProfile(models.Model):
    """Uživatelský profil"""

    class Meta:
        verbose_name = _(u"Uživatel")
        verbose_name_plural = _(u"Uživatelé")
        ordering = [ "user__last_name", "user__first_name" ]

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
    telephone = models.CharField(
        verbose_name=_(u"Telefon"),
        max_length=30, null=False)
    language = models.CharField(
        verbose_name=_(u"Jazyk komunikace"),
        choices=LANGUAGE,
        max_length=16,
        null=False,
        default='cs')
    mailing_id = models.CharField(
        verbose_name=_(u"ID uživatele v mailing listu"),
        max_length = 128,
        db_index=True,
        default=None,
        #TODO:
        #unique=True,
        null=True,
        blank=True
        )

    def first_name(self):
        return self.user.first_name

    def last_name(self):
        return self.user.last_name

    def __unicode__(self):
        return self.user.get_full_name()

    def save(self, force_insert=False, force_update=False):
        if self.mailing_id and UserProfile.objects.exclude(pk=self.pk).filter(mailing_id=self.mailing_id).count() > 0:
            logger.error(_(u"Mailing id %s is already used") % self.mailing_id)
        super(UserProfile, self).save(force_insert, force_update)

@receiver(pre_save, sender=UserAttendance)
def set_team_coordinator_pre(sender, instance, **kwargs):
    if hasattr(instance, "coordinated_team") and instance.coordinated_team != instance.team:
        coordinated_team = instance.coordinated_team
        coordinated_team.coordinator_campaign = None
        coordinated_team.save()

@receiver(post_save, sender=UserAttendance)
def set_team_coordinator_post(sender, instance, created, **kwargs):
    if instance.team and instance.team.coordinator_campaign == None:
        instance.team.coordinator_campaign = instance
        instance.team.save()

class CompanyAdmin(models.Model):
    """Profil firemního administrátora"""

    COMPANY_APPROVAL = (('approved', _(u"Odsouhlasený")),
              ('undecided', _(u"Nerozhodnuto")),
              ('denied', _(u"Zamítnutý")),
              )

    class Meta:
        verbose_name = _(u"Firemní administrátor")
        verbose_name_plural = _(u"Firemní administrátoři")
        unique_together = (
                ("user", "campaign"),
                ("administrated_company", "campaign"),
                )

    user = models.ForeignKey(
        User,
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
       related_name = "company_admin",
       verbose_name = _(u"Administrovaná společnost"),
       null=True,
       blank=True)

    campaign = models.ForeignKey(
       Campaign, 
       null=False,
       blank=False)

    def __unicode__(self):
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
class Transaction(PolymorphicModel):
    """Transakce"""
    status = models.PositiveIntegerField(
        verbose_name=_(u"Status"),
        max_length=50,
        default=0,
        null=False, blank=False)
    user_attendance = models.ForeignKey(UserAttendance, 
        related_name="transactions",
        null=True, 
        blank=False, 
        default=None)
    created = models.DateTimeField(
        verbose_name=_(u"Vytvoření"),
        default=datetime.datetime.now,
        null=False)
    description = models.CharField(
        verbose_name=_(u"Popis"),
        max_length=500,
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

    class Status (object):
        BIKE_REPAIR = 40001

    STATUS = (
        (Status.BIKE_REPAIR, 'Oprava v cykloservisu'),
        )

    class Meta:
        verbose_name = _(u"Obecná transakce")
        verbose_name_plural = _(u"Obecné transakce")


class CommonTransactionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CommonTransactionForm, self).__init__(*args, **kwargs)
        self.fields['status'] = forms.ChoiceField(choices=CommonTransaction.STATUS)

    class Meta:
        model = CommonTransaction


class UserActionTransaction(Transaction):
    """Uživatelská akce"""

    class Status (object):
        COMPETITION_START_CONFIRMED = 30002
        
    STATUS = (
        (Status.COMPETITION_START_CONFIRMED, 'Potvrzen vstup do soutěže'),
        )

    class Meta:
        verbose_name = _(u"Uživatelská akce")
        verbose_name_plural = _(u"Uživatelské akce")

class UserActionTransactionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserActionTransactionForm, self).__init__(*args, **kwargs)
        self.fields['status'] = forms.ChoiceField(choices=UserActionTransaction.STATUS)

    class Meta:
        model = UserActionTransaction


class PackageTransaction(Transaction):
    """Transakce balíku"""

    class Status (object):
        PACKAGE_ACCEPTED_FOR_ASSEMBLY = 20002
        PACKAGE_ASSEMBLED = 20003
        PACKAGE_SENT = 20004
        PACKAGE_DELIVERY_CONFIRMED = 20005
        
    STATUS = (
        (Status.PACKAGE_ACCEPTED_FOR_ASSEMBLY, 'Přijat k sestavení'),
        (Status.PACKAGE_ASSEMBLED, 'Sestaven'),
        (Status.PACKAGE_SENT, 'Odeslán'),
        (Status.PACKAGE_DELIVERY_CONFIRMED, 'Doručení potvrzeno'),
        )

    class Meta:
        verbose_name = _(u"Transakce balíku")
        verbose_name_plural = _(u"Transakce balíku")


class PackageTransactionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PackageTransactionForm, self).__init__(*args, **kwargs)
        self.fields['status'] = forms.ChoiceField(choices=PackageTransaction.STATUS)

    class Meta:
        model = PackageTransaction


class Payment(Transaction):
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
        (Status.DONE, 'Platba přijata'),
        (Status.WRONG_STATUS, 'Nesprávný status -- kontaktovat PayU'),
        (Status.COMPANY_ACCEPTS, 'Platba akceptována firmou'),
        (Status.INVOICE_MADE, 'Faktura vystavena'),
        (Status.INVOICE_PAID, 'Faktura zaplacena'),
        )

    done_statuses = [Status.DONE,
        Status.COMPANY_ACCEPTS,
        Status.INVOICE_MADE,
        Status.INVOICE_PAID]
    waiting_statuses = [Status.NEW,
        Status.COMMENCED,
        Status.WAITING_CONFIRMATION]

    PAY_TYPES = (
        ('mp', 'mPenize'),
        ('kb', 'MojePlatba'),
        ('rf', 'ePlatby pro eKonto'),
        ('pg', 'GE Money Bank'),
        ('pv', 'Volksbank'),
        ('pf', 'Fio banka'),
        ('cs', 'Česká spořitelna'),
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
        null=True,
        blank=True,
        default="")
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

    def save(self, *args, **kwargs):
        status_before_update = None
        if self.id:
            status_before_update = Payment.objects.get(pk=self.id).status
            logger.info(u"Saving payment (before): %s" % Payment.objects.get(pk=self.id).full_string())
        super(Payment, self).save(*args, **kwargs)

        statuses_company_ok = (Payment.Status.COMPANY_ACCEPTS, Payment.Status.INVOICE_MADE, Payment.Status.INVOICE_PAID)
        if (self.user_attendance
            and (status_before_update != Payment.Status.DONE)
            and self.status == Payment.Status.DONE):
            payment_confirmation_mail(self.user_attendance.userprofile.user)
        elif (self.user_attendance
            and (status_before_update not in statuses_company_ok)
            and self.status in statuses_company_ok):
            payment_confirmation_company_mail(self.user_attendance)

        logger.info(u"Saving payment (after):  %s" % Payment.objects.get(pk=self.id).full_string())

    def full_string(self):
        if self.user_attendance:
            user = self.user_attendance
        else:
            user = None
        return u"user: %s, order_id: %s, session_id: %s, trans_id: %s, amount: %s, description: %s, created: %s, realized: %s, pay_type: %s, status: %s, error: %s" % (
            user, self.order_id, self.session_id, self.trans_id, self.amount, self.description, self.created, self.realized, self.pay_type, self.status, self.error) 

    def __unicode__(self):
        if self.trans_id:
            return self.trans_id
        else:
            return self.session_id


class PaymentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        self.fields['status'] = forms.ChoiceField(choices=Payment.STATUS)

    class Meta:
        model = Payment


class Trip(models.Model):
    """Cesty"""

    class Meta:
        verbose_name = _(u"Cesta")
        verbose_name_plural = _(u"Cesty")
        unique_together = (("user_attendance", "date"),)

    user_attendance = models.ForeignKey(
        UserAttendance, 
        related_name="user_trips",
        null=True,
        blank=True,
        default=None)
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
        null=True,
        blank=True,
        default=None,
        )
    distance_from = models.IntegerField(
        verbose_name=_(u"Ujetá vzdálenost z práce"),
        null=True,
        blank=True,
        default=None,
        )

class Competition(models.Model):
    """Soutěž"""

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
        verbose_name = _(u"Soutěž")
        verbose_name_plural = _(u"Soutěže")
    name = models.CharField(
        unique=True,
        verbose_name=_(u"Jméno soutěže"),
        max_length=40, null=False)
    campaign = models.ForeignKey(
       Campaign, 
       verbose_name = _(u"Kampaň"),
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
        null=True, 
        blank=True,
        )
    date_from = models.DateField(
        verbose_name=_(u"Datum začátku soutěže"),
        help_text=_(u"Po tomto datu nebude možné se do soutěže přihlásit"),
        default=None,
        null=False, blank=False)
    date_to = models.DateField(
        verbose_name=_(u"Datum konce soutěže"),
        help_text=_(u"Po tomto datu nebude možné soutěžit (vyplňovat dotazník)"),
        default=None,
        null=False, blank=False)
    type = models.CharField(
        verbose_name=_(u"Typ"),
        choices=CTYPES,
        max_length=16,
        null=False)
    competitor_type = models.CharField(
        verbose_name=_(u"Typ soutěžícího"),
        choices=CCOMPETITORTYPES,
        max_length=16,
        null=False)
    user_attendance_competitors = models.ManyToManyField(
        UserAttendance,
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
    is_public = models.BooleanField(
        verbose_name = _(u"Soutěž je veřejná"),
        default=True,
        null=False)

    def get_competitors(self):
        return results.get_competitors(self)

    def get_results(self):
        return results.get_results(self)

    def has_started(self):
        return self.date_from <= util.today()

    def has_finished(self):
        return not self.date_to >= util.today()

    def is_actual(self):
        return self.has_started() and not self.has_finished()

    def recalculate_results(self):
        return results.recalculate_result_competition(self)

    def can_admit(self, user_attendance):
        if self.without_admission:
            return 'without_admission'
        if not is_team_coordinator(user_attendance) and self.competitor_type == 'team':
            return 'not_team_coordinator'
        if not get_company_admin(user_attendance.userprofile.user, self.campaign) and self.competitor_type == 'company':
            return 'not_company_admin'
        if self.type == 'questionnaire' and not self.has_started():
            return 'before_beginning'
        if self.type == 'questionnaire' and self.has_finished():
            return 'after_end'
        if self.type != 'questionnaire' and self.has_started():
            return 'after_beginning'

        if not user_attendance.is_libero() == (self.competitor_type == 'liberos'):
            return 'not_libero'
        if self.company and self.company != user_attendance.team.subsidiary.company:
            return 'not_for_company'
        if self.city and self.city != user_attendance.team.subsidiary.city:
            return 'not_for_city'

        return True

    def has_admission(self, userprofile):
        if not userprofile.is_libero() == (self.competitor_type == 'liberos'):
            return False
        if self.company and userprofile.team and self.company != userprofile.team.subsidiary.company:
            return False
        if self.city and userprofile.team and self.city != userprofile.team.subsidiary.city:
            return False

        if self.without_admission:
            return True
        else:
            if self.competitor_type == 'single_user' or self.competitor_type == 'liberos':
                return self.user_attendance_competitors.filter(pk=userprofile.pk).count() > 0
            elif self.competitor_type == 'team':
                return self.team_competitors.filter(pk=userprofile.team.pk).count() > 0
            elif self.competitor_type == 'company':
                return self.company_competitors.filter(pk=userprofile.team.subsidiary.company.pk).count() > 0
            return True

    def make_admission(self, userprofile, admission=True):
        if not self.without_admission and self.can_admit(userprofile) == True:
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
                    self.company_competitors.add(userprofile.team.subsidiary.company)
                else:
                    self.company_competitors.remove(userprofile.team.subsidiary.company)

    def __unicode__(self):
        return "%s" % self.name

class CompetitionResult(models.Model):
    """Výsledek soutěže"""
    class Meta:
        verbose_name = _(u"Výsledek soutěže")
        verbose_name_plural = _(u"Výsledky soutěží")
        unique_together = (("user_attendance", "competition"), ("team", "competition"))

    user_attendance = models.ForeignKey(UserAttendance,
        related_name="competitions_results",
        null=True,
        blank=True,
        default=None,
        )
    team = models.ForeignKey(Team,
        related_name="competitions_results",
        null=True,
        blank=True,
        default=None,
        )
    competition = models.ForeignKey(Competition,
        related_name="results",
        null=False,
        blank=False,
        )
    result = models.FloatField(
        verbose_name=_(u"Výsledek"),
        null=True,
        blank=True,
        default=None,
        )

    def get_total_result(self):
        members = self.team.member_count if self.team else 1
        return float(self.result) * float(members)

    def __unicode__(self):
        if self.competition.competitor_type == 'team':
            return "%s" % self.team.name
        else:
            if self.user_attendance:
                return "%s" % self.user_attendance.userprofile.user.get_full_name()
    
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
        unique_together = (("competition", "order"),)

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
        default=False,
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
        unique_together = (("choice_type", "text"),)

    choice_type = models.ForeignKey(ChoiceType,
        verbose_name=_(u"Typ volby"),
        related_name="choices",
        null=False,
        blank=False)
    text = models.CharField(
        verbose_name=_(u"Nabídka"),
        max_length=250,
        db_index = True,
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
    """Odpověď"""
    class Meta:
        verbose_name = _(u"Odpověď")
        verbose_name_plural = _(u"Odpovědi")
        ordering = ('user_attendance__team__subsidiary__city', 'pk')
        unique_together = (("user_attendance", "question"),)

    user_attendance = models.ForeignKey(UserAttendance, null=True, blank=True)
    question = models.ForeignKey(Question, null=False)
    choices = models.ManyToManyField(Choice)
    comment = models.TextField(
        verbose_name=_(u"Komentář"),
        max_length=600,
        null=True, blank=True)
    points_given = models.IntegerField(
        null=True, blank=True, default=None)
    attachment = models.FileField(
        upload_to="questionaire/",
        max_length=600,
        )

    def str_choices(self):
        return ", ".join([choice.text for choice in self.choices.all()])

    def __unicode__(self):
        return "%s" % self.str_choices()

def get_company(campaign, user):
    if not user.userprofile.userattendance_set.get(campaign=campaign).team:
        return None
    try:
        return user.userprofile.userattendance_set.get(campaign=campaign).team.subsidiary.company
    except UserProfile.DoesNotExist:
        return user.company_admin.administrated_company

def is_team_coordinator(user_attendance):
    if user_attendance.team and user_attendance.team.coordinator_campaign == user_attendance:
        return True
    return False

def get_company_admin(user, campaign):
    try:
        return user.company_admin.get(campaign=campaign, company_admin_approved='approved')
    except CompanyAdmin.DoesNotExist:
        return None

def is_competitor(user):
    try:
        if user.get_profile():
            return True
        else:
            return False
    except UserProfile.DoesNotExist:
        return False


#TODO: this is quickfix, should be geting campaign slug from URL
class TeamInCampaignManager(models.Manager):
    def get_query_set(self):
        return super(TeamInCampaignManager,self).get_query_set().filter(campaign__slug=settings.CAMPAIGN)


class TeamInCampaign(Team):
    objects = TeamInCampaignManager()
    class Meta:
        proxy = True


class SubsidiaryInCampaignManager(models.Manager):
    def get_query_set(self):
        return super(SubsidiaryInCampaignManager,self).get_query_set().filter(city__cityincampaign__campaign__slug=settings.CAMPAIGN)


class SubsidiaryInCampaign(Subsidiary):
    objects = SubsidiaryInCampaignManager()
    class Meta:
        proxy = True

#Signals:
def pre_user_team_changed(sender, instance, changed_fields=None, **kwargs):
    field, (old, new) = changed_fields.items()[0]
    old_team = Team.objects.get(pk=old) if old else None
    new_team = Team.objects.get(pk=new) if new else None
    if instance.team and new_team.member_count == 0:
        instance.approved_for_team = 'approved'
    else:
        instance.approved_for_team = 'undecided'
pre_save_changed.connect(pre_user_team_changed, sender=UserAttendance, fields=['team'])

def post_user_team_changed(sender, instance, changed_fields=None, **kwargs):
    field, (old, new) = changed_fields.items()[0]
    old_team = Team.objects.get(pk=old) if old else None
    new_team = Team.objects.get(pk=new) if new else None
    if new_team:
        new_team.autoset_member_count()
        new_team.save()
        results.recalculate_results_team(new_team)

    if old_team:
        old_team.autoset_member_count()
        old_team.save()
        results.recalculate_results_team(old_team)

    results.recalculate_result_competitor(instance)
post_save_changed.connect(post_user_team_changed, sender=UserAttendance, fields=['team'])

@receiver(post_save, sender=User)
def update_mailing_user(sender, instance, created, **kwargs):
    try:
        for user_attendance in instance.userprofile.userattendance_set.all():
            mailing.add_or_update_user(user_attendance)
    except UserProfile.DoesNotExist:
        pass

@receiver(post_save, sender=UserAttendance)
def update_mailing_user_attendance(sender, instance, created, **kwargs):
    mailing.add_or_update_user(instance)

@receiver(post_save, sender=Payment)
def update_mailing_payment(sender, instance, created, **kwargs):
    if instance.user_attendance:
        mailing.add_or_update_user(instance.user_attendance)

@receiver(post_save, sender=Trip)
def trip_post_save(sender, instance, **kwargs):
    if instance.user:
        results.recalculate_result_competitor(instance.user)

@receiver(post_save, sender=Competition)
def competition_post_save(sender, instance, **kwargs):
    instance.recalculate_results()

@receiver(post_save, sender=Answer)
def answer_post_save(sender, instance, **kwargs):
    competition = instance.question.competition
    if competition.competitor_type == 'team':
        results.recalculate_result(competition, instance.user.team)
    elif competition.competitor_type == 'single_user' or competition.competitor_type == 'liberos':
        results.recalculate_result(competition, instance.user)
    elif competition.competitor_type == 'company':
        raise NotImplementedError("Company competitions are not working yet")

@receiver(pre_save, sender=Payment)
def payment_set_realized_date(sender, instance, **kwargs):
    if instance.status in Payment.done_statuses and not instance.realized:
        instance.realized = datetime.datetime.now()

def team_admin_changed(sender, instance, changed_fields=None, **kwargs):
    field, (old, new) = changed_fields.items()[0]
    try:
        email.new_team_coordinator_mail(UserAttendance.objects.get(pk=new))
    except UserAttendance.DoesNotExist:
        pass
post_save_changed.connect(team_admin_changed, sender=Team, fields=['coordinator_campaign'])
