import datetime
from collections import OrderedDict
from unittest.mock import MagicMock

import createsend

from django.test import Client, TestCase
from django.test.utils import override_settings

from dpnk import mailing, models, util
from dpnk.test.util import DenormMixin

from model_mommy import mommy

from rest_framework.authtoken.models import Token

from .mommy_recipes import CampaignRecipe, PriceLevelRecipe, UserAttendancePaidRecipe


@override_settings(
    SITE_ID=2,
    FAKE_DATE=datetime.date(year=2010, month=11, day=20),
    SSLIFY_ADMIN_DISABLE=True,
)
class MailingTests(DenormMixin, TestCase):
    # fixtures = ['sites', 'campaign', 'auth_user', 'users', 'transactions', 'batches', 'company_competition']

    def setUp(self):
        super().setUp()
        util.rebuild_denorm_models(models.Team.objects.filter(pk=1))
        self.client = Client(HTTP_HOST="testing-campaign.testserver")

    def test_dpnk_mailing_list(self):
        campaign = CampaignRecipe.make(
            slug="testing-campaign",
            name='Testing campaign',
            mailing_list_type='campaign_monitor',
            mailing_list_id='12345abcde',
            pk=339,
        )
        PriceLevelRecipe.make()
        user_attendance = UserAttendancePaidRecipe.make(
            approved_for_team='approved',
            personal_data_opt_in=True,
            userprofile__user__pk=1128,
            team__subsidiary__city__slug='testing-city',
            userprofile__mailing_opt_in=True,
            userprofile__sex='male',
            userprofile__user__email='test@test.cz',
            userprofile__user__first_name='Testing',
            userprofile__user__last_name='User 1',
        )
        mommy.make(
            'CompanyAdmin',
            userprofile=user_attendance.userprofile,
            campaign=campaign,
            company_admin_approved='approved',
        )

        UserAttendancePaidRecipe.make(team=user_attendance.team, approved_for_team='approved',)
        UserAttendancePaidRecipe.make(team=user_attendance.team, approved_for_team='approved',)
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        util.rebuild_denorm_models(models.Team.objects.all())
        Token.objects.filter(user=user_attendance.userprofile.user).update(key='d201a3c9e88ecd433fdbbc3a2e451cbd3f80c4ba')
        user_attendance.refresh_from_db()
        user_attendance.team.refresh_from_db()
        user_attendance.userprofile.user.refresh_from_db()
        campaign.refresh_from_db()
        ret_mailing_id = "344ass"
        createsend.Subscriber.add = MagicMock(return_value=ret_mailing_id)
        mailing.add_or_update_user_synchronous(user_attendance)
        custom_fields = [
            OrderedDict((('Key', 'Mesto'), ('Value', 'testing-city'))),
            OrderedDict((('Key', 'Firemni_spravce'), ('Value', 'approved'))),
            OrderedDict((('Key', 'Stav_platby'), ('Value', 'done'))),
            OrderedDict((('Key', 'Aktivni'), ('Value', True))),
            OrderedDict((('Key', 'Auth_token'), ('Value', 'd201a3c9e88ecd433fdbbc3a2e451cbd3f80c4ba'))),
            OrderedDict((('Key', 'Id'), ('Value', 1128))),
            OrderedDict((('Key', 'Novacek'), ('Value', False))),
            OrderedDict((('Key', 'Kampan'), ('Value', 339))),
            OrderedDict((('Key', 'Vstoupil_do_souteze'), ('Value', True))),
            OrderedDict((('Key', 'Pocet_lidi_v_tymu'), ('Value', 3))),
            OrderedDict((('Key', 'Povoleni_odesilat_emaily'), ('Value', True))),
        ]
        createsend.Subscriber.add.assert_called_once_with('12345abcde', 'test@test.cz', 'Testing User 1', custom_fields, True)
        self.assertEqual(user_attendance.userprofile.mailing_id, ret_mailing_id)
        self.assertEqual(user_attendance.userprofile.mailing_hash, '0ef7bf8842d0f25db6a7e108b8d46228')

        createsend.Subscriber.update = MagicMock()
        mailing.add_or_update_user_synchronous(user_attendance)
        self.assertFalse(createsend.Subscriber.update.called)
        self.assertEqual(user_attendance.userprofile.mailing_hash, '0ef7bf8842d0f25db6a7e108b8d46228')

        custom_fields[0] = OrderedDict((('Key', 'Mesto'), ('Value', 'other-city')))
        user_attendance.team.subsidiary.city = mommy.make('City', slug="other-city")
        user_attendance.team.subsidiary.save()
        createsend.Subscriber.get = MagicMock()
        createsend.Subscriber.update = MagicMock()
        mailing.add_or_update_user_synchronous(user_attendance)
        createsend.Subscriber.get.assert_called_once_with('12345abcde', ret_mailing_id)
        createsend.Subscriber.update.assert_called_once_with('test@test.cz', 'Testing User 1', custom_fields, True)
        self.assertEqual(user_attendance.userprofile.mailing_hash, '1e57792f94b9a95f1d6c812429873b40')

        user_attendance.userprofile.user.is_active = False
        user_attendance.userprofile.user.save()
        createsend.Subscriber.get = MagicMock()
        createsend.Subscriber.delete = MagicMock(return_value=ret_mailing_id)
        mailing.add_or_update_user_synchronous(user_attendance)
        createsend.Subscriber.get.assert_called_once_with('12345abcde', ret_mailing_id)
        createsend.Subscriber.delete.assert_called_once_with()
        self.assertEqual(user_attendance.userprofile.mailing_id, ret_mailing_id)
        self.assertEqual(user_attendance.userprofile.mailing_hash, None)
