# -*- coding: utf-8 -*-

import os
import reportlab
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.barcode import code128
from svg2rlg import svg2rlg


def make_customer_sheets_pdf(outfile, delivery_batch):
    doc = SimpleDocTemplate(outfile, pagesize=A4,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    Story = []

    for package_transaction in delivery_batch.packagetransaction_set.all():
        make_sheet(package_transaction, Story)

    def firstPageGraphics(canvas, doc):
        canvas.saveState()

        canvas.setLineWidth(.3)
        canvas.line(45, 80, 550, 80)
        canvas.setFont('DejaVuB', 9)
        canvas.restoreState()

    doc.build(Story, onFirstPage=firstPageGraphics)


def make_sheet(package_transaction, Story):
    DIR = os.path.dirname(__file__)
    # CONFIGURATION
    user_attendance = package_transaction.user_attendance
    delivery_number = "{:0>9.0f}".format(package_transaction.tracking_number)
    if u"pánské" in user_attendance.t_shirt_size.__unicode__():
        t_shirt_preview_file = os.path.join(DIR, "static/img/campaign_tshirt_men.svg")
    if u"dámské" in user_attendance.t_shirt_size.__unicode__():
        t_shirt_preview_file = os.path.join(DIR, "static/img/campaign_tshirt_women.svg")
    logo_file = os.path.join(DIR, "static/img/logo.jpg")
    # END OF CONFIGURATION

    folder = '/usr/share/fonts/truetype/ttf-dejavu'
    reportlab.rl_config.TTFSearchPath.append(folder)
    pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuB', 'DejaVuSans-Bold.ttf'))

    # STYLES
    styles = getSampleStyleSheet()
    styles['Normal'].fontName = 'DejaVu'
    styles['Normal'].fontSize = 10
    styles['Heading1'].fontName = 'DejaVuB'
    styles['Heading1'].fontSize = 16
    styles['Heading1'].alignment = TA_CENTER
    styles['Heading2'].fontName = 'DejaVuB'
    styles['Heading2'].fontSize = 10
    styles['Heading2'].alignment = TA_CENTER
    styles['Heading3'].fontName = 'DejaVuB'
    styles['Heading3'].fontSize = 10
    styles['Heading3'].alignment = TA_RIGHT
    styles.add(ParagraphStyle(name='Indented', leftIndent=290))
    styles['Indented'].fontName = 'DejaVu'

    # START OF THE DOCUMENT
    im = Image(logo_file, 3.98*cm, 1.5*cm)
    Story.append(im)
    Story.append(Spacer(1, 30))

    barcode = code128.Code128(delivery_number, barWidth=0.5*mm, barHeight=20*mm, left=5*cm)
    Story.append(barcode)
    Story.append(Paragraph(delivery_number, styles["Normal"]))

    Story.append(Paragraph(user_attendance.campaign.__unicode__(), styles["Heading1"]))
    Story.append(Paragraph(u"Zákaznický list", styles["Heading2"]))
    Story.append(Spacer(1, 36))

    Story.append(Spacer(1, 30))

    Story.append(Paragraph(u"Uživatelské jméno: %s" % user_attendance.userprofile.user.username, styles["Normal"]))
    d = package_transaction.created
    datestr = "%d. %d. %d" % (d.day, d.month, d.year)
    Story.append(Paragraph(datestr, styles["Heading3"]))
    Story.append(Paragraph(u"#%s" % package_transaction.delivery_batch.pk, styles["Heading3"]))
    Story.append(Spacer(1, 30))

    Story.append(Paragraph(u"%s, %s" % (user_attendance.team.subsidiary.company, user_attendance.team.subsidiary.address_recipient), styles["Normal"]))
    Story.append(Paragraph(user_attendance.__unicode__(), styles["Normal"]))
    Story.append(Paragraph(u"%s %s" % (user_attendance.team.subsidiary.address_street, user_attendance.team.subsidiary.address_street_number), styles["Normal"]))
    Story.append(Paragraph(u"%s, %s" % (user_attendance.team.subsidiary.address_psc, user_attendance.team.subsidiary.address_city), styles["Normal"]))
    Story.append(Paragraph(user_attendance.t_shirt_size.__unicode__(), styles["Heading1"]))
    Story.append(Spacer(1, 72))

    svg_tshirt = svg2rlg(t_shirt_preview_file)
    svg_tshirt.scale(0.2, 0.2)
    svg_tshirt.width = 5*cm
    svg_tshirt.height = 0
    svg_tshirt.shift(11*cm, 0)
    Story.append(svg_tshirt)

    Story.append(PageBreak())
