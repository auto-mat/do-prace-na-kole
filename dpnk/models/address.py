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

from composite_field import CompositeField

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext_lazy as _

from psc.models import PSC

from .. import util


def get_address_string(address):
    return ", ".join(
        filter(
            None,
            [
                getattr(address, 'recipient', ''),
                ("%s %s" % (address.street, address.street_number)).strip(),
                ("%s %s" % (util.format_psc(address.psc), address.city)).strip(),
            ],
        ),
    )


def address_generator(
    null_blank=False,
    recipient_name=_("Název pobočky"),
    char_psc=False,
):
    if char_psc:
        psc_field = models.CharField(
            verbose_name=_(u"PSČ"),
            max_length=50,
            null=True,
            blank=True,
        )
    else:
        psc_field = models.IntegerField(
            verbose_name=_(u"PSČ"),
            validators=[
                MaxValueValidator(99999),
                MinValueValidator(10000),
            ],
            default=None,
            null=True,
            blank=null_blank,
        )

    class AddressField(CompositeField):
        street = models.CharField(
            verbose_name=_(u"Ulice"),
            default="",
            max_length=50,
            null=null_blank,
            blank=null_blank,
        )
        street_number = models.CharField(
            verbose_name=_(u"Číslo domu"),
            default="",
            max_length=10,
            null=null_blank,
            blank=null_blank,
        )
        recipient = models.CharField(
            verbose_name=recipient_name,
            help_text=_("Nezadávejte adresu jako název pobočky."),
            default="",
            max_length=50,
            null=True,
            blank=True,
        )
        psc = psc_field
        city = models.CharField(
            verbose_name=_(u"Město"),
            default="",
            max_length=50,
            null=null_blank,
            blank=null_blank,
        )

        def __str__(self):
            return get_address_string(self)

        def clean(self, value, model):
            if self.psc and not PSC.objects.filter(psc=self.psc).exists():
                raise ValidationError(
                    {'address_psc': _('Toto PSČ neexistuje v databázi všech směrovacích čísel České Republiky. Prosím zadejte platné PSČ')},
                )

    return AddressField


Address = address_generator()
AddressOptional = address_generator(True)
addressee_string = _("Adresát na faktuře")
CompanyAddress = address_generator(
    False,
    recipient_name=addressee_string,
)
InvoiceAddress = address_generator(
    True,
    recipient_name=addressee_string,
    char_psc=True,
)
