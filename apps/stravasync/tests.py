import datetime
from unittest.mock import patch

from django.test.utils import override_settings
from django.urls import reverse

from dpnk.test.test_views import ViewsLogon

from stravasync.models import StravaAccount


mock_token_response = {
    "access_token": "123456",
    "refresh_token": "6789",
    "expires_at": 343,
}


class MockAthlete():
    def __init__(self):
        self.username = 'test_strava_user'
        self.firstname = 'John'
        self.lastname = 'Smith'


class MockActivity():
    def __init__(self, id, type, name=None):  # noqa
        self.name = '#testing-campaigntam ' + str(id)
        if name:
            self.name = name
        self.description = ""
        self.start_date = lambda: None
        self.start_date.date = lambda: datetime.date(2010, 11, id + 1)
        self.map = lambda: None
        self.map.summary_polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
        self.id = id
        self.type = type
        self.distance = 3
        self.elapsed_time = lambda: None
        self.elapsed_time.total_seconds = lambda: 34


@override_settings(
    FAKE_DATE=datetime.date(year=2010, month=11, day=5),
    STRAVA_FINE_POLYLINES=False,
)
class TestStravaAuth(ViewsLogon):

    @patch('stravalib.Client')
    def test_strava_auth(self, mock_strava_client):
        msc = mock_strava_client()
        msc.exchange_code_for_token.return_value = mock_token_response
        msc.refresh_access_token.return_value = mock_token_response
        msc.get_athlete.return_value = MockAthlete()
        response = self.client.get(reverse('strava_auth'))
        self.assertRedirects(response, reverse('about_strava'), status_code=302)

    @patch('stravalib.Client')
    def test_about_strava_logged_out(self, mock_strava_client):
        msc = mock_strava_client()
        msc.authorization_url.return_value = "https://strava.com/authorize/url.html"
        response = self.client.get(reverse('about_strava'))
        self.assertContains(
            response,
            '<input type="image" src="/static/img/connect_with_strava.png" alt="Propojit se Stravou" class="btn btn-default float-right"/>',
            html=True,
            status_code=200,
        )

    @patch('stravalib.Client')
    def test_about_strava_logged_in(self, mock_strava_client):
        msc = mock_strava_client()
        msc.exchange_code_for_token.return_value = mock_token_response
        msc.refresh_access_token.return_value = mock_token_response
        msc.get_athlete.return_value = MockAthlete()
        self.client.get(reverse('strava_auth'))
        response = self.client.get(reverse('about_strava'))
        self.assertContains(
            response,
            '<input type="submit" class="btn btn-default float-right" value="Synchronizovat" />',
            html=True,
            status_code=200,
        )

    @patch('stravalib.Client')
    def test_strava_deauth(self, mock_strava_client):
        msc = mock_strava_client()
        msc.exchange_code_for_token.return_value = mock_token_response
        msc.get_athlete.return_value = MockAthlete()
        self.client.get(reverse('strava_auth'))
        response = self.client.post(reverse('strava_deauth'))
        self.assertRedirects(response, reverse('about_strava'), status_code=302)

    @patch('stravalib.Client')
    def test_strava_sync_no_activities(self, mock_strava_client):
        from stravasync.tasks import sync
        msc = mock_strava_client()
        msc.exchange_code_for_token.return_value = mock_token_response
        msc.get_athlete.return_value = MockAthlete()
        msc.refresh_access_token.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }
        msc.get_activities.return_value = [
        ]
        self.client.get(reverse('strava_auth'))
        strava_account = StravaAccount.objects.all().first()
        stats = sync(strava_account.pk)
        self.assertEqual(stats["activities"], [])
        self.assertEqual(stats["new_trips"], 0)
        self.assertEqual(stats["synced_trips"], 0)
        self.assertEqual(stats["synced_activities"], 0)
        strava_account = StravaAccount.objects.all().first()
        self.assertEqual(strava_account.errors, "")

    @patch('stravalib.Client')
    def test_strava_sync_activities(self, mock_strava_client):
        from stravasync.tasks import sync
        msc = mock_strava_client()
        msc.exchange_code_for_token.return_value = mock_token_response
        msc.get_athlete.return_value = MockAthlete()
        msc.refresh_access_token.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }
        msc.get_activities.return_value = [
            MockActivity(1, "ride"),
            MockActivity(2, "run"),
            MockActivity(3, "non-existant-commute-mode"),
            MockActivity(4, "walk", name="other"),
        ]
        self.client.get(reverse('strava_auth'))
        strava_account = StravaAccount.objects.all().first()
        stats = sync(strava_account.pk)
        strava_account = StravaAccount.objects.all().first()
        self.assertEqual(
            stats["activities"],
            [
                '#testing-campaigntam 1',
                '#testing-campaigntam 2',
                '#testing-campaigntam 3',
                'other',
            ],
        )
        self.assertEqual(stats["new_trips"], 2)
        self.assertEqual(stats["synced_trips"], 3)
        self.assertEqual(stats["synced_activities"], 4)
        self.assertEqual(
            strava_account.errors,
            "Error syncing activity #testing-campaigntam 3 \nUnknown activity type 'non-existant-commute-mode'\n\n",
        )
