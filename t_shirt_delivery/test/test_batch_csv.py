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

from django.core.files.temp import NamedTemporaryFile
from django.test import TestCase

from dpnk.test.mommy_recipes import CampaignRecipe, UserAttendanceRecipe

from model_mommy import mommy

from t_shirt_delivery import batch_csv


class TestBatchCsv(TestCase):
    def setUp(self):
        campaign = CampaignRecipe.make(
            package_weight=0.5,
            package_width=0.5,
            package_height=0.5,
            package_depth=0.5,
        )
        user_attendance = UserAttendanceRecipe.make(
            campaign=campaign,
            userprofile__user__username="test_username ",
            userprofile__user__first_name="Testing",
            userprofile__user__email="foo@email.cz",
            userprofile__user__last_name="User ",
            userprofile__nickname="Nick",
            userprofile__telephone=123456789,
        )
        team = mommy.make(
            "dpnk.Team",
            campaign=campaign,
            name="Testin team",
        )

        self.delivery_batch = mommy.prepare(
            "DeliveryBatch",
            campaign=campaign,
        )
        self.delivery_batch.add_packages_on_save = False
        self.delivery_batch.save()
        self.subsidiary_box = mommy.make(
            "SubsidiaryBox",
            subsidiary__address_street="Foo street",
            subsidiary__address_psc=12234,
            subsidiary__address_street_number="123",
            subsidiary__address_city="Foo city",
            subsidiary__address_recipient="Foo recipient",
            subsidiary__id=123,
            subsidiary__company__name="Foo company",
            subsidiary__company__ico=1231321313,
            delivery_batch=self.delivery_batch,
            id=1603824,
        )
        mommy.make(
            "TeamPackage",
            box=self.subsidiary_box,
            team=team,
            packagetransaction_set=mommy.make(
                'PackageTransaction',
                user_attendance=user_attendance,
                _quantity=1,
            ),
        )

    def test_batch_csv(self):
        """ Test generating batch CSV """
        batch = self.delivery_batch
        self.subsidiary_box.subsidiary.box_addressee_name = ""
        self.subsidiary_box.subsidiary.save()
        with NamedTemporaryFile(mode="w", delete=False) as temp_file:
            batch_csv.generate_csv(temp_file, batch)
        with open(temp_file.name) as temp_file:
            csv_string_lines = temp_file.read().split("\n")
            self.assertEquals(
                'Číslo dokladu;Příjemce - Název;Příjemce - Stát;'
                'Příjemce - Město;Příjemce - Ulice;Příjemce - PSČ;'
                'Přijemce - kontaktní osoba;Příjemce - kontaktní email;'
                'Přijemce - kontaktní telefon;Datum svozu;Reference;'
                'EXW;Dobírka (COD);Hodnota dobírky;Variabilní symbol;'
                'Hmotnost;Objem;Počet;Popis zboží;Druh obalu (zkratka);Typ zásilky',
                csv_string_lines[0],
            )
            self.assertEquals(
                ';Foo recipient (Foo company);CZ;Foo city;Foo street 123;12234;Testing User;'
                'foo@email.cz;123456789;;;;;;1603824;0.5;0.125;1;;;',
                csv_string_lines[1],
            )
        os.system("rm %s" % temp_file.name)

    def test_batch_csv_addressee(self):
        """ Test, that if subsidiary.addressee_name is filled, it will appear in CSV """
        batch = self.delivery_batch
        self.subsidiary_box.subsidiary.box_addressee_name = "Addressee name"
        self.subsidiary_box.subsidiary.box_addressee_email = "addressee@email.cz"
        self.subsidiary_box.subsidiary.box_addressee_telephone = "987654321"
        self.subsidiary_box.subsidiary.save()
        with NamedTemporaryFile(mode="w", delete=False) as temp_file:
            batch_csv.generate_csv(temp_file, batch)
        with open(temp_file.name) as temp_file:
            csv_string_lines = temp_file.read().split("\n")
            self.assertEquals(
                ';Foo recipient (Foo company);CZ;Foo city;Foo street 123;12234;Addressee name;'
                'addressee@email.cz;987654321;;;;;;1603824;0.5;0.125;1;;;',
                csv_string_lines[1],
            )
        os.system("rm %s" % temp_file.name)
