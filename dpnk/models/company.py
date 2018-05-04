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
from django.core.validators import RegexValidator
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from stdnumfield.models import StdNumField

from .address import Address, get_address_string


ICO_ERROR_MESSAGE = _("IČO není zadáno ve správném formátu. Zkontrolujte že číslo má osm číslic a případně ho doplňte nulami zleva.")
DIC_ERROR_MESSAGE = _(
    "DIČ není zadáno ve správném formátu. "
    "Zkontrolujte že číslo má 8 až 10 číslic a případně ho doplňte nulami zleva. "
    "Číslu musí předcházet dvě písmena identifikátoru země (např. CZ)",
)


class Company(models.Model):
    """Organizace"""

    class Meta:
        verbose_name = _(u"Organizace")
        verbose_name_plural = _(u"Organizace")
        ordering = ('name',)

    name = models.CharField(
        unique=True,
        verbose_name=_(u"Název organizace"),
        help_text=_(u"Např. „Výrobna, a.s.“, „Příspěvková, p.o.“, „Nevládka, z.s.“, „Univerzita Karlova“"),
        max_length=60,
        null=False,
    )
    address = Address()
    ico = StdNumField(
        'cz.dic',
        default=None,
        verbose_name=_(u"IČO"),
        help_text=_("Pokud má vaše organizace IČO, prosím vyplňte, jinak nechte prázdné."),
        validators=[RegexValidator(r'^[0-9]*$', _('IČO musí být číslo'))],
        error_messages={'stdnum_format': ICO_ERROR_MESSAGE},
        blank=True,
        null=True,
    )
    dic = StdNumField(
        'cz.dic',
        verbose_name=_(u"DIČ"),
        max_length=15,
        default="",
        validators=[RegexValidator(r'^[a-zA-Z]{2}[0-9]*$', _('DIČ musí být číslo uvozené dvoupísmeným identifikátorem státu.'))],
        error_messages={'stdnum_format': DIC_ERROR_MESSAGE},
        blank=True,
        null=True,
    )
    active = models.BooleanField(
        verbose_name=_(u"Aktivní"),
        default=True,
        null=False,
    )

    def has_filled_contact_information(self):
        address_complete = self.address.street and self.address.street_number and self.address.psc and self.address.city
        return bool(self.name and address_complete and self.ico)

    def __str__(self):
        return "%s" % self.name

    def company_address(self):
        return get_address_string(self.address)

    def admin_emails(self, campaign):
        admins = self.company_admin.filter(campaign=campaign)
        return ", ".join([a.userprofile.user.email for a in admins])

    def admin_telephones(self, campaign):
        admins = self.company_admin.filter(campaign=campaign)
        return ", ".join([a.userprofile.telephone for a in admins])

    def clean(self):
        if Company.objects.filter(name__unaccent__iexact=self.name).exclude(pk=self.pk).exists():
            raise ValidationError({'name': _('Organizace s tímto názvem již existuje. Nemusíte tedy zakládat novou, vyberte tu stávající.')})

        if self.ico and Company.objects.filter(
            ico=self.ico,
            active=True,
        ).exclude(pk=self.pk).exists():
            raise ValidationError({'ico': 'Organizace s tímto IČO již existuje, nezakládemte prosím novou, ale vyberte jí prosím ze seznamu'})

    def get_related_competitions(self, campaign):
        """ Get all competitions where this company is involved filtered by given campaign """
        from .competition import Competition
        cities = self.subsidiaries.values('city')
        competitions = Competition.objects.filter(company__isnull=True).filter(
            Q(city__in=cities, campaign=campaign) |
            Q(city__isnull=True, campaign=campaign),
        )
        return competitions
