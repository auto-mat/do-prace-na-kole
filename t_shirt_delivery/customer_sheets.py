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
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Image

from svg2rlg import svg2rlg


DIR = os.path.dirname(__file__)
logo_file = os.path.join(DIR, "static/img/logo.jpg")


def make_customer_sheets_pdf(outfile, subsidiary_box):
    canvas = Canvas(outfile, pagesize=A4)

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

    canvas.setFont('DejaVuB', 15)
    canvas.drawString(5.5 * cm, 28.2 * cm, subsidiary_box.delivery_batch.campaign.__str__())
    canvas.drawString(5.5 * cm, 27.5 * cm, "Krabice pro pobočku firmy")

    canvas.setFont('DejaVu', 10)
    canvas.drawString(5.5 * cm, 27 * cm, "%s" % (subsidiary.company))

    im = Image(logo_file, 3.98 * cm, 1.5 * cm)
    im.drawOn(canvas, 1 * cm, 27 * cm)

    canvas.setFont('DejaVu', 10)
    barcode = code128.Code128("K%s" % subsidiary_box.id, barWidth=0.5 * mm, barHeight=20 * mm, humanReadable=True)
    barcode.drawOn(canvas, 14.5 * cm, 26 * cm)
    canvas.drawString(15 * cm, 28.25 * cm, "ID krabice pro pobočku:")

    canvas.setFont('DejaVu', 10)
    canvas.drawString(2 * cm, (20 + 5 * 0.5) * cm, "Společnost:")
    canvas.drawString(5 * cm, (20 + 5 * 0.5) * cm, "%s" % subsidiary.company)

    canvas.drawString(2 * cm, (20 + 4 * 0.5) * cm, "IČO:")
    if subsidiary.company.ico:
        canvas.drawString(5 * cm, (20 + 4 * 0.5) * cm, "%s" % subsidiary.company.ico)

    canvas.drawString(2 * cm, (20 + 3 * 0.5) * cm, "Adresát:")
    canvas.drawString(5 * cm, (20 + 3 * 0.5) * cm, "%s" % subsidiary.address_recipient)

    canvas.drawString(2 * cm, (20 + 2 * 0.5) * cm, "Ulice:")
    canvas.drawString(5 * cm, (20 + 2 * 0.5) * cm, "%s %s" % (subsidiary.address_street, subsidiary.address_street_number))

    canvas.drawString(2 * cm, (20 + 1 * 0.5) * cm, "PSČ:")
    canvas.drawString(5 * cm, (20 + 1 * 0.5) * cm, "%s" % subsidiary.address_psc)

    canvas.drawString(2 * cm, (20 + 0 * 0.5) * cm, "Město:")
    canvas.drawString(5 * cm, (20 + 0 * 0.5) * cm, "%s" % subsidiary.address_city)


def make_team_sheet(team_package, canvas):
    barcode = code128.Code128("T%s" % team_package.id, barWidth=0.5 * mm, barHeight=20 * mm, humanReadable=True)
    barcode.drawOn(canvas, 14.5 * cm, 26 * cm)
    canvas.drawString(15 * cm, 28.25 * cm, "ID týmového balíku:")

    canvas.setFont('DejaVuB', 15)
    canvas.drawString(5.5 * cm, 28 * cm, "Balíček pro tým")
    canvas.setFont('DejaVu', 10)
    canvas.drawString(5.5 * cm, 27 * cm, team_package.team.name)

    im = Image(logo_file, 3.98 * cm, 1.5 * cm)
    im.drawOn(canvas, 1 * cm, 27 * cm)

    offset = 3
    for user_attendance in team_package.team.users.all():
        canvas.setFont('DejaVu', 10)
        canvas.drawString(2 * cm, (offset + 19 + 6 * 0.5) * cm, "Uživatelské jméno:")
        canvas.drawString(6 * cm, (offset + 19 + 6 * 0.5) * cm, "%s" % user_attendance.userprofile.user.username)

        canvas.drawString(2 * cm, (offset + 19 + 5 * 0.5) * cm, "Email:")
        canvas.drawString(6 * cm, (offset + 19 + 5 * 0.5) * cm, "%s" % user_attendance.userprofile.user.email)

        canvas.drawString(2 * cm, (offset + 19 + 4 * 0.5) * cm, "Jméno:")
        canvas.drawString(6 * cm, (offset + 19 + 4 * 0.5) * cm, "%s" % user_attendance.userprofile.user.get_full_name())

        nickname = user_attendance.userprofile.nickname
        if nickname:
            canvas.drawString(2 * cm, (offset + 19 + 3 * 0.5) * cm, "Přezdívka:")
            canvas.drawString(6 * cm, (offset + 19 + 3 * 0.5) * cm, "%s" % nickname)

        canvas.drawString(2 * cm, (offset + 19 + 2 * 0.5) * cm, "Telefon:")
        canvas.drawString(6 * cm, (offset + 19 + 2 * 0.5) * cm, "%s" % user_attendance.userprofile.telephone)

        realized = getattr(user_attendance.representative_payment, 'realized', None)
        if realized:
            canvas.drawString(2 * cm, (offset + 19 + 1 * 0.5) * cm, "Zaplaceno:")
            canvas.drawString(6 * cm, (offset + 19 + 1 * 0.5) * cm, "%s" % (realized.date()))

        if user_attendance.t_shirt_size:
            canvas.setFont('DejaVuB', 20)
            canvas.drawString(2 * cm, (offset + 18) * cm, user_attendance.t_shirt_size.__str__())

            if user_attendance.t_shirt_size.t_shirt_preview:
                svg_tshirt = svg2rlg(user_attendance.t_shirt_size.t_shirt_preview.path)
                svg_tshirt.scale(0.1, 0.1)
                svg_tshirt.drawOn(canvas, 15 * cm, (offset + 18) * cm)
        canvas.line(0, (offset + 22.5) * cm, 100 * cm, (offset + 22.5) * cm)

        offset -= 5
    canvas.line(0, (offset + 22.5) * cm, 100 * cm, (offset + 22.5) * cm)
