from PyPDF2 import PdfFileReader

from django.core.files import File
from django.test import TestCase

from model_mommy import mommy

from .. import tasks


class TestTasks(TestCase):
    def setUp(self):
        self.delivery_batch = mommy.make(
            "DeliveryBatch",
            order_pdf=File(open("apps/t_shirt_delivery/test_files/batch198.pdf", "rb+")),
        )
        mommy.make(
            "SubsidiaryBox",
            delivery_batch=self.delivery_batch,
            customer_sheets=File(open("apps/t_shirt_delivery/test_files/customer_sheets_33431.pdf", "rb+")),
            id=33431,
        )
        mommy.make(
            "SubsidiaryBox",
            delivery_batch=self.delivery_batch,
            customer_sheets=File(open("apps/t_shirt_delivery/test_files/customer_sheets_33432.pdf", "rb+")),
            id=33432,
        )

    def test_delivery_batch_generate_pdf_for_opt(self):
        tasks.delivery_batch_generate_pdf_for_opt([self.delivery_batch.pk])
        self.delivery_batch.refresh_from_db()
        pdf = PdfFileReader(self.delivery_batch.combined_opt_pdf)
        self.assertEquals(pdf.pages.lengthFunction(), 4)

        pdf_string = pdf.pages[1].extractText()
        self.assertTrue("Do krab. †.:" in pdf_string)
        self.assertTrue("33431" in pdf_string)
        self.assertTrue("T38005" in pdf_string)

        pdf_string = pdf.pages[3].extractText()
        self.assertTrue("Do krab. †.:" in pdf_string)
        self.assertTrue("33432" in pdf_string)
        self.assertTrue("T38006" in pdf_string)
