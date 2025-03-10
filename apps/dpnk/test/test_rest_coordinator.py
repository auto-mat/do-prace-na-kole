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
    Team,
)

from t_shirt_delivery.models import (
    BoxRequest,
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


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2025, month=1, day=10),
)
class GetAttendanceViewTest(TestCase):
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

        ga = reverse("get-attendance")
        response = self.client.get(ga)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "subsidiaries": [
                    {
                        "id": 4,
                        "address": {
                            "street": "Pobřežní",
                            "street_number": "1785",
                            "recipient": None,
                            "psc": "50301",
                            "city": "Hradec Králové",
                        },
                        "city": "Hradec Králové",
                        "teams": [
                            {
                                "id": 3,
                                "name": "Tým3",
                                "users": [
                                    {
                                        "id": 9,
                                        "first_name": "",
                                        "last_name": "",
                                        "nickname": "",
                                        "email": "",
                                        "company_admission_fee": 100,
                                        "payment_status": "done",
                                        "created": "2025-02-01 22:56:18.959000",
                                    },
                                    {
                                        "id": 8,
                                        "first_name": "",
                                        "last_name": "",
                                        "nickname": "",
                                        "email": "",
                                        "company_admission_fee": 100,
                                        "payment_status": "done",
                                        "created": "2025-02-01 22:55:46.917000",
                                    },
                                    {
                                        "id": 7,
                                        "first_name": "",
                                        "last_name": "",
                                        "nickname": "",
                                        "email": "",
                                        "company_admission_fee": 600,
                                        "payment_status": "none",
                                        "created": "2025-02-01 22:55:05.650000",
                                    },
                                    {
                                        "id": 6,
                                        "first_name": "",
                                        "last_name": "",
                                        "nickname": "",
                                        "email": "",
                                        "company_admission_fee": 100,
                                        "payment_status": "done",
                                        "created": "2025-02-01 22:54:08.194000",
                                    },
                                    {
                                        "id": 4,
                                        "first_name": "",
                                        "last_name": "",
                                        "nickname": "",
                                        "email": "b@centrum.cz",
                                        "company_admission_fee": 100,
                                        "payment_status": "done",
                                        "created": "2025-01-02 16:59:16.439000",
                                    },
                                ],
                            }
                        ],
                    },
                    {
                        "id": 2,
                        "address": {
                            "street": "Mečová",
                            "street_number": "475",
                            "recipient": None,
                            "psc": "60200",
                            "city": "Brno",
                        },
                        "city": "Brno",
                        "teams": [
                            {
                                "id": 2,
                                "name": "Tým2",
                                "users": [
                                    {
                                        "id": 5,
                                        "first_name": "",
                                        "last_name": "",
                                        "nickname": "",
                                        "email": "uzivatel@test.cz",
                                        "company_admission_fee": 100,
                                        "payment_status": "waiting",
                                        "created": "2025-01-15 18:24:19.594000",
                                    },
                                    {
                                        "id": 2,
                                        "first_name": "Petr",
                                        "last_name": "Nový",
                                        "nickname": "petr",
                                        "email": "p@centrum.cz",
                                        "company_admission_fee": 100,
                                        "payment_status": "done",
                                        "created": "2024-08-06 02:46:22.269000",
                                    },
                                ],
                            }
                        ],
                    },
                ]
            },
        )

        def test_permissions(self):
            self.client.force_login(
                User.objects.get(pk=1), settings.AUTHENTICATION_BACKENDS[0]
            )
            fa = reverse("get-attendance")
            response = self.client.get(fa)
            self.assertEqual(response.status_code, 403)


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2025, month=1, day=10),
)
class SubsidiariesViewTest(TestCase):
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

        sbd = reverse("subsidiary-coordinator-list")
        response = self.client.get(sbd)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 4,
                        "address": {
                            "street": "Pobřežní",
                            "street_number": "1785",
                            "recipient": None,
                            "psc": "50301",
                            "city": "Hradec Králové",
                        },
                        "city": "Hradec Králové",
                        "teams": [{"id": 3, "name": "Tým3"}],
                    },
                    {
                        "id": 2,
                        "address": {
                            "street": "Mečová",
                            "street_number": "475",
                            "recipient": None,
                            "psc": "60200",
                            "city": "Brno",
                        },
                        "city": "Brno",
                        "teams": [{"id": 2, "name": "Tým2"}],
                    },
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2025, month=1, day=10),
)
class SubsidiaryViewTest(TestCase):
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

        sbd = reverse("subsidiary-coordinator-detail", args=[2])
        response = self.client.get(sbd)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "id": 2,
                "address": {
                    "street": "Mečová",
                    "street_number": "475",
                    "recipient": None,
                    "psc": "60200",
                    "city": "Brno",
                },
                "city": "Brno",
                "teams": [{"id": 2, "name": "Tým2"}],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2025, month=1, day=10),
)
class TeamsViewTest(TestCase):
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

        sbd = reverse("subsidiary-team-list", args=[2])
        response = self.client.get(sbd)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 2,
                        "name": "Tým2",
                        "members": [
                            {
                                "id": 2,
                                "first_name": "Petr",
                                "last_name": "Nový",
                                "nickname": "petr",
                                "email": "p@centrum.cz",
                                "company_admission_fee": 100,
                                "payment_status": "done",
                                "created": "2024-08-06 02:46:22.269000",
                            },
                            {
                                "id": 5,
                                "first_name": "",
                                "last_name": "",
                                "nickname": "",
                                "email": "uzivatel@test.cz",
                                "company_admission_fee": 100,
                                "payment_status": "waiting",
                                "created": "2025-01-15 18:24:19.594000",
                            },
                        ],
                    }
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2025, month=1, day=10),
)
class TeamViewTest(TestCase):
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

        sbd = reverse("subsidiary-team-detail", args=[2, 2])
        response = self.client.get(sbd)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "id": 2,
                "name": "Tým2",
                "members": [
                    {
                        "id": 2,
                        "first_name": "Petr",
                        "last_name": "Nový",
                        "nickname": "petr",
                        "email": "p@centrum.cz",
                        "company_admission_fee": 100,
                        "payment_status": "done",
                        "created": "2024-08-06 02:46:22.269000",
                    },
                    {
                        "id": 5,
                        "first_name": "",
                        "last_name": "",
                        "nickname": "",
                        "email": "uzivatel@test.cz",
                        "company_admission_fee": 100,
                        "payment_status": "waiting",
                        "created": "2025-01-15 18:24:19.594000",
                    },
                ],
            },
        )

    def test_patch(self):

        self.client.force_login(
            User.objects.get(pk=3), settings.AUTHENTICATION_BACKENDS[0]
        )

        patch_data = {
            "name": "Tým100",
        }
        response = self.client.patch(
            reverse("subsidiary-team-detail", kwargs={"subsidiary_id": 2, "pk": 2}),
            patch_data,
            format="json",
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "id": 2,
                "name": "Tým100",
            },
        )

        team = Team.objects.get(pk=2)
        self.assertEqual(team.name, "Tým100")

    def test_delete(self):

        self.client.force_login(
            User.objects.get(pk=3), settings.AUTHENTICATION_BACKENDS[0]
        )

        response = self.client.delete(
            reverse("subsidiary-team-detail", kwargs={"subsidiary_id": 2, "pk": 2})
        )
        self.assertEqual(response.status_code, 400)

        self.assertTrue(Team.objects.filter(pk=2).exists())


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2025, month=1, day=10),
)
class MembersViewTest(TestCase):
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

        sbd = reverse("subsidiary-team-member-list", args=[2, 2])
        response = self.client.get(sbd)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 5,
                        "name": "uzivatel@test.cz",
                        "approved_for_team": "approved",
                    },
                    {"id": 2, "name": "petr", "approved_for_team": "approved"},
                ],
            },
        )


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2025, month=1, day=10),
)
class MemberViewTest(TestCase):
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

        sbd = reverse("subsidiary-team-member-detail", args=[2, 2, 5])
        response = self.client.get(sbd)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"id": 5, "name": "uzivatel@test.cz", "approved_for_team": "approved"},
        )

    def test_move_member_to_another_team(self):
        self.client.force_login(
            User.objects.get(pk=3), settings.AUTHENTICATION_BACKENDS[0]
        )

        patch_data = {
            "team_id": "3",
        }
        response = self.client.patch(
            reverse(
                "subsidiary-team-member-detail",
                kwargs={"subsidiary_id": 2, "team_id": 2, "pk": 2},
            ),
            patch_data,
            format="json",
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "campaign_id": 20,
                "id": 2,
                "name": "petr",
                "team_id": 3,
                "approved_for_team": "undecided",
            },
        )

        # approve new member
        patch_data_approved = {"approved_for_team": "approved"}
        response = self.client.patch(
            reverse(
                "subsidiary-team-member-detail",
                kwargs={"subsidiary_id": 4, "team_id": 3, "pk": 2},
            ),
            patch_data_approved,
            format="json",
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "campaign_id": 20,
                "id": 2,
                "name": "petr",
                "team_id": 3,
                "approved_for_team": "approved",
            },
        )

        user_attendance = UserAttendance.objects.get(pk=2)
        self.assertEqual(user_attendance.team_id, 3)

        # team has 5 members
        patch_data = {
            "team_id": "3",
        }
        response = self.client.patch(
            reverse(
                "subsidiary-team-member-detail",
                kwargs={"subsidiary_id": 2, "team_id": 2, "pk": 5},
            ),
            patch_data,
            format="json",
            follow=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(),
            {"team": ["Tento tým již má plný počet členů"]},
        )

    def test_move_members_between_companies(self):
        self.client.force_login(
            User.objects.get(pk=3), settings.AUTHENTICATION_BACKENDS[0]
        )

        patch_data = {
            "team_id": "1",
        }
        response = self.client.patch(
            reverse(
                "subsidiary-team-member-detail",
                kwargs={"subsidiary_id": 2, "team_id": 2, "pk": 2},
            ),
            patch_data,
            format="json",
            follow=True,
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(),
            {"non_field_errors": ["Cannot move members between companies"]},
        )

    def test_delete_member(self):
        self.client.force_login(
            User.objects.get(pk=3), settings.AUTHENTICATION_BACKENDS[0]
        )

        # delete members
        response = self.client.delete(
            reverse(
                "subsidiary-team-member-detail",
                kwargs={"subsidiary_id": 2, "team_id": 2, "pk": 5},
            ),
            format="json",
            follow=True,
        )
        self.assertEqual(response.status_code, 204)

        # delete non empty team
        response = self.client.delete(
            reverse("subsidiary-team-detail", kwargs={"subsidiary_id": 2, "pk": 2}),
            format="json",
            follow=True,
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(),
            {"detail": "Cannot delete a team with active members."},
        )

        response = self.client.delete(
            reverse(
                "subsidiary-team-member-detail",
                kwargs={"subsidiary_id": 2, "team_id": 2, "pk": 2},
            ),
            format="json",
            follow=True,
        )
        self.assertEqual(response.status_code, 204)

        # delete empty team
        response = self.client.delete(
            reverse("subsidiary-team-detail", kwargs={"subsidiary_id": 2, "pk": 2}),
            format="json",
            follow=True,
        )
        self.assertEqual(response.status_code, 204)


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2025, month=1, day=10),
)
class BoxRequestViewTest(TestCase):
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

    def test_post_get(self):

        self.client.force_login(
            User.objects.get(pk=3), settings.AUTHENTICATION_BACKENDS[0]
        )

        # post
        post_data = {"subsidiary_ids": [2]}
        response = self.client.post(
            reverse("package-request"), post_data, format="json", follow=True
        )

        self.assertEqual(response.status_code, 201)
        self.assertJSONEqual(
            response.content.decode(),
            {"message": "Created 1 box requests", "added_subsidiary_ids": [2]},
        )

        self.assertFalse(BoxRequest.objects.filter(pk=2).exists())

        # get
        pkg = reverse("package-request")
        response = self.client.get(pkg)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"subsidiary_ids": [2]},
        )

        # delete

        post_data = {"subsidiary_ids": [2]}
        response = self.client.post(
            reverse("package-request-remove"), post_data, format="json", follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"message": "Deleted 1 box requests", "deleted_subsidiary_ids": [2]},
        )
        self.assertEqual(response.status_code, 200)

        self.assertFalse(BoxRequest.objects.filter(pk=2).exists())
