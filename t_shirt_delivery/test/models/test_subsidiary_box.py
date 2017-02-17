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
import os

from django.test import TestCase, override_settings

from dpnk.test.mommy_recipes import CampaignRecipe, UserAttendanceRecipe

from freezegun import freeze_time

from model_mommy import mommy


class TestSubsidiaryBox(TestCase):
    def test_str(self):
        """
        Test that __str__ returns SubsidiaryBox string
        """
        subsidiary_box = mommy.make(
            'SubsidiaryBox',
            subsidiary__address_street="Foo street",
            subsidiary__address_street_number="7",
            subsidiary__address_recipient="Foo recipient",
            subsidiary__address_city="Foo city",
            subsidiary__address_psc="12345",
            subsidiary__company__name="Foo company",
            subsidiary__city__name="Foo city",
        )
        self.assertEqual(
            str(subsidiary_box),
            "Krabice pro pobočku Foo recipient, Foo street 7, 123 45 Foo city - Foo city",
        )

    @freeze_time("2010-11-20")
    @override_settings(MEDIA_ROOT='/tmp/django_test')
    def test_create_customer_sheets(self):
        """
        Test that customer sheets are created
        """
        os.system("rm -f /tmp/django_test/customer_sheets/customer_sheets_123_2010-11-20.pdf")
        subsidiary_box = mommy.make(
            'SubsidiaryBox',
            id=123,
        )
        self.assertEqual(
            subsidiary_box.customer_sheets.name,
            "customer_sheets/customer_sheets_123_2010-11-20.pdf",
        )

    def test_box_parameters_zero(self):
        subsidiary_box = mommy.make('SubsidiaryBox')
        self.assertEqual(subsidiary_box.get_t_shirt_count(), 0)
        self.assertEqual(subsidiary_box.get_weight(), 0)
        self.assertEqual(subsidiary_box.get_volume(), 0)

    def test_box_parameters_non_zero(self):
        campaign = CampaignRecipe.make(
            package_weight=0.5,
            package_width=0.5,
            package_height=0.5,
            package_depth=0.5,
        )
        subsidiary_box = mommy.make(
            'SubsidiaryBox',
            teampackage_set=mommy.make(
                'TeamPackage',
                packagetransaction_set=mommy.make(
                    'PackageTransaction',
                    user_attendance=UserAttendanceRecipe.make(
                        campaign=campaign,
                    ),
                    _quantity=2,
                ),
                _quantity=1,
            ),
            delivery_batch__campaign=campaign,
        )
        self.assertEqual(subsidiary_box.get_t_shirt_count(), 2)
        self.assertEqual(subsidiary_box.get_weight(), 1)
        self.assertEqual(subsidiary_box.get_volume(), 0.25)

    def test_get_representative_user_attendance(self):
        campaign = CampaignRecipe.make()
        user_attendance = UserAttendanceRecipe.make(
            campaign=campaign,
        )
        subsidiary_box = mommy.make(
            'SubsidiaryBox',
            teampackage_set=[
                mommy.make(
                    'TeamPackage',
                    packagetransaction_set=mommy.make(
                        'PackageTransaction',
                        user_attendance=user_attendance,
                        _quantity=1,
                    ),
                ),
            ],
            delivery_batch__campaign=campaign,
        )
        self.assertEqual(subsidiary_box.get_representative_user_attendance(), user_attendance)

    def test_get_representative_user_attendance_no_package_transaction(self):
        campaign = CampaignRecipe.make()
        subsidiary_box = mommy.make(
            'SubsidiaryBox',
            teampackage_set=[
                mommy.make(
                    'TeamPackage',
                ),
            ],
            delivery_batch__campaign=campaign,
        )
        self.assertEqual(subsidiary_box.get_representative_user_attendance(), None)

    def test_get_representative_user_attendance_no_teampackage(self):
        campaign = CampaignRecipe.make()
        subsidiary_box = mommy.make(
            'SubsidiaryBox',
            delivery_batch__campaign=campaign,
        )
        self.assertEqual(subsidiary_box.get_representative_user_attendance(), None)
