# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
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

from django.core.management import call_command
from django.test import TestCase
from dpnk import models, util
import datetime


class Tests(TestCase):
    def setUp(self):
        call_command('denorm_init')
        util.rebuild_denorm_models(models.Team.objects.filter(pk=1))

    def tearDown(self):
        call_command('denorm_drop')

    fixtures = ['campaign', 'auth_user', 'users', 'transactions', 'invoices', 'company_competition']

    def test_change_invoice_payments_status(self):
        payment = models.Payment.objects.get(pk=3)
        invoice = models.Invoice.objects.get(pk=1)
        payment.invoice = invoice
        payment.save()
        self.assertEquals(invoice.payment_set.get().status, 0)
        invoice.paid_date = datetime.date(year=2010, month=11, day=20)
        invoice.save()
        self.assertEquals(invoice.payment_set.get().status, 1007)
        invoice.delete()
        payment = models.Payment.objects.get(pk=3)
        self.assertEquals(payment.status, 1005)

    def test_competition_type_string(self):
        competition = models.Competition.objects.get(pk=3)
        self.assertEquals(str(competition.type_string()), " soutěž na pravidelnost týmů   ")

        competition = models.Competition.objects.get(pk=4)
        self.assertEquals(str(competition.type_string()), " dotazník jednotlivců   ")

        competition = models.Competition.objects.get(pk=5)
        self.assertEquals(str(competition.type_string()), " soutěž na vzdálenost jednotlivců  ve městě Testing city pro muže")

        competition = models.Competition.objects.get(pk=6)
        self.assertEquals(str(competition.type_string()), " soutěž na vzdálenost jednotlivců  ve městě Testing city ")

        competition = models.Competition.objects.get(pk=7)
        self.assertEquals(str(competition.type_string()), "vnitrofiremní soutěž na pravidelnost týmů organizace Testing company  ")

        competition = models.Competition.objects.get(pk=8)
        self.assertEquals(str(competition.type_string()), " soutěž na vzdálenost společností  ve městě Testing city ")

        competition = models.Competition.objects.get(pk=9)
        self.assertEquals(str(competition.type_string()), " soutěž na vzdálenost týmů  ve městě Testing city pro muže")
