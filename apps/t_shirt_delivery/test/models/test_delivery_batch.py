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
import datetime
import os

from PyPDF2 import PdfFileReader

from django.test import TestCase, override_settings

from dpnk.test.mommy_recipes import (
    CampaignRecipe,
    UserAttendanceRecipe,
    testing_campaign,
)

from model_mommy import mommy
from model_mommy.recipe import seq

from t_shirt_delivery.models import PackageTransaction


class TestDeliveryBatch(TestCase):
    def test_str(self):
        """
        Test that __str__ returns DeliveryBatch string
        """
        delivery_batch = mommy.make(
            "DeliveryBatch",
            id=11,
            created=datetime.datetime(
                year=2016, month=1, day=1, hour=1, minute=1, second=1
            ),
        )
        self.assertEqual(
            str(delivery_batch), "id 11 vytvořená 2016-01-01 01:01:01",
        )

    def test_box_count_zero(self):
        """
        Test box_count() with zero boxes
        """
        delivery_batch = mommy.make("DeliveryBatch")
        self.assertEqual(delivery_batch.box_count(), 0)

    def test_box_count_non_zero(self):
        """
        Test box_count() with nonzero boxes
        """
        campaign = CampaignRecipe.make(name="Testin campaign")
        delivery_batch = mommy.make(
            "DeliveryBatch",
            subsidiarybox_set=mommy.prepare("SubsidiaryBox", _quantity=2,),
            campaign=campaign,
        )
        self.assertEqual(delivery_batch.box_count(), 2)

    @override_settings(MEDIA_ROOT="/tmp/django_test")
    def test_batch_csv_sheets(self):
        """
        Test that batch CSV is created
        """
        os.system(
            "rm -f /tmp/django_test/csv_delivery/delivery_batch_123_2010-11-20.csv"
        )
        delivery_batch = mommy.make(
            "DeliveryBatch", created=datetime.date(year=2010, month=11, day=20), id=123,
        )
        self.assertEqual(
            delivery_batch.tnt_order.name,
            "csv_delivery/delivery_batch_123_2010-11-20.csv",
        )

    def test_create_packages(self):
        """
        Test that packages are created on save
        """
        city = mommy.make("City", name="Foo city")
        subsidiary = mommy.make(
            "Subsidiary",
            address_street="Foo street",
            address_psc=12234,
            address_street_number="123",
            address_city="Foo city",
            city=city,
            address_recipient="Foo recipient",
        )
        user_attendance = UserAttendanceRecipe.make(
            userprofile__user__first_name="Foo",
            userprofile__user__last_name=seq("Name "),
            approved_for_team="approved",
            team__subsidiary=subsidiary,
            team__name=seq("Team "),
            discount_coupon__discount=100,
            discount_coupon__coupon_type__name="Discount",
            _quantity=2,
        )
        delivery_batch = mommy.make(
            "DeliveryBatch", campaign=user_attendance[0].campaign,
        )
        self.assertQuerysetEqual(
            delivery_batch.subsidiarybox_set.all(),
            (
                "<SubsidiaryBox: Krabice pro pobočku Foo recipient, Foo street 123, 122 34 Foo city - Foo city>",
            ),
        )
        self.assertQuerysetEqual(
            delivery_batch.subsidiarybox_set.first()
            .teampackage_set.all()
            .order_by("pk"),
            [
                "<TeamPackage: Balíček pro tým Team 1>",
                "<TeamPackage: Balíček pro tým Team 2>",
            ],
        )
        self.assertQuerysetEqual(
            PackageTransaction.objects.all().order_by("pk"),
            [
                "<PackageTransaction: Package transaction for user Foo Name 1>",
                "<PackageTransaction: Package transaction for user Foo Name 2>",
            ],
        )
        # Test that PackageTransaction object is created
        self.assertEqual(
            PackageTransaction.objects.first().team_package.box.delivery_batch,
            delivery_batch,
        )

        # Test that PDF is created correctly - with the t-shirt sizes for all UserAttendance objects
        pdf = PdfFileReader(delivery_batch.subsidiarybox_set.first().customer_sheets)
        pdf_string = pdf.pages[0].extractText()
        self.assertTrue("Foo Name" in pdf_string)

    def test_create_packages_max_packages(self):
        """
        Test that packages are created on save.
        If package_max_count is reached, the box must be split into two.
        """
        city = mommy.make("City", name="Foo city")
        subsidiary = mommy.make(
            "Subsidiary",
            address_street="Foo street",
            address_psc=12234,
            address_street_number="123",
            address_city="Foo city",
            city=city,
            address_recipient="Foo recipient",
        )
        user_attendance = UserAttendanceRecipe.make(
            userprofile__user__first_name="Foo",
            userprofile__user__last_name=seq("Name "),
            approved_for_team="approved",
            team__subsidiary=subsidiary,
            team__name=seq("Team "),
            discount_coupon__discount=100,
            discount_coupon__coupon_type__name="Discount",
            _quantity=2,
        )
        user_attendance[0].campaign.package_max_count = 1
        user_attendance[0].campaign.save()
        delivery_batch = mommy.make(
            "DeliveryBatch", campaign=user_attendance[0].campaign,
        )
        subsidiary_boxes = delivery_batch.subsidiarybox_set
        self.assertQuerysetEqual(
            subsidiary_boxes.all().order_by("pk"),
            (
                "<SubsidiaryBox: Krabice pro pobočku Foo recipient, Foo street 123, 122 34 Foo city - Foo city>",
                "<SubsidiaryBox: Krabice pro pobočku Foo recipient, Foo street 123, 122 34 Foo city - Foo city>",
            ),
        )
        pdf = PdfFileReader(subsidiary_boxes.all()[0].customer_sheets)
        pdf_string = pdf.pages[0].extractText()
        self.assertTrue("Foo Name 1" in pdf_string)

        pdf = PdfFileReader(subsidiary_boxes.all()[1].customer_sheets)
        pdf_string = pdf.pages[0].extractText()
        self.assertTrue("Foo Name 2" in pdf_string)

        self.assertQuerysetEqual(
            subsidiary_boxes.first().teampackage_set.all().order_by("pk"),
            ["<TeamPackage: Balíček pro tým Team 1>",],
        )
        self.assertQuerysetEqual(
            PackageTransaction.objects.all().order_by("pk"),
            [
                "<PackageTransaction: Package transaction for user Foo Name 1>",
                "<PackageTransaction: Package transaction for user Foo Name 2>",
            ],
        )

    def test_create_packages_large_team(self):
        """
        Test that packages are created on save.
        Also unapproved team members will get package.
        If there is more than 5 members of the team, the package should be divided.
        """
        city = mommy.make("City", name="Foo city")
        subsidiary = mommy.make(
            "Subsidiary",
            address_street="Foo street",
            address_psc=12234,
            address_street_number="123",
            address_city="Foo city",
            city=city,
            address_recipient="Foo recipient",
        )
        team = mommy.make(
            "Team", subsidiary=subsidiary, name="Foo Team", campaign=testing_campaign,
        )
        user_attendance = UserAttendanceRecipe.make(
            userprofile__user__first_name="Foo",
            userprofile__user__last_name=seq("Name "),
            approved_for_team="undecided",
            team=team,
            discount_coupon__discount=100,
            discount_coupon__coupon_type__name="Discount",
            _quantity=6,
        )
        user_attendance[0].campaign.package_max_count = 1
        user_attendance[0].campaign.save()
        delivery_batch = mommy.make(
            "DeliveryBatch", campaign=user_attendance[0].campaign,
        )
        self.assertQuerysetEqual(
            delivery_batch.subsidiarybox_set.all().order_by("pk"),
            (
                "<SubsidiaryBox: Krabice pro pobočku Foo recipient, Foo street 123, 122 34 Foo city - Foo city>",
            ),
        )
        team_packages = delivery_batch.subsidiarybox_set.first().teampackage_set.all()
        self.assertQuerysetEqual(
            team_packages.order_by("pk"),
            [
                "<TeamPackage: Balíček pro tým Foo Team>",
                "<TeamPackage: Balíček pro tým Foo Team>",
            ],
        )
        self.assertQuerysetEqual(
            team_packages[0].packagetransaction_set.all().order_by("pk"),
            [
                "<PackageTransaction: Package transaction for user Foo Name 1>",
                "<PackageTransaction: Package transaction for user Foo Name 2>",
                "<PackageTransaction: Package transaction for user Foo Name 3>",
                "<PackageTransaction: Package transaction for user Foo Name 4>",
                "<PackageTransaction: Package transaction for user Foo Name 5>",
            ],
        )
        self.assertQuerysetEqual(
            team_packages[1].packagetransaction_set.all().order_by("pk"),
            ["<PackageTransaction: Package transaction for user Foo Name 6>",],
        )

    def test_create_packages_not_member(self):
        """
        Test that packages are created on save
        PackageTransaction should be added only
        if UserAttendance has paid
        and the t_shirt is shipped
        the approval for tema should not matter
        """
        mommy.make(
            "PriceLevel",
            pricable=testing_campaign,
            price=100,
            takes_effect_on=datetime.date(year=2010, month=2, day=1),
        )
        user_attendance = UserAttendanceRecipe.make(
            transactions=[mommy.make("Payment", status=1)],
            userprofile__user__first_name="Foo",
            campaign=testing_campaign,
        )
        user_attendance.save()
        self.assertTrue(user_attendance.payment_status, "none")
        added_user_attendance = UserAttendanceRecipe.make(
            approved_for_team="undecided",
            transactions=[mommy.make("Payment", status=99)],
            userprofile__user__first_name="Bar",
            campaign=testing_campaign,
        )
        added_user_attendance.save()
        self.assertTrue(added_user_attendance.payment_status, "done")
        UserAttendanceRecipe.make(
            t_shirt_size__ship=False,
            approved_for_team="approved",
            transactions=[mommy.make("Payment", status=99)],
            userprofile__user__first_name="Baz",
            campaign=testing_campaign,
        )
        mommy.make(
            "DeliveryBatch", campaign=user_attendance.campaign,
        )
        self.assertEqual(
            PackageTransaction.objects.get().user_attendance,  # Only one package transaction is created
            added_user_attendance,
        )
