import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from rest_framework.test import APIClient

from dpnk import util

from dpnk.models import (
    UserAttendance,
)


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2025, month=1, day=10),
)
class FeeApprovalSetTest(TestCase):
    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.client.force_login(
            User.objects.get(pk=3), settings.AUTHENTICATION_BACKENDS[0]
        )
        self.maxDiff = None
        util.rebuild_denorm_models(UserAttendance.objects.filter())

    def test_get(self):
        fa = reverse("fee-approval-list")
        response = self.client.get(fa)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 5,
                        "company_admission_fee": 100,
                        "first_name": "",
                        "last_name": "",
                        "nickname": "None",
                        "email": "uzivatel@test.cz",
                        "city": "Brno",
                        "created": "2025-01-15 18:24:19.594000",
                    }
                ],
            },
        )
