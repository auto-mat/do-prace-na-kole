# -*- coding: utf-8 -*-

import os
import reportlab
from reportlab.platypus import Paragraph, Image
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import locale


def make_invoice_sheet_pdf(outfile, invoice):
    canvas = Canvas(outfile, pagesize=A4)

    folder = '/usr/share/fonts/truetype/ttf-dejavu'
    reportlab.rl_config.TTFSearchPath.append(folder)
    pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuB', 'DejaVuSans-Bold.ttf'))

    make_sheet(invoice, canvas)
    canvas.showPage()

    canvas.save()


def make_sheet(invoice, canvas):
    DIR = os.path.dirname(__file__)
    # CONFIGURATION
    logo_file = os.path.join(DIR, "static/img/logo.jpg")
    # END OF CONFIGURATION

    # STYLES
    styles = getSampleStyleSheet()
    styles['Normal'].fontName = 'DejaVu'
    styles['Normal'].fontSize = 10
    styles['Heading1'].fontName = 'DejaVuB'
    styles['Heading1'].fontSize = 12
    styles['Heading1'].alignment = TA_CENTER
    styles.add(ParagraphStyle(name='Indented', leftIndent=290))
    styles['Indented'].fontName = 'DejaVu'

    # START OF THE DOCUMENT
    im = Image(logo_file, 3.98*cm, 1.5*cm)
    im.drawOn(canvas, 11*cm, 25*cm)

    canvas.setFont('DejaVuB', 20)
    canvas.drawString(3*cm, 26*cm, "FAKTURA 2/2014")
    canvas.drawString(3*cm, 25*cm, "Daňový doklad")

    canvas.setFont('DejaVuB', 10)
    canvas.drawString(3*cm, 23.5*cm, "OBJEDNATEL")
    canvas.drawString(3*cm, 22.5*cm, invoice.company.name)
    canvas.setFont('DejaVu', 10)
    canvas.drawString(3*cm, 22*cm, "%s %s" % (invoice.company.address_street, invoice.company.address_street_number))
    canvas.drawString(3*cm, 21.5*cm, invoice.company.address_city)
    canvas.drawString(3*cm, 21*cm, "PSČ %s" % invoice.company.address_psc)
    canvas.drawString(3*cm, 20.5*cm, "IČO: %s" % invoice.company.ico)

    canvas.setFont('DejaVuB', 10)
    canvas.drawString(10*cm, 23.5*cm, "DODAVATEL")
    canvas.drawString(10*cm, 22.5*cm, "Auto*Mat, o.s.")
    canvas.setFont('DejaVu', 10)
    canvas.drawString(10*cm, 22*cm, "Lublaňská 398/18")
    canvas.drawString(10*cm, 21.5*cm, "120 00 Praha 2")
    canvas.drawString(10*cm, 21*cm, "IČ: 22670319/ DIČ: CZ22670319")
    canvas.drawString(10*cm, 20.5*cm, "č. účtu: 217 359 444 / 0300")
    canvas.drawString(10*cm, 20*cm, "VS: 2014002")

    canvas.drawString(3*cm, 18.5*cm, "Fakturujeme Vám startovní poplatek za účastníky akce Do práce na kole 2014.")
    invoice_count = invoice.payment_set.count()
    canvas.drawString(3*cm, 18*cm, "Počet soutěžících, za které fakturujeme poplatek: %s" % invoice_count)
    p = Paragraph(u"Jména účastníků: %s" % (", ".join([u.user_attendance.__unicode__() for u in invoice.payment_set.all()])), styles['Normal'])
    p.wrapOn(canvas, 17*cm, 10*cm)
    p.drawOn(canvas, 3 * cm, 7.5 * cm)

    payment_base = sum([u.user_attendance.team.subsidiary.city.cityincampaign_set.get(campaign=invoice.campaign).admission_fee for u in invoice.payment_set.all()])

    #TODO: get the fee from the database
    locale.setlocale(locale.LC_ALL, "cs_CZ.utf8")
    canvas.drawRightString(18*cm, 7*cm, u"CELKEM: %s Kč" % locale.format("%0.1f", payment_base * 1.21))
    canvas.drawRightString(18*cm, 6.5*cm, u"Bez daně: %s Kč" % (locale.format("%0.1f", payment_base)))
    canvas.drawRightString(18*cm, 6*cm, u"DPH 21,0%%: %s Kč" % locale.format("%0.1f", payment_base * 0.21))
    canvas.drawRightString(18*cm, 5.5*cm, u"CELKEM K ÚHRADĚ vč. DPH: %s Kč" % (locale.format("%0.1f", payment_base)))
    canvas.drawRightString(18*cm, 5*cm, u"Částka k úhradě: %s Kč" % (locale.format("%0.1f", payment_base)))

    canvas.drawString(3*cm, 4*cm, "V Praze, dne ")
    canvas.drawString(3*cm, 3.5*cm, "vystavil: Lucie Mullerová/737 563 750")
    canvas.drawString(3*cm, 3*cm, "lucie.mullerova@auto-mat.cz")

    canvas.drawString(3*cm, 2.5*cm, "Sdružení Auto*Mat bylo zaregistrováno u MV ČR pod číslem VS/1-1/68 776/07-R.")
    canvas.drawString(3*cm, 2*cm, "U Městského soudu v Praze jsme vedeni pod spisovou značkou L 18119.")
    canvas.drawString(3*cm, 1.5*cm, "Společně s vámi tvoříme město, ve kterém chceme žít.")
    canvas.drawString(3*cm, 1*cm, "www.auto-mat.cz")
