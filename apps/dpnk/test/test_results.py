import datetime
from itertools import cycle

from django.test import TestCase
from django.test.utils import override_settings

from dpnk import models, results, util
from dpnk.test.util import ClearCacheMixin, DenormMixin
from dpnk.test.util import print_response  # noqa

from model_mommy import mommy


@override_settings(
    FAKE_DATE=datetime.date(year=2017, month=5, day=5),
)
class ResultsTests(DenormMixin, ClearCacheMixin, TestCase):
    def setUp(self, recreational=False):
        super().setUp()
        competition_phase = mommy.make(
            "Phase",
            phase_type="competition",
            date_from="2017-4-2",
            date_to="2017-5-20",
        )
        self.testing_campaign = competition_phase.campaign
        if recreational:
            self.testing_campaign.recreational = True
            self.testing_campaign.save()
        team = mommy.make("Team", campaign=self.testing_campaign)
        mommy.make(
            "UserAttendance",
            approved_for_team="approved",
            team=team,
            campaign=self.testing_campaign,
            t_shirt_size__campaign=self.testing_campaign,
            team__campaign=self.testing_campaign,
            transactions=[mommy.make("Payment", status=99)],
        )
        self.user_attendance = mommy.make(
            "UserAttendance",
            approved_for_team="approved",
            team=team,
            campaign=self.testing_campaign,
            t_shirt_size__campaign=self.testing_campaign,
            team__campaign=self.testing_campaign,
            transactions=[mommy.make("Payment", status=99)],
        )
        mommy.make(
            "Trip",
            commute_mode_id=1,
            distance="1",
            direction="trip_to",
            user_attendance=self.user_attendance,
            date="2017-05-01",
        )
        mommy.make(
            "Trip",
            commute_mode_id=1,
            distance="3",
            direction="trip_from",
            date="2017-05-01",
            user_attendance=self.user_attendance,
        )
        mommy.make(
            "Trip",
            commute_mode_id=4,
            direction=cycle(["trip_to", "trip_from"]),
            date="2017-05-02",
            user_attendance=self.user_attendance,
            _quantity=2,
        )
        mommy.make(
            "Trip",
            commute_mode_id=2,
            distance="1",
            direction="trip_from",
            date="2017-05-03",
            user_attendance=self.user_attendance,
        )

    def test_get_userprofile_length(self):
        competition = mommy.make(
            "Competition",
            competition_type="length",
            competitor_type="single_user",
            campaign=self.testing_campaign,
            date_from=datetime.date(2017, 4, 3),
            date_to=datetime.date(2017, 5, 23),
            commute_modes=models.CommuteMode.objects.filter(
                slug__in=("bicycle", "by_foot")
            ),
        )
        result = results.get_userprofile_length([self.user_attendance], competition)
        self.assertEqual(result, 5.0)

        util.rebuild_denorm_models([self.user_attendance])
        self.user_attendance.refresh_from_db()

        result = self.user_attendance.trip_length_total
        self.assertEqual(result, 5.0)

    def test_get_userprofile_frequency(self):
        competition = mommy.make(
            "Competition",
            competition_type="frequency",
            competitor_type="team",
            campaign=self.testing_campaign,
            date_from=datetime.date(2017, 4, 3),
            date_to=datetime.date(2017, 5, 23),
            commute_modes=models.CommuteMode.objects.filter(
                slug__in=("bicycle", "by_foot")
            ),
        )

        util.rebuild_denorm_models([self.user_attendance])
        self.user_attendance.refresh_from_db()
        self.user_attendance.team.refresh_from_db()

        result = self.user_attendance.get_rides_count_denorm
        self.assertEqual(result, 3)

        result = self.user_attendance.get_working_rides_base_count()
        self.assertEqual(result, 48)

        result = self.user_attendance.frequency
        self.assertEqual(result, 0.0625)

        result = self.user_attendance.team.frequency
        self.assertEqual(result, 0.03125)

        result = self.user_attendance.team.get_rides_count_denorm
        self.assertEqual(result, 3)

        result = self.user_attendance.team.get_working_trips_count()
        self.assertEqual(result, 96)

        result = results.get_working_trips_count(self.user_attendance, competition)
        self.assertEqual(result, 48)

        result = results.get_userprofile_frequency(self.user_attendance, competition)
        self.assertEqual(result, (3, 48, 3 / 48.0))

        result = results.get_team_frequency(
            self.user_attendance.team.members, competition
        )
        self.assertEqual(result, (3, 96, 3 / 96.0))

    def test_get_userprofile_length_by_foot(self):
        competition = mommy.make(
            "Competition",
            competition_type="length",
            competitor_type="single_user",
            campaign=self.testing_campaign,
            date_from=datetime.date(2017, 4, 1),
            date_to=datetime.date(2017, 5, 31),
            commute_modes=models.CommuteMode.objects.filter(slug__in=("by_foot",)),
        )
        result = results.get_userprofile_length([self.user_attendance], competition)
        self.assertEqual(result, 1.0)


class RecreationalResultsTests(ResultsTests):
    fixtures = ["commute_mode"]

    def setUp(self):
        super().setUp(recreational=True)
        mommy.make(
            "Trip",
            commute_mode_id=2,
            distance="3",
            direction="recreational",
            date="2017-05-04",
            user_attendance=self.user_attendance,
        )

    def test_get_userprofile_length_recreational(self):
        competition = mommy.make(
            "Competition",
            competition_type="length",
            competitor_type="single_user",
            campaign=self.testing_campaign,
            date_from=datetime.date(2017, 4, 3),
            date_to=datetime.date(2017, 5, 23),
            commute_modes=models.CommuteMode.objects.filter(
                slug__in=("bicycle", "by_foot")
            ),
        )
        result = results.get_userprofile_length(
            [self.user_attendance], competition, recreational=True
        )
        self.assertEqual(result, 8.0)

        util.rebuild_denorm_models([self.user_attendance])
        self.user_attendance.refresh_from_db()

        result = self.user_attendance.total_trip_length_including_recreational
        self.assertEqual(result, 8.0)
