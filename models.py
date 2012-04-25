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
# Python library imports
import datetime

class Team(models.Model):
    """Profil týmu"""

    class Meta:
        verbose_name = "Tým"
        verbose_name_plural = "Týmy"
        ordering = ('name',)

    CITIES = (2*('Praha',),
              2*('Brno',),
              2*('Liberec',))

    name = models.CharField(
        verbose_name="Název týmu",
        max_length=50, null=False,
        unique=True)
    company = models.CharField(
        verbose_name="Firma",
        max_length=50, null=False)
    address = models.CharField(
        verbose_name="Adresa firmy/pobočky (ulice a číslo)",
        max_length=50, null=False)
    city = models.CharField(
        verbose_name="Soutěžní město",
        choices=CITIES,
        max_length=40, null=False)
    password = models.CharField(
        verbose_name="Kódové slovo",
        max_length=20, null=False)

    def __unicode__(self):
        return "%s / %s" % (self.name, self.company)

class UserProfile(models.Model):
    """Uživatelský profil"""

    class Meta:
        verbose_name = "Uživatel"
        verbose_name_plural = "Uživatelé"

    GENDER = (('man', "Muž"),
              ('woman', "Žena"))

    firstname = models.CharField(
        verbose_name="Jméno",
        max_length=30, null=False)
    surname = models.CharField(
        verbose_name="Příjmení",
        max_length=30, null=False)
    user = models.ForeignKey(
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
        ('bt*', 'bankovní převod'),
        ('pt*', 'převod přes poštu'),
        ('sc', 'superCASH'),
        ('t', 'testovací platba'),
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
        max_length=50, null=True)
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
        null=True)
    pay_type = models.CharField(
        verbose_name="Typ platby",
        choices=PAY_TYPES,
        max_length=50,
        null=True)
    status = models.PositiveIntegerField(
        verbose_name="Status",
        choices=STATUS,
        max_length=50,
        null=True)
    error = models.PositiveIntegerField(
        verbose_name="Chyba",
        null=True)

    def __unicode__(self):
        return self.trans_id

class Voucher(models.Model):
    """Slevove kupony"""

    class Meta:
        verbose_name = "Kupon"
        verbose_name_plural = "Kupony"

    code = models.CharField(
        verbose_name="Kód",
        max_length=20, null=False)
    user = models.ForeignKey(UserProfile, null=True, blank=True)
