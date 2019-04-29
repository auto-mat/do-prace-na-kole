import datetime
from unittest.mock import MagicMock

from django.test import TestCase
from django.test.utils import override_settings

from model_mommy import mommy

from .models import MotivationMessage


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
)
class MessagesTest(TestCase):
    def setUp(self):
        self.user_attendance = MagicMock()
        self.user_attendance.get_frequency_percentage.return_value = 65
        self.user_attendance.campaign.competition_phase.return_value.date_from = datetime.date(2010, 11, 22)
        self.user_attendance.get_frequency_rank_in_team.return_value = 2
        self.user_attendance.team.members.return_value.count.return_value = 4

    def test_get_all_messages_simple(self):
        message = mommy.make("MotivationMessage")
        self.assertQuerysetEqual(MotivationMessage._get_all_messages(self.user_attendance), [message], transform=lambda x: x)

    def test_get_all_messages_date(self):
        message1 = mommy.make("MotivationMessage", message="message 1", date_from=datetime.date(2010, 11, 20), date_to=datetime.date(2010, 11, 20))
        message2 = mommy.make("MotivationMessage", message="message 2", date_from=datetime.date(2010, 11, 20))
        message3 = mommy.make("MotivationMessage", message="message 3", date_to=datetime.date(2010, 11, 20))
        mommy.make("MotivationMessage", message="message 4", date_from=datetime.date(2010, 11, 21), date_to=datetime.date(2010, 11, 21))
        mommy.make("MotivationMessage", message="message 5", date_from=datetime.date(2010, 11, 21))
        mommy.make("MotivationMessage", message="message 6", date_from=datetime.date(2010, 11, 19), date_to=datetime.date(2010, 11, 19))
        mommy.make("MotivationMessage", message="message 7", date_to=datetime.date(2010, 11, 19))
        messages = MotivationMessage._get_all_messages(self.user_attendance).order_by('id')
        self.assertQuerysetEqual(messages, (message1, message2, message3), transform=lambda x: x)

    def test_get_all_messages_percentage(self):
        message1 = mommy.make("MotivationMessage", message="message 1", frequency_min=65, frequency_max=65)
        message2 = mommy.make("MotivationMessage", message="message 2", frequency_min=60)
        message3 = mommy.make("MotivationMessage", message="message 3", frequency_max=65)
        mommy.make("MotivationMessage", message="message 4", frequency_min=66, frequency_max=66)
        mommy.make("MotivationMessage", message="message 5", frequency_min=64, frequency_max=64)
        mommy.make("MotivationMessage", message="message 6", frequency_min=66)
        mommy.make("MotivationMessage", message="message 7", frequency_max=64)
        messages = MotivationMessage._get_all_messages(self.user_attendance).order_by('id')
        self.assertQuerysetEqual(messages, [message1, message2, message3], transform=lambda x: x)

    def test_get_all_messages_day(self):
        message1 = mommy.make("MotivationMessage", message="message1", day_from=2, day_to=2)
        message2 = mommy.make("MotivationMessage", message="message2", day_from=2)
        message3 = mommy.make("MotivationMessage", message="message3", day_to=3)
        mommy.make("MotivationMessage", message="message4", day_from=1, day_to=1)
        mommy.make("MotivationMessage", message="message5", day_from=3, day_to=3)
        mommy.make("MotivationMessage", message="message6", day_from=3)
        mommy.make("MotivationMessage", message="message7", day_to=1)
        messages = MotivationMessage._get_all_messages(self.user_attendance).order_by('id')
        self.assertQuerysetEqual(messages, (message1, message2, message3), transform=lambda x: x)

    def test_get_all_messages_rank(self):
        message1 = mommy.make("MotivationMessage", message="message1", team_rank_from=2, team_rank_to=2)
        message2 = mommy.make("MotivationMessage", message="message2", team_rank_from=2)
        message3 = mommy.make("MotivationMessage", message="message3", team_rank_to=3)
        mommy.make("MotivationMessage", message="message4", team_rank_from=1, team_rank_to=1)
        mommy.make("MotivationMessage", message="message5", team_rank_from=3, team_rank_to=3)
        mommy.make("MotivationMessage", message="message6", team_rank_from=3)
        mommy.make("MotivationMessage", message="message7", team_rank_to=1)
        messages = MotivationMessage._get_all_messages(self.user_attendance).order_by('id')
        self.assertQuerysetEqual(messages, (message1, message2, message3), transform=lambda x: x)

    def test_get_random_simple(self):
        """ Random enabled message from set with highest priority should be returned """
        message1 = mommy.make("MotivationMessage", message="message1", priority=2)
        message2 = mommy.make("MotivationMessage", message="message2", priority=2)
        mommy.make("MotivationMessage", message="message2d", enabled=False)
        mommy.make("MotivationMessage", message="message3", priority=1)
        mommy.make("MotivationMessage", message="message4", priority=1)
        mommy.make("MotivationMessage", message="message5", priority=1)
        mommy.make("MotivationMessage", message="message6")
        message = MotivationMessage.get_random_message(self.user_attendance)
        self.assertTrue(message in (message1, message2))
