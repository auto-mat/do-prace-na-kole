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
    UserProfile,
    Status,
)

import json


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

        self.maxDiff = None
        util.rebuild_denorm_models(UserAttendance.objects.filter())

    def test_get(self):

        self.client.force_login(
            User.objects.get(pk=3), settings.AUTHENTICATION_BACKENDS[0]
        )

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

        def test_permissions(self):
            self.client.force_login(
                User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
            )
            fa = reverse("fee-approval-list")
            response = self.client.get(fa)
            self.assertEqual(response.status_code, 403)


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2025, month=1, day=10),
)
class ApprovePaymentsViewTest(TestCase):

    fixtures = [
        "dump",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient(
            HTTP_HOST="testing-campaign.testserver", HTTP_REFERER="test-referer"
        )
        self.maxDiff = None

    def test_post(self):
        self.client.force_login(
            User.objects.get(pk=3), settings.AUTHENTICATION_BACKENDS[0]
        )
        post_data = {
            "ids": [5, 4],
        }
        response = self.client.post(
            reverse("approve-payments"), post_data, format="json", follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "message": "Approved 1 payments successfully",
                "approved_ids": [5],
            },
        )

        user_attendance = UserAttendance.objects.get(pk=5)
        payment = user_attendance.representative_payment
        self.assertEqual(payment.status, Status.COMPANY_ACCEPTS)

    def test_permissions(self):
        self.client.force_login(
            User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
        )
        post_data = {
            "ids": [5, 4],
        }
        response = self.client.post(
            reverse("approve-payments"), post_data, format="json", follow=True
        )
        self.assertEqual(response.status_code, 403)
