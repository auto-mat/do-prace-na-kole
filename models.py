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

    name = models.CharField(
        verbose_name="Jméno",
        max_length=50, null=False)
    company = models.CharField(
        verbose_name="Firma",
        max_length=50, null=False)
    password = models.CharField(
        verbose_name="Kódové slovo",
        max_length=20, null=False)

    def __unicode__(self):
        return self.name

class UserProfile(models.Model):
    """Uživatelský profil"""

    class Meta:
        verbose_name = "Uživatel"
        verbose_name_plural = "Uživatelé"

    GENDER = (('man', "Muž"),
              ('woman', "Žena"))

    LANGUAGE = (('cs', "Čeština"),
                ('en', "Angličtina"))

    COMPETITION_CITY = (2*('Praha',),
                        2*('Brno',),
                        2*('Liberec',))

    firstname = models.CharField(
        verbose_name="Jméno",
        max_length=30, null=False)
    surname = models.CharField(
        verbose_name="Příjmení",
        max_length=30, null=False)
    user = models.ForeignKey(
        User, unique=True)
    sex = models.CharField(
        verbose_name="Pohlaví",
        choices=GENDER,
        max_length=10, null=False)
    language = models.CharField(
        verbose_name="Jazyk",
        choices=LANGUAGE,
        default="cs",
        max_length=2,
        null=False)
    # -- Contacts
    telephone = models.CharField(
        verbose_name="Telefon",
        max_length=30, null=False)
    competition_city = models.CharField(
        verbose_name="Soutěžní město",
        choices=COMPETITION_CITY,
        max_length=40, null=False)
    team = models.ForeignKey(
        Team,
        verbose_name='Tým')

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



class Payment(models.Model):
    """Platba"""

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
        default=datetime.datetime.now(),
        null=False)
    realized = models.DateTimeField(
        verbose_name="Realizace",
        null=True)
    pay_type = models.CharField(
        verbose_name="Typ platby",
        max_length=50,
        null=True)
    status = models.CharField(
        verbose_name="Status",
        max_length=50,
        null=True)
    error = models.PositiveIntegerField(
        verbose_name="Chyba",
        null=True)

    def __unicode__(self):
        return self.trans_id
