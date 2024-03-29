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
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.urls import reverse

from dpnk.views_permission_mixins import (
    GroupRequiredResponseMixin,
    MustBeApprovedForTeamMixin,
    MustBeCompanyAdminMixin,
    MustBeInPhaseMixin,
    MustHaveTeamMixin,
)

from freezegun import freeze_time

from model_mommy import mommy

from .mommy_recipes import testing_campaign
from .mommy.mommy import Fixtures


class FakeViewClass(object):
    def dispatch(request, *args, **kwargs):
        return "superdispatch"


class MustBeInPhase(MustBeInPhaseMixin, FakeViewClass):
    must_be_in_phase = "competition"


class MustBeInPhaseMixinTest(TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

    @freeze_time("2011-01-01")
    def test_is_in_phase(self):
        self.request.campaign = testing_campaign()
        mixin = MustBeInPhase()
        self.assertEqual(mixin.dispatch(self.request), "superdispatch")

    @freeze_time("2009-01-01")
    def test_is_phase_hasnt_started(self):
        self.request.campaign = testing_campaign()
        mixin = MustBeInPhase()
        with self.assertRaisesRegex(
            PermissionDenied,
            "Ještě nenastal čas, kdy by se měla tato stránka zobrazit.<br/>Stránka se zobrazí až 01.01.2010",
        ):
            mixin.dispatch(self.request)

    @freeze_time("2029-01-01")
    def test_is_phase_after_end(self):
        self.request.campaign = testing_campaign()
        mixin = MustBeInPhase()
        with self.assertRaisesRegex(
            PermissionDenied,
            "Pro jahody ke dvanácti měsíčkům na kole dojedete i mimo sezónu, ale na novou soutěž musíte ještě chvilku počkat.",
        ):
            mixin.dispatch(self.request)

    def test_isnt_in_phase(self):
        self.request.campaign = mommy.make("Campaign")
        mixin = MustBeInPhase()
        with self.assertRaisesRegex(
            PermissionDenied,
            "Tato stránka nemůže být v této kampani zobrazena. Neexistuje v ní fáze soutěžní.",
        ):
            mixin.dispatch(self.request)


class MustBeCompanyAdmin(MustBeCompanyAdminMixin, FakeViewClass):
    pass


class MustBeCompanyAdminMixinTest(TestCase):
    def setUp(self):
        super().setUp()
        self.objs = Fixtures(
            {
                "campaigns",
                "phases",
                "competitions",
            }
        )
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

    def test_no_user_attendance(self):
        self.request.user_attendance = None
        mixin = MustBeCompanyAdmin()
        self.assertEqual(mixin.dispatch(self.request), "superdispatch")

    def test_is_admin_approved(self):
        self.request.user_attendance = mommy.make(
            "UserAttendance",
            userprofile__company_admin=[
                mommy.make(
                    "CompanyAdmin",
                    company_admin_approved="approved",
                    campaign=testing_campaign(),
                )
            ],
            campaign=testing_campaign,
        )
        self.request.user_attendance.save()
        mixin = MustBeCompanyAdmin()
        self.assertEqual(mixin.dispatch(self.request), "superdispatch")

    def test_is_admin_undecided(self):
        self.request.user_attendance = mommy.make(
            "UserAttendance",
            userprofile__company_admin=[
                mommy.make(
                    "CompanyAdmin",
                    company_admin_approved="undecided",
                    campaign=testing_campaign,
                )
            ],
            campaign=testing_campaign,
        )
        self.request.user_attendance.save()
        mixin = MustBeCompanyAdmin()
        with self.assertRaisesRegex(
            PermissionDenied,
            "Tato stránka je určená pouze ověřeným firemním koordinátorům.",
        ):
            mixin.dispatch(self.request)

    def test_is_admin_denied(self):
        self.request.user_attendance = mommy.make(
            "UserAttendance",
            userprofile__company_admin=[
                mommy.make(
                    "CompanyAdmin",
                    company_admin_approved="denied",
                    campaign=testing_campaign,
                )
            ],
            campaign=testing_campaign,
        )
        self.request.user_attendance.save()
        mixin = MustBeCompanyAdmin()
        with self.assertRaisesRegex(
            PermissionDenied,
            "Tato stránka je určená pouze ověřeným firemním koordinátorům.",
        ):
            mixin.dispatch(self.request)

    def test_isnt_admin(self):
        self.request.user_attendance = mommy.make(
            "UserAttendance", campaign=testing_campaign()
        )
        mixin = MustBeCompanyAdmin()
        with self.assertRaisesRegex(
            PermissionDenied,
            "Tato stránka je určená pouze ověřeným firemním koordinátorům.",
        ):
            mixin.dispatch(self.request)


class GroupRequiredResponse(GroupRequiredResponseMixin, FakeViewClass):
    group_required = "cykloservis"


class GroupRequiredResponseMixinTest(TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

    def test_not_logged_in(self):
        self.request.user = AnonymousUser()
        mixin = GroupRequiredResponse()
        response = mixin.dispatch(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/login?next=/")

    def test_no_group(self):
        self.request.user = mommy.make("User")
        mixin = GroupRequiredResponse()
        with self.assertRaisesRegex(
            PermissionDenied,
            "Pro přístup k této stránce musíte být ve skupině cykloservis",
        ):
            mixin.dispatch(self.request)

    def test_in_group(self):
        self.request = self.factory.get(reverse("team_members"))
        self.request.user = mommy.make(
            "User", groups=[mommy.make("auth.Group", name="cykloservis")]
        )
        mixin = GroupRequiredResponse()
        self.assertEqual(mixin.dispatch(self.request), "superdispatch")


class MustHaveTeam(MustHaveTeamMixin, FakeViewClass):
    pass


class MustHaveTeamMixinTest(TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

    def test_team_none(self):
        self.request.user_attendance = mommy.make(
            "UserAttendance",
            team=None,
        )
        mixin = MustHaveTeam()
        with self.assertRaisesRegex(
            PermissionDenied,
            "Pokud jeli napřed tak je dohoňte a <a href='/tym/'>přidejte se k týmu</a>.",
        ):
            mixin.dispatch(self.request)

    def test_team_exists(self):
        self.request.user_attendance = mommy.make(
            "UserAttendance",
            team__campaign=testing_campaign,
            campaign=testing_campaign,
        )
        mixin = MustHaveTeam()
        self.assertEqual(mixin.dispatch(self.request), "superdispatch")

    def test_no_user_attendance(self):
        self.request.user_attendance = None
        mixin = MustHaveTeam()
        self.assertEqual(mixin.dispatch(self.request), "superdispatch")


class MustBeApprovedForTeam(MustBeApprovedForTeamMixin, FakeViewClass):
    pass


class MustBeApprovedForTeamMixinTest(TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

    def test_team_none(self):
        self.request.user_attendance = mommy.make(
            "UserAttendance",
            team=None,
        )
        mixin = MustBeApprovedForTeam()
        with self.assertRaisesRegex(
            PermissionDenied,
            "Pokud jeli napřed tak je dohoňte a <a href='/tym/'>přidejte se k týmu</a>.",
        ):
            mixin.dispatch(self.request)

    def test_team_approved(self):
        self.request.user_attendance = mommy.make(
            "UserAttendance",
            team__campaign=testing_campaign,
            campaign=testing_campaign,
            approved_for_team="approved",
        )
        mixin = MustBeApprovedForTeam()
        self.assertEqual(mixin.dispatch(self.request), "superdispatch")

    def test_team_undecided(self):
        self.request.user_attendance = mommy.make(
            "UserAttendance",
            team__campaign=testing_campaign,
            team__name="Foo team",
            campaign=testing_campaign,
            approved_for_team="undecided",
        )
        mixin = MustBeApprovedForTeam()
        with self.assertRaisesRegex(
            PermissionDenied, "Tým Foo team rebeluje proti Vašemu členství."
        ):
            mixin.dispatch(self.request)

    def test_team_denied(self):
        self.request.user_attendance = mommy.make(
            "UserAttendance",
            team__campaign=testing_campaign,
            team__name="Foo team",
            campaign=testing_campaign,
            approved_for_team="denied",
        )
        mixin = MustBeApprovedForTeam()
        with self.assertRaisesRegex(
            PermissionDenied, "Tým Foo team rebeluje proti Vašemu členství."
        ):
            mixin.dispatch(self.request)

    def test_no_user_attendance(self):
        self.request.user_attendance = None
        mixin = MustHaveTeam()
        self.assertEqual(mixin.dispatch(self.request), "superdispatch")
