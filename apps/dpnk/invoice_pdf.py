# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2015 o.s. Auto*Mat
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
import os
from InvoiceGenerator.api import Invoice, Item, Client, Provider, Creator
from InvoiceGenerator.pdf import SimpleInvoice
import datetime


def make_invoice_sheet_pdf(outfile, invoice):
    DIR = os.path.dirname(__file__)

    client = Client(
        invoice.company.name,
        address=u"%s %s" % (invoice.company.address_street, invoice.company.address_street_number),
        zip=invoice.company.address_psc,
        city=invoice.company.address_city,
        ir=invoice.company.ico,
        vat_id=invoice.company.dic,
    )

    if invoice.order_number:
        client.note = u"Číslo objednávky: %s" % invoice.order_number

    provider = Provider(
        u"Auto*Mat, o.s.",
        email=u"lucie.mullerova@auto-mat.cz",
        address=u"Lublaňská 398/18",
        zip=u"120 00",
        city=u"Praha 2",
        bank_name=u"Poštovní spořitelna",
        bank_account='217 359 444 / 0300',
        vat_id=u"CZ22670319",
        ir=u"22670319",
        phone=u"737 563 750",
        logo_filename=os.path.join(DIR, "static/img/logo.jpg"),
        note=u"""Sdružení Auto*Mat bylo zaregistrováno u MV ČR pod č. VS/1-1/68 776/07-R.
U Městského soudu v Praze jsme vedeni pod spisovou značkou L 18119.
Společně s vámi tvoříme město, ve kterém chceme žít. www.auto-mat.cz
""",
    )

    creator = Creator(
        u'Lucie Mullerová',
        stamp_filename=os.path.join(DIR, "static/img/stamp.png"),
    )

    invoice_gen = Invoice(client, provider, creator)
    invoice_gen.title = u"Faktura %s/%s" % (invoice.sequence_number, invoice.exposure_date.year)
    invoice_gen.variable_symbol = "%s%03d" % (invoice.exposure_date.year, invoice.sequence_number)
    invoice_gen.date = invoice.exposure_date
    invoice_gen.payback = invoice.exposure_date + datetime.timedelta(days=14)
    invoice_gen.taxable_date = invoice.taxable_date
    invoice_gen.rounding_result = True
    invoice_gen.use_tax = True
    invoice_gen.currency_locale = u"cs_CZ.utf-8"
    invoice_gen.paytype = u"bankovním převodem"

    for payment in invoice.payment_set.order_by("user_attendance__userprofile__user__last_name", "user_attendance__userprofile__user__first_name"):
        if invoice.company_pais_benefitial_fee:
            amount = invoice.campaign.benefitial_admission_fee_company
        else:
            amount = payment.amount
        invoice_gen.add_item(Item(1, amount, description=u"Platba za soutěžící/ho %s" % (payment.user_attendance.userprofile.user.get_full_name()), tax=21))
    invoice.total_amount = invoice_gen.price_tax
    pdf = SimpleInvoice(invoice_gen)
    pdf.gen(outfile, generate_qr_code=True)
