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
from django.core.exceptions import ValidationError
from django.test import TestCase

from dpnk import models

from model_mommy import mommy

from ..mommy_recipes import testing_campaign


class TestCompany(TestCase):
    def test_str(self):
        """
        Test that __str__ returns Company string
        """
        company = models.Company(name="Foo company")
        self.assertEqual(str(company), "Foo company")

    def test_company_address(self):
        """
        Test that company_address returns Company string
        """
        company = models.Company(name="Foo company", address_street="Foo street")
        self.assertEqual(company.company_address(), "Foo street")

    def test_clean(self):
        """
        Test that clean method doesn't raise error if company with similar name doesn't exist.
        """
        models.Company.objects.create(name="Foo company")
        company = models.Company(name="Foo company 1")
        company.clean()

    def test_clean_name_error(self):
        """
        Test that clean method raises error if company with similar name exists.
        """
        models.Company.objects.create(name="Foo company")
        company = models.Company(name="Foo Čömpany")
        with self.assertRaisesRegex(ValidationError, "Organizace s tímto názvem již existuje. Nemusíte tedy zakládat novou, vyberte tu stávající."):
            company.clean()

    def test_clean_name_self(self):
        """
        Test that clean method doesn't raise error if company with similar name is self.
        """
        company = models.Company.objects.create(name="Foo company")
        company.clean()

    def test_clean_ico_error(self):
        """
        Test that clean method raises error if company with same ico exists.
        """
        models.Company.objects.create(name="Foo", ico=12345)
        company = models.Company(name="Bar", ico=12345)
        with self.assertRaisesRegex(
            ValidationError,
            "Organizace s tímto IČO již existuje, nezakládemte prosím novou, ale vyberte jí prosím ze seznamu",
        ):
            company.clean()

    def test_clean_ico_error_not_changed(self):
        """
        Test that clean method doesn't raises error if company with same ico exists, but nothing changed on self.
        """
        models.Company.objects.create(name="Foo", ico=12345)
        company = models.Company(name="Bar", ico=12345)
        company.save()
        company.clean()

    def test_clean_ico_self(self):
        """
        Test that clean method doesn't raise error if company with same ico is self.
        """
        company = models.Company.objects.create(name="Foo", ico=12345)
        company.clean()

    def test_has_filled_contact_information_false(self):
        """
        Test that has_filled_contact_information returns False if address information is not complete
        """
        company = models.Company(name="Foo company")
        self.assertEqual(company.has_filled_contact_information(), False)

    def test_has_filled_contact_information(self):
        """
        Test that has_filled_contact_information returns True if address information is complete
        """
        company = models.Company(
            name="Foo company",
            ico=123,
            address_street="Foo street",
            address_street_number=123,
            address_psc=12345,
            address_city="Foo city",
        )
        self.assertEqual(company.has_filled_contact_information(), True)

    def test_admin_emails_blank(self):
        """
        Test that admin_emails returns "" if no company admin exists
        """
        company = models.Company(name="Foo company")
        self.assertEqual(company.admin_emails(None), "")

    def test_admin_emails(self):
        """
        Test that admin_emails returns "" if no company admin exists
        """
        company = mommy.make(
            "Company",
            company_admin__userprofile__user__email="foo@bar.cz",
            company_admin__campaign=testing_campaign,
        )
        self.assertEqual(company.admin_emails(testing_campaign()), "foo@bar.cz")

    def test_admin_telephones_blank(self):
        """
        Test that admin_telephones returns "" if no company admin exists
        """
        company = models.Company(name="Foo company")
        self.assertEqual(company.admin_telephones(None), "")

    def test_admin_telephones(self):
        """
        Test that admin_telephones returns "" if no company admin exists
        """
        company = mommy.make(
            "Company",
            company_admin__userprofile__telephone="1234234",
            company_admin__campaign=testing_campaign,
        )
        self.assertEqual(company.admin_telephones(testing_campaign()), "1234234")
