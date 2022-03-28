from django.test import TestCase

from model_mommy import mommy

from .mommy_recipes import testing_campaign

from ..fakturoid_invoice_gen import get_fakturoid_api, generate_invoice


class IvoiceDoesNotExist(Exception):
    pass


class TestGenerateFakturoidInvoice(TestCase):
    def setUp(self):
        self.fakturoid_account = "test"
        self.fa = get_fakturoid_api(account=self.fakturoid_account)
        self.company_name = "Test s.r.o."
        self.payment_amount = 1500
        self.invoice = mommy.make(
            "Invoice",
            campaign=testing_campaign,
            company__name=self.company_name,
            payment__amount=self.payment_amount,
        )
        mommy.make(
            "Payment",
            user_attendance__campaign=testing_campaign,
            user_attendance__team__campaign=testing_campaign,
            invoice=self.invoice,
            user_attendance__team__name="Foo team",
            user_attendance__userprofile__user__email="test@email.cz",
            amount=self.payment_amount,
        )

    def tearDown(self):
        if self.fa_invoice:
            self.fa.delete(self.fa_invoice)
            self.fa.delete(
                self.fa.subject(self.fa_invoice.subject_id),
            )

    def test_generate_fakturoid_invoice(self):
        generate_invoice(
            invoice=self.invoice,
            fakturoid_account=self.fakturoid_account,
        )
        try:
            self.fa_invoice = list(
                self.fa.invoices(custom_id=self.invoice.id),
            )[0]
            self.assertEqual(
                self.fa_invoice.client_name,
                self.company_name,
            )
            self.assertEqual(len(self.fa_invoice.lines), 1)
            self.assertEqual(
                self.fa_invoice.lines[0].unit_price,
                self.payment_amount,
            )
        except IndexError:
            self.fa_invoice = None
            raise IvoiceDoesNotExist(
                "Invoice with 'custom_id' = {self.fa_invoice.custom_id}"
                " doesn't exist."
            )
