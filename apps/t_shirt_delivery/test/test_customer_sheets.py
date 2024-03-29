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
import datetime
from itertools import cycle

from PyPDF2 import PdfFileReader

from django.core.files.temp import NamedTemporaryFile
from django.test import TestCase

from dpnk.test.mommy_recipes import UserAttendanceRecipe, testing_campaign

from model_mommy import mommy
from model_mommy.recipe import seq

from t_shirt_delivery import customer_sheets


class TestCreateCustomerSheets(TestCase):
    def setUp(self):
        t_shirt_size = mommy.make(
            "TShirtSize",
            name="Testing t-shirt size",
            campaign=testing_campaign,
            # t_shirt_preview=SimpleUploadedFile(
            #    "t_shirt_preview.svg",
            #    b'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600">'
            #    b'<text>Example SVG text 1</text>'
            #    b'<rect x="0" y="0" width="600" height="600"/>'
            #    b'</svg>',
            #    ),
            ship=True,
        )
        mommy.make(
            "price_level.PriceLevel",
            takes_effect_on=datetime.date(year=2017, month=1, day=1),
            pricable=testing_campaign,
        )
        user_attendances = UserAttendanceRecipe.make(
            campaign=testing_campaign,
            userprofile__user__username=seq("test_username "),
            userprofile__user__first_name="Testing",
            userprofile__user__email="foo@email.cz",
            userprofile__user__last_name=seq("User "),
            userprofile__nickname=cycle(["Nick", None]),
            userprofile__telephone=seq(123456789),
            t_shirt_size=t_shirt_size,
            transactions=[
                mommy.make(
                    "Payment",
                    status=99,
                    realized=datetime.date(year=2017, month=2, day=1),
                ),
            ],
            _quantity=5,
        )
        self.subsidiary_box = mommy.make(
            "SubsidiaryBox",
            subsidiary__address_street="Foo street",
            subsidiary__address_psc=12234,
            subsidiary__address_street_number="123",
            subsidiary__address_city="Foo city",
            subsidiary__address_recipient="Foo recipient",
            subsidiary__id=123,
            delivery_batch__campaign=testing_campaign,
            id=1603824,
        )
        mommy.make(
            "TeamPackage",
            box=self.subsidiary_box,
            team__users=user_attendances,
            team__name="Foo team with max name lenth fooo foo foo foo fooo",
            team__campaign=testing_campaign,
            team__subsidiary__company__name="Foo company",
            team__subsidiary__company__ico=1231321313,
            id=34567812,
            packagetransaction_set=mommy.make(
                "PackageTransaction",
                t_shirt_size=t_shirt_size,
                user_attendance=cycle(user_attendances),
                _quantity=5,
            ),
        )

    def test_make_customer_sheets_pdf(self):
        with NamedTemporaryFile() as temp_file:
            customer_sheets.make_customer_sheets_pdf(temp_file, self.subsidiary_box)
            pdf = PdfFileReader(temp_file)
            pdf_string = pdf.pages[0].extractText()
            self.assertTrue("1603824" in pdf_string)
            self.assertTrue("Foo company" in pdf_string)
            self.assertTrue("T34567812" in pdf_string)
            self.assertTrue("Testing t-shirt size" in pdf_string)
            self.assertTrue("Testing User 1" in pdf_string)
            self.assertTrue("foo@email.cz" in pdf_string)
            self.assertTrue("Foo team with max name lenth" in pdf_string)
            self.assertTrue("123456794" in pdf_string)
            self.assertTrue("Testing t-shirt size" in pdf_string)
            # Previews on customer sheets have been disabled
            # self.assertTrue("Example SVG text 1" in pdf_string)
