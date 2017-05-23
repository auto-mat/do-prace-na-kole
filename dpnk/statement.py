# -*- coding: utf-8 -*-
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2017 o.s. Auto*Mat
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
import datetime

from django.conf import settings

from fiobank import FioBank

from .models import Invoice


def parse(days_back=7):
    client = FioBank(token=settings.FIO_TOKEN)
    gen = client.period(
        datetime.datetime.now() - datetime.timedelta(days=days_back),
        datetime.datetime.now(),
    )
    for payment in gen:
        if payment['amount'] >= 0:
            variable_symbol = payment['variable_symbol']
            if not variable_symbol:
                print(payment)
                continue
            try:
                invoice = Invoice.objects.get(
                    variable_symbol=int(variable_symbol),
                )
                if invoice.total_amount == payment['amount'] and 'CZK' == payment['currency']:
                    invoice.paid_date = payment['date']
                    invoice.save()
                else:
                    print(payment)
            except Invoice.DoesNotExist:
                print(payment)
