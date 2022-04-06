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
import re

from django.conf import settings
from django.test import Client, TestCase
from django.test.utils import override_settings
from django.urls import reverse

from dpnk.test.test_views import ViewsLogon
from dpnk.test.util import ClearCacheMixin
from dpnk.test.util import print_response  # noqa

from model_mommy import mommy

from .mommy_recipes import UserAttendanceRecipe, testing_campaign

from ..fakturoid_invoice_gen import get_fakturoid_api, generate_invoice
from .test_fakturoid_invoice_gen import TestGenerateFakturoidInvoice


class CompanyAdminViewTests(ViewsLogon):
    def test_edit_subsidiary(self):
        address = reverse("edit_subsidiary", kwargs={"pk": 1})
        response = self.client.get(address)
        self.assertContains(response, "Upravit adresu pobočky")
        self.assertContains(response, "11111")

    def test_edit_company(self):
        address = reverse("edit_company")
        response = self.client.get(address)
        self.assertContains(response, "Adresa společnosti")
        self.assertContains(response, "11111")
        self.assertContains(response, "CZ1234567890")


class SelectUsersPayTests(ClearCacheMixin, TestCase):
    def setUp(self):
        self.client = Client(HTTP_HOST="testing-campaign.example.com")
        self.user_attendance = UserAttendanceRecipe.make()
        mommy.make("Phase", phase_type="payment", campaign=testing_campaign)
        self.company_admin = mommy.make(
            "CompanyAdmin",
            userprofile=self.user_attendance.userprofile,
            company_admin_approved="approved",
            campaign=testing_campaign,
            administrated_company=self.user_attendance.team.subsidiary.company,
        )
        self.user_attendance.save()
        self.client.force_login(
            self.user_attendance.userprofile.user, settings.AUTHENTICATION_BACKENDS[0]
        )

    def test_not_allowed(self):
        self.company_admin.can_confirm_payments = False
        self.company_admin.save()
        response = self.client.get(reverse("company_admin_pay_for_users"))
        self.assertContains(
            response,
            "<div class='alert alert-danger'>Potvrzování plateb nemáte povoleno</div>",
            html=True,
            status_code=403,
        )


