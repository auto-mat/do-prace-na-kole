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

import reportlab
from reportlab.graphics.barcode import code128
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Image

from svg2rlg import svg2rlg


DIR = os.path.dirname(__file__)
logo_file = os.path.join(DIR, "static/img/logo.jpg")

page_height = 10
page_width = 15

text_line_height = 0.4
first_column = 0.5
second_column = 2
third_column = 7
fourth_column = 9


def make_customer_sheets_pdf(outfile, subsidiary_box):
    canvas = Canvas(outfile, pagesize=(page_width * cm, page_height * cm))

    folder = '/usr/share/fonts/truetype/ttf-dejavu'
    reportlab.rl_config.TTFSearchPath.append(folder)
    pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuB', 'DejaVuSans-Bold.ttf'))

    make_sheet(subsidiary_box, canvas)
    canvas.save()


def make_sheet(subsidiary_box, canvas):
    make_subsidiary_sheet(subsidiary_box, canvas)
    canvas.showPage()
    for team_package in subsidiary_box.teampackage_set.all():
        make_team_sheet(team_package, canvas)
        canvas.showPage()


def make_subsidiary_sheet(subsidiary_box, canvas):
    subsidiary = subsidiary_box.subsidiary
    if not subsidiary:
        return

    canvas.setFont('DejaVuB', 12)
    canvas.drawString(first_column * cm, (page_height - 2.5) * cm, subsidiary_box.delivery_batch.campaign.__str__())
    canvas.drawString(first_column * cm, (page_height - 3) * cm, "Krabice pro pobočku firmy")

    canvas.setFont('DejaVu', 10)
    canvas.drawString(first_column * cm, (page_height - 3.5) * cm, "%s" % (subsidiary.company))

    im = Image(logo_file, 3.98 * cm, 1.5 * cm)
    im.drawOn(canvas, first_column * cm, (page_height - 2) * cm)

    canvas.setFont('DejaVu', 10)
    barcode = code128.Code128(subsidiary_box.identifier(), barWidth=0.5 * mm, barHeight=20 * mm, humanReadable=True)
    barcode.drawOn(canvas, 8.3 * cm, (page_height - 2.7) * cm)
    canvas.drawString(9 * cm, (page_height - 0.45) * cm, "ID krabice pro pobočku:")

    offset = 5
    second_column = 4
    canvas.setFont('DejaVu', 10)
    canvas.drawString(first_column * cm, (page_height - offset - 0 * 0.5) * cm, "Společnost:")
    canvas.drawString(4 * cm, (page_height - offset - 0 * 0.5) * cm, "%s" % subsidiary.company)

    canvas.drawString(first_column * cm, (page_height - offset - 1 * 0.5) * cm, "IČO:")
    if subsidiary.company.ico:
        canvas.drawString(second_column * cm, (page_height - offset - 1 * 0.5) * cm, "%s" % subsidiary.company.ico)

    canvas.drawString(first_column * cm, (page_height - offset - 2 * 0.5) * cm, "Adresát:")
    canvas.drawString(second_column * cm, (page_height - offset - 2 * 0.5) * cm, "%s" % subsidiary.address_recipient)

    canvas.drawString(first_column * cm, (page_height - offset - 3 * 0.5) * cm, "Ulice:")
    canvas.drawString(second_column * cm, (page_height - offset - 3 * 0.5) * cm, "%s %s" % (subsidiary.address_street, subsidiary.address_street_number))

    canvas.drawString(first_column * cm, (page_height - offset - 4 * 0.5) * cm, "PSČ:")
    canvas.drawString(second_column * cm, (page_height - offset - 4 * 0.5) * cm, "%s" % subsidiary.address_psc)

    canvas.drawString(first_column * cm, (page_height - offset - 5 * 0.5) * cm, "Město:")
    canvas.drawString(second_column * cm, (page_height - offset - 5 * 0.5) * cm, "%s" % subsidiary.address_city)


def make_team_sheet(team_package, canvas):
    barcode = code128.Code128(team_package.identifier(), barWidth=0.5 * mm, barHeight=20 * mm, humanReadable=True)
    barcode.drawOn(canvas, 8.3 * cm, (page_height - 2.7) * cm)
    canvas.drawString(9 * cm, (page_height - 0.45) * cm, "ID týmového balíku:")

    canvas.setFont('DejaVuB', 12)
    canvas.drawString(4.5 * cm, (page_height - 1.2) * cm, "Balíček pro tým")
    canvas.setFont('DejaVu', 8)
    canvas.drawString(first_column * cm, (page_height - 2.3) * cm, "Tým: ")
    canvas.drawString(second_column * cm, (page_height - 2.3) * cm, team_package.team.name)
    canvas.drawString(first_column * cm, (page_height - 2.7) * cm, "ID krab.: ")
    canvas.drawString(second_column * cm, (page_height - 2.7) * cm, "%s" % team_package.box.id)

    im = Image(logo_file, 3.98 * cm, 1.5 * cm)
    im.drawOn(canvas, first_column * cm, (page_height - 2) * cm)

    offset = page_height - 3.2
    canvas.line(0, offset * cm, 100 * cm, offset * cm)
    for package_transaction in team_package.packagetransaction_set.all():
        user_attendance = package_transaction.user_attendance
        canvas.setFont('DejaVu', 8)
        canvas.drawString(first_column * cm, (offset - 1 * text_line_height) * cm, "Email:")
        canvas.drawString(second_column * cm, (offset - 1 * text_line_height) * cm, "%s" % user_attendance.userprofile.user.email)

        canvas.drawString(first_column * cm, (offset - 2 * text_line_height) * cm, "Jméno:")
        canvas.drawString(second_column * cm, (offset - 2 * text_line_height) * cm, "%s" % user_attendance.userprofile.user.get_full_name())

        canvas.drawString(first_column * cm, (offset - 3 * text_line_height) * cm, "Telefon:")
        canvas.drawString(second_column * cm, (offset - 3 * text_line_height) * cm, "%s" % user_attendance.userprofile.telephone)

        if package_transaction.t_shirt_size:
            canvas.setFont('DejaVuB', 10)
            canvas.drawString(third_column * cm, (offset - 1 * text_line_height - 0.1) * cm, package_transaction.t_shirt_size.__str__())

            if package_transaction.t_shirt_size.t_shirt_preview:
                svg_tshirt = svg2rlg(package_transaction.t_shirt_size.t_shirt_preview.path)
                svg_tshirt.scale(1.1 * cm / svg_tshirt.height, 1.1 * cm / svg_tshirt.width)
                svg_tshirt.drawOn(canvas, 12 * cm, (offset - 3 * text_line_height - 0.05) * cm)
        canvas.line(0, (offset - 3 * text_line_height - 0.2) * cm, 100 * cm, (offset - 3 * text_line_height - 0.2) * cm)

        offset -= 3 * text_line_height + 0.1
