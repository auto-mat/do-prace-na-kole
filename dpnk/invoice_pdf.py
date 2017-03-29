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

from InvoiceGenerator.api import Client, Creator, Invoice, Item, Provider
from InvoiceGenerator.pdf import SimpleInvoice


def make_invoice_sheet_pdf(outfile, invoice):
    DIR = os.path.dirname(__file__)

    client = Client(
        invoice.company_name,
        address="%s %s" % (invoice.company_address_street, invoice.company_address_street_number),
        zip=invoice.company_address_psc,
        city=invoice.company_address_city,
        ir=invoice.company_ico,
        vat_id=invoice.company_dic,
    )

    if invoice.order_number:
        client.note = u"Číslo objednávky: %s" % invoice.order_number

    provider = Provider(
        "Auto*Mat, z.s.",
        email="kontakt@dopracenakole.cz",
        address="Bořivojova 694/108",
        zip="130 00",
        city="Praha 3",
        bank_name="Fio banka",
        bank_account='2601085491 / 2010',
        vat_id="CZ22670319",
        ir="22670319",
        phone="212 240 666",
        logo_filename=os.path.join(DIR, "static/img/logo.jpg"),
        note="Spolek je veden u Městského soudu v Praze pod spisovou značkou L 18119.\n"
             "Auto*mat - společně s vámi tvoříme město, ve kterém chceme žít.\n"
             "                                       http://www.auto-mat.cz",
    )

    creator = Creator(
        'Klára Dušáková',
        stamp_filename=os.path.join(DIR, "static/img/stamp.png"),
    )

    invoice_gen = Invoice(client, provider, creator)
    invoice_gen.title = u"Faktura %s/%s" % (invoice.sequence_number, invoice.exposure_date.year)
    invoice_gen.variable_symbol = invoice.variable_symbol
    invoice_gen.number = invoice.document_number()
    invoice_gen.date = invoice.exposure_date.strftime("%d.%m.%Y")
    invoice_gen.payback = invoice.payback_date.strftime("%d.%m.%Y")
    invoice_gen.taxable_date = invoice.taxable_date.strftime("%d.%m.%Y")
    invoice_gen.rounding_result = True
    invoice_gen.use_tax = True
    invoice_gen.currency_locale = u"cs_CZ.UTF-8"
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