@override_settings(
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class InvoiceTests(ClearCacheMixin, TestCase):
    def setUp(self):
        self.fakturoid_account = "test"
        self.fa = get_fakturoid_api(account=self.fakturoid_account)
        self.payment_amount = 1500
        self.client = Client(HTTP_HOST="testing-campaign.example.com")
        self.user_attendance = UserAttendanceRecipe.make(
            team__subsidiary__company__address_street="Foo street",
            team__subsidiary__company__address_street_number="1",
            team__subsidiary__company__address_psc="12345",
            team__subsidiary__company__address_city="Foo city",
            team__subsidiary__company__name="Foo name",
            team__subsidiary__company__ico=1234234,
            team__campaign=testing_campaign,
        )
        self.company_admin = mommy.make(
            "CompanyAdmin",
            userprofile=self.user_attendance.userprofile,
            company_admin_approved="approved",
            campaign=testing_campaign,
            administrated_company=self.user_attendance.team.subsidiary.company,
        )
        mommy.make(
            "dpnk.Phase",
            campaign=testing_campaign,
            phase_type="invoices",
            date_from="2010-1-1",
            date_to="2020-1-1",
        )
        self.user_attendance.save()
        self.client.force_login(
            self.user_attendance.userprofile.user, settings.AUTHENTICATION_BACKENDS[0]
        )

    def tearDown(self):
        if hasattr(self, "fa_invoice") and self.fa_invoice:
            TestGenerateFakturoidInvoice.deleteFakturoidModels(
                fa=self.fa,
                fa_invoice=self.fa_invoice,
            )

    def test_get_blank(self):
        self.user_attendance.team.subsidiary.company.save()
        response = self.client.get(reverse("invoices"))
        self.assertContains(
            response,
            '<div class="alert alert-info">Nemáte žádné další soutěžící, pro které by bylo možné vytvořit fakturu</div>',
            html=True,
        )

    def test_get_unfilled_company_details(self):
        """Test, that if company doesn't have it's details filled in, the invoice couldn't be generated"""
        self.user_attendance.team.subsidiary.company.ico = None
        self.user_attendance.team.subsidiary.company.save()
        response = self.client.get(reverse("invoices"))
        self.assertContains(
            response,
            "<div class='alert alert-danger'>"
            "Před vystavením faktury "
            "<a href='/spolecnost/editovat_spolecnost/'>prosím vyplňte údaje o Vaší společnosti</a>."
            "</div>",
            html=True,
            status_code=403,
        )

    def test_get_not_allowed(self):
        """Test, that if company doesn't have it's details filled in, the invoice couldn't be generated"""
        self.company_admin.can_confirm_payments = False
        self.company_admin.save()
        response = self.client.get(reverse("invoices"))
        self.assertContains(
            response,
            "<div class='alert alert-danger'>"
            "Vystavování faktur nemáte povoleno"
            "</div>",
            html=True,
            status_code=403,
        )

    def test_get_invoice_present(self):
        invoice = mommy.make(
            "Invoice",
            company=self.user_attendance.team.subsidiary.company,
            campaign=testing_campaign,
            exposure_date=datetime.date(2010, 10, 10),
            variable_symbol=2010111,
            payment__amount=self.payment_amount,
        )
        mommy.make(
            "Payment",
            user_attendance__campaign=testing_campaign,
            user_attendance__team__campaign=testing_campaign,
            invoice=invoice,
            user_attendance__team__name="Foo team",
            user_attendance__userprofile__user__email="test@email.cz",
            amount=self.payment_amount,
        )
        self.fa_invoice = generate_invoice(
            invoice=invoice,
            fakturoid_account=self.fakturoid_account,
        )
        self.assertIsNotNone(self.fa_invoice)
        response = self.client.get(reverse("invoices"))
        self.assertContains(
            response,
            "<tr>"
            "<td>10. října 2010</td>"
            "<td>"
            '<a href="/media/upload/%s">PDF soubor</a>'
            "<br/>"
            '(<a href="/media/upload/%s" download="faktura_None_%s_pohoda.xml">Pohoda&nbsp;XML</a>)'
            "<br/>"
            '(<a href="%s">Fakturoid PDF soubor</a>)'
            "</td>"
            "<td>1</td>"
            "<td>2010111</td>"
            "<td>0,0</td>"
            "<td>Zaplacení nepotvrzeno</td>"
            "</tr>"
            % (
                invoice.invoice_pdf,
                invoice.invoice_xml,
                invoice.id,
                self.fa_invoice.public_html_url,
            ),
            html=True,
        )

    def test_get_invoice_present_paid(self):
        invoice = mommy.make(
            "Invoice",
            company=self.user_attendance.team.subsidiary.company,
            campaign=testing_campaign,
            exposure_date=datetime.date(2010, 10, 10),
            paid_date=datetime.date(2010, 10, 10),
            variable_symbol=2010111,
            payment__amount=self.payment_amount,
        )
        mommy.make(
            "Payment",
            user_attendance__campaign=testing_campaign,
            user_attendance__team__campaign=testing_campaign,
            invoice=invoice,
            user_attendance__team__name="Foo team",
            user_attendance__userprofile__user__email="test@email.cz",
            amount=self.payment_amount,
        )
        self.fa_invoice = generate_invoice(
            invoice=invoice,
            fakturoid_account=self.fakturoid_account,
        )
        self.assertIsNotNone(self.fa_invoice)
        response = self.client.get(reverse("invoices"))
        self.assertContains(
            response,
            "<tr>"
            "<td>10. října 2010</td>"
            "<td>"
            '<a href="/media/upload/%s">PDF soubor</a>'
            "<br/>"
            '(<a href="/media/upload/%s" download="faktura_None_%s_pohoda.xml">Pohoda&nbsp;XML</a>)'
            "<br/>"
            '(<a href="%s">Fakturoid PDF soubor</a>)'
            "</td>"
            "<td>1</td>"
            "<td>2010111</td>"
            "<td>0,0</td>"
            "<td>10. října 2010</td>"
            "</tr>"
            % (
                invoice.invoice_pdf,
                invoice.invoice_xml,
                invoice.id,
                self.fa_invoice.public_html_url,
            ),
            html=True,
        )

    def test_get_payments_present(self):
        mommy.make(
            "Payment",
            status=1005,
            pay_type="fc",
            user_attendance__team__subsidiary__company=self.user_attendance.team.subsidiary.company,
            user_attendance__campaign=testing_campaign,
            user_attendance__team__campaign=testing_campaign,
            user_attendance__userprofile__user__first_name="Foo",
            user_attendance__userprofile__user__last_name="User",
            amount=123,
        )
        response = self.client.get(reverse("invoices"))
        self.assertContains(
            response,
            "<h2>Vystavit novou fakturu</h2>",
            html=True,
        )
        self.assertContains(
            response,
            "<tr> <td>Foo User</td> <td>123 Kč</td> </tr>",
            html=True,
        )

    def test_post(self):
        mommy.make(
            "Payment",
            status=1005,
            pay_type="fc",
            user_attendance__team__subsidiary__company=self.user_attendance.team.subsidiary.company,
            user_attendance__campaign=testing_campaign,
            user_attendance__team__campaign=testing_campaign,
            user_attendance__userprofile__user__first_name="Foo",
            user_attendance__userprofile__user__last_name="User",
            amount=123,
        )
        response = self.client.post(
            reverse("invoices"),
            {"create_invoice": True},
            follow=True,
        )
        self.assertRedirects(response, reverse("invoices"))
        fa_invoice = re.search(r"fakturoid(.*?)\"", response.content.decode())
        if fa_invoice:
            fa_invoice_number = fa_invoice.group(0).rsplit("/", 1)[-1].rstrip('"')
            self.fa_invoice = list(self.fa.invoices(number=fa_invoice_number))[0]
        self.assertContains(
            response,
            "<td>Zaplacení nepotvrzeno</td>",
            html=True,
        )
