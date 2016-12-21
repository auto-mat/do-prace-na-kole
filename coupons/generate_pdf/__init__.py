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
import os

from io import BytesIO

from PyPDF2 import PdfFileReader, PdfFileWriter

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def normpath(*args):
    return os.path.normpath(os.path.abspath(os.path.join(*args)))


def generate_coupon_pdf(outputStream, code, valid_until):
    packet = BytesIO()
    zirkel_path = normpath(__file__, "..", "Zirkel Regular.ttf")
    pdfmetrics.registerFont(TTFont('Zirkel-Regular', zirkel_path))
    # create a new PDF with Reportlab
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont('Zirkel-Regular', 20)
    can.drawString(150, 110, code)
    can.drawString(380, 110, valid_until)
    can.save()

    # move to the beginning of the StringIO buffer
    packet.seek(0)
    new_pdf = PdfFileReader(packet)
    # read your existing PDF
    dpnk_voucher_path = normpath(__file__, "..", "dpnk_voucher_final_new.pdf")
    with open(dpnk_voucher_path, "rb") as pdf_input:
        existing_pdf = PdfFileReader(pdf_input)
        output = PdfFileWriter()
        # add the "watermark" (which is the new pdf) on the existing page
        page = existing_pdf.getPage(0)
        page.mergePage(new_pdf.getPage(0))
        output.addPage(page)
        # finally, write "output" to a real file
        output.write(outputStream)
