from unittest.mock import patch

from django.urls import reverse

from dpnk.test.test_views import ViewsLogon


class MockAthlete():
    def __init__(self):
        self.username = 'test_strava_user'
        self.firstname = 'John'
        self.lastname = 'Smith'


class TestStravaAuth(ViewsLogon):

    @patch('stravalib.Client')
    def test_strava_auth(self, mock_strava_client):
        msc = mock_strava_client()
        msc.exchange_code_for_token.return_value = "123456"
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
            '<a href="https://strava.com/authorize/url.html" class="btn btn-default float-right">' +
            '<img src="/static/img/connect_with_strava.png" alt="Propojit se Stravou" /></a>',
            html=True,
            status_code=200,
        )

    @patch('stravalib.Client')
    def test_about_strava_logged_in(self, mock_strava_client):
        msc = mock_strava_client()
        msc.exchange_code_for_token.return_value = "123456"
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
        msc.exchange_code_for_token.return_value = "123456"
        msc.get_athlete.return_value = MockAthlete()
        self.client.get(reverse('strava_auth'))
        response = self.client.post(reverse('strava_deauth'))
        self.assertRedirects(response, reverse('about_strava'), status_code=302)
