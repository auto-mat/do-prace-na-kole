import requests
import logging

from django.test import TestCase

from model_mommy import mommy

from .mommy_recipes import testing_campaign

from ..fakturoid_invoice_gen import generate_invoice, create_api_session, delete_invoice, get_invoice, delete_subject

logger = logging.getLogger(__name__)


class TestGenerateFakturoidInvoice(TestCase):
    def setUp(self):
        self.fakturoid_account = "test"
        self.session, self.base_url = create_api_session(self.fakturoid_account)
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
          error_message = (
              "Delete Fakturoid '{model}' with id = {model_id}"
              " wasn't succesfull with Fakturoid account"
              " '{fakturoid_user_account_slug}' due error: '{error}'"
          )
          try:
              model = "Invoice"
              model_id = self.fa_invoice["custom_id"]
              delete_invoice(self.session, self.base_url, model_id)
              model = "Subject"
              model_id = self.fa_invoice["subject_id"]
              delete_subject(self.session, self.base_url, self.fa_invoice["subject_id"])
          except (
              requests.RequestException,
              requests.ConnectionError,
              requests.HTTPError,
              requests.URLRequired,
              requests.TooManyRedirects,
              requests.Timeout,
          ) as error:
              logger.error(
                  error_message.format(
                      model_id=model_id,
                      model=model,
                      fakturoid_user_account_slug=fa.slug,
                      error=error,
                  )
              )

    def test_generate_fakturoid_invoice(self):
        fa_invoice = generate_invoice(
            invoice=self.invoice,
            fakturoid_account=self.fakturoid_account,
        )
        self.assertIsNotNone(fa_invoice)
        self.fa_invoice = get_invoice(self.session, self.base_url, self.invoice.id)
        self.assertEqual(
            self.fa_invoice["client_name"],
            self.company_name,
        )
        self.assertEqual(len(self.fa_invoice["lines"]), 1)
        self.assertEqual(
            float(self.fa_invoice["lines"][0]["unit_price"]),
            self.payment_amount,
        )
