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

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from smart_selects.db_fields import ChainedForeignKey

from .address import Address, get_address_string
from .city import City
from .. import util


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(active=True)


class Subsidiary(models.Model):
    """Pobočka"""

    class Meta:
        verbose_name = _(u"Pobočka organizace")
        verbose_name_plural = _(u"Pobočky organizací")

    address = Address()
    company = ChainedForeignKey(
        'Company',
        related_name="subsidiaries",
        null=False,
        blank=False,
    )
    city = models.ForeignKey(
        City,
        verbose_name=_("Soutěžní město"),
        help_text=_("Váš tým se zařadí do žebříčků za nejbližší soutěžní město."),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    active = models.BooleanField(
        verbose_name=_(u"Aktivní"),
        default=True,
        null=False,
    )

    box_addressee_name = models.CharField(
        verbose_name=_("Jméno adresáta krabice pro pobočku"),
        help_text=_("Jmené osoby, která převezme krabici s tričky a zajistí jeich rozdělení na této pobočce. Nemusí se účastnit soutěže."),
        max_length=30,
        null=True,
        blank=True,
    )
    box_addressee_telephone = models.CharField(
        verbose_name=_("Telefon adresáta krabice pro pobočku"),
        max_length=30,
        null=True,
        blank=True,
    )
    box_addressee_email = models.EmailField(
        verbose_name=_("Email adresáta krabice pro pobočku"),
        null=True,
        blank=True,
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    def __str__(self):
        return "%s - %s" % (get_address_string(self.address), self.city)

    def name(self):
        return get_address_string(self.address)

    def get_recipient_string(self):
        """ makes recipient from address_recipient and company name """
        if self.address_recipient:
            if self.address_recipient.lower().strip() == self.company.name.lower().strip():
                return self.address_recipient
            else:
                return "%s (%s)" % (self.address_recipient, self.company.name)
        else:
            return self.company.name

    def clean(self):
        Address.clean(self.address, self, Subsidiary)
        if self.box_addressee_name or self.box_addressee_email or self.box_addressee_telephone:
            if not self.box_addressee_name:
                raise ValidationError({'box_addressee_name': _("Pokud vyplňujete adresáta krabice, vyplňte prosím i jeho jméno")})
            if not self.box_addressee_email:
                raise ValidationError({'box_addressee_email': _("Pokud vyplňujete adresáta krabice, vyplňte prosím i jeho e-mail")})
            if not self.box_addressee_telephone:
                raise ValidationError({'box_addressee_telephone': _("Pokud vyplňujete adresáta krabice, vyplňte prosím i jeho telefon")})


class SubsidiaryInCampaign:
    def __init__(self, subsidiary, campaign):
        self.subsidiary = subsidiary
        self.campaign = campaign

    def teams(self):
        return self.subsidiary.teams.filter(campaign=self.campaign)

    def eco_trip_count(self):
        return sum(team.get_eco_trip_count() for team in self.teams())

    def frequency(self):
        teams = self.teams()
        return sum(team.get_frequency() for team in teams) / len(teams)

    def distance(self):
        return sum(team.get_length() for team in self.teams())

    def emissions(self):
        return util.get_emissions(self.distance())

    def __str__(self):
        return str(self.subsidiary)
