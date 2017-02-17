# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2017 o.s. Auto*Mat
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

import csv


def generate_csv(csvfile, delivery_batch):
    spamwriter = csv.writer(csvfile)
    spamwriter.writerow([
        "Číslo dokladu",
        "Příjemce - Název",
        "Příjemce - Stát",
        "Příjemce - Město",
        "Příjemce - Ulice",
        "Příjemce - PSČ",
        "Přijemce - kontaktní osoba",
        "Příjemce - kontaktní email",
        "Přijemce - kontaktní telefon",
        "Datum svozu",
        "Reference",
        "EXW",
        "Dobírka (COD)",
        "Hodnota dobírky",
        "Variabilní symbol",
        "Hmotnost",
        "Objem",
        "Počet",
        "Popis zboží",
        "Druh obalu (zkratka)",
        "Typ zásilky",
    ])
    for subsidiary_box in delivery_batch.subsidiarybox_set.all():
        subsidiary = subsidiary_box.subsidiary
        user_attendance = subsidiary_box.get_representative_user_attendance()
        spamwriter.writerow([
            "",  # Číslo dokladu",
            user_attendance.userprofile.user.get_full_name() if user_attendance else "",
            "",  # CZ",
            subsidiary.address_city,
            "%s %s" % (subsidiary.address_street, subsidiary.address_street_number),
            subsidiary.address_psc,
            user_attendance.userprofile.user.get_full_name() if user_attendance else "",
            user_attendance.userprofile.user.email if user_attendance else "",
            user_attendance.userprofile.telephone if user_attendance else "",
            "",  # Datum svozu",
            "",  # Reference",
            "",  # EXW",
            "",  # Dobírka (COD)",
            "",  # Hodnota dobírky",
            subsidiary_box.id,
            subsidiary_box.get_weight(),
            subsidiary_box.get_volume(),
            1,
            "",  # Popis zboží",
            "",  # Druh obalu (zkratka)",
            "",  # Typ zásilky",
        ])
