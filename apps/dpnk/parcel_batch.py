# -*- coding: utf-8 -*-

from datetime import datetime
import os
import reportlab
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.barcode import code128
from svg2rlg import svg2rlg


def make_customer_sheet_pdf(outfile, user_attendance):
    DIR = os.path.dirname(__file__)
    # CONFIGURATION
    delivery_number = "1234567890"
    t_shirt_preview_file = os.path.join(DIR, "static/img/campaign_tshirt_men.svg")
    # END OF CONFIGURATION

    folder = '/usr/share/fonts/truetype/ttf-dejavu'
    reportlab.rl_config.TTFSearchPath.append(folder)
    pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuB', 'DejaVuSans-Bold.ttf'))

    doc = SimpleDocTemplate(outfile, pagesize=A4,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    Story = []

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
    Story.append(Paragraph(u"Zákaznický list", styles["Heading1"]))
    Story.append(Spacer(1, 36))

    d = datetime.now()
    datestr = "%d. %d. %d" % (d.day, d.month, d.year)
    Story.append(Paragraph(u"Ze dne %s" % datestr, styles["Normal"]))
    Story.append(Spacer(1, 30))

    barcode = code128.Code128(delivery_number, barWidth=0.5*mm, barHeight=20*mm)
    Story.append(barcode)
    Story.append(Paragraph(delivery_number, styles["Normal"]))

    Story.append(Spacer(1, 30))

    # START OF THE DOCUMENT
    svg_tshirt = svg2rlg(t_shirt_preview_file)
    svg_tshirt.scale(0.2, 0.2)
    svg_tshirt.width = 5*cm
    svg_tshirt.height = 0
    svg_tshirt.shift(10*cm, 0)
    Story.append(svg_tshirt)

    Story.append(Paragraph(u"Kampaň: %s" % user_attendance.campaign, styles["Normal"]))
    Story.append(Paragraph(u"Uživatelské jméno: %s" % user_attendance.userprofile.user.username, styles["Normal"]))
    Story.append(Paragraph(u"Adresa: %s" % user_attendance.team.subsidiary, styles["Normal"]))
    Story.append(Paragraph(u"Triko: %s" % user_attendance.t_shirt_size, styles["Normal"]))
    Story.append(Spacer(1, 72))

    def firstPageGraphics(canvas, doc):
        canvas.saveState()

        canvas.setLineWidth(.3)
        canvas.line(45, 80, 550, 80)
        canvas.setFont('DejaVuB', 9)
        canvas.restoreState()

    doc.build(Story, onFirstPage=firstPageGraphics)
