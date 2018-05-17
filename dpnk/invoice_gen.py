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
import decimal
import os

from InvoiceGenerator import pdf, pohoda
from InvoiceGenerator.api import Client, Creator, Invoice, Item, Provider


def generate_invoice(invoice):
    DIR = os.path.dirname(__file__)

    client = Client(
        invoice.company_name,
        division=invoice.company_address_recipient,
        country=invoice.country,
        address=" ".join(filter(None, (invoice.company_address_street, invoice.company_address_street_number))),
        zip_code=str(invoice.company_address_psc or ""),
        city=invoice.company_address_city,
        ir=invoice.company_ico,
        vat_id=invoice.company_dic,
        phone=invoice.telephone,
        email=invoice.email,
        note=invoice.client_note,
    )

    if invoice.order_number:
        client.note += "\nČíslo objednávky: %s" % invoice.order_number

    provider = Provider(
        "Auto*Mat, z.s.",
        email="kontakt@dopracenakole.cz",
        address="Vodičkova 704/36",
        zip_code="110 00",
        city="Praha 1",
        bank_name="Fio banka",
        bank_account='2601085491',
        bank_code='2010',
        vat_id="CZ22670319",
        ir="22670319",
        phone="212 240 666",
        logo_filename=os.path.join(DIR, "static/img/logo.jpg"),
        note="Spolek je veden u Městského soudu v Praze pod spisovou značkou L 18119. "
             "Auto*mat - společně s vámi tvoříme město, ve kterém chceme žít."
             "\nhttps://www.auto-mat.cz",
    )

    creator = Creator(
        'Klára Dušáková',
        stamp_filename=os.path.join(DIR, "static/img/stamp.png"),
    )

    invoice_gen = Invoice(client, provider, creator)
    invoice_gen.title = u"Faktura %s/%03d" % (invoice.exposure_date.year, invoice.sequence_number)
    invoice_gen.variable_symbol = invoice.variable_symbol
    invoice_gen.number = invoice.document_number()
    invoice_gen.date = invoice.exposure_date
    invoice_gen.payback = invoice.payback_date
    invoice_gen.taxable_date = invoice.taxable_date
    invoice_gen.rounding_result = True
    invoice_gen.rounding_strategy = decimal.ROUND_HALF_UP
    invoice_gen.use_tax = True
    invoice_gen.currency_locale = u"cs_CZ.UTF-8"
    invoice_gen.paytype = u"bankovním převodem"

    for payment in invoice.payment_set.order_by("user_attendance__userprofile__user__last_name", "user_attendance__userprofile__user__first_name"):
        if invoice.company_pais_benefitial_fee:
            amount = invoice.campaign.benefitial_admission_fee_company
        else:
            amount = payment.amount
        description = "Platba za soutěžící/ho %s" % ("" if invoice.anonymize else payment.user_attendance.name_for_trusted())
        invoice_gen.add_item(Item(1, amount, description=description, tax=21))
    return invoice_gen


def make_invoice_pdf(outfile_pdf, invoice_gen):
    os.environ["INVOICE_LANG"] = "cs"
    pdf_file = pdf.SimpleInvoice(invoice_gen)
    pdf_file.gen(outfile_pdf, generate_qr_code=True)


def make_invoice_xml(outfile_xml, invoice_gen):
    xml_file = pohoda.SimpleInvoice(invoice_gen)
    xml_file.gen(outfile_xml)
