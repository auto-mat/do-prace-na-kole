# -*- coding: utf-8 -*-
import os
from InvoiceGenerator.api import Invoice, Item, Client, Provider, Creator
from InvoiceGenerator.pdf import SimpleInvoice
import models
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
    invoice_gen.currency = u"Kč"

    for subsidiary in models.Subsidiary.objects.filter(teams__users__transactions__payment__invoice=invoice).distinct():
       competitors = invoice.payment_set.filter(user_attendance__team__subsidiary=subsidiary).order_by("user_attendance__userprofile__user__last_name", "user_attendance__userprofile__user__first_name")
       if competitors.exists():
          fee = subsidiary.city.cityincampaign_set.get(campaign=invoice.campaign).admission_fee_company
          invoice_gen.add_item(Item(competitors.count(), fee, description=u"Platba účasti v kampani %s na pobočce %s, %s za soutěžící %s" % (invoice.campaign, subsidiary.address.street, subsidiary.address.city, ", ".join([u.user_attendance.__unicode__() for u in competitors])), tax=21))

    pdf = SimpleInvoice(invoice_gen)
    pdf.gen(outfile, generate_qr_code=True)
