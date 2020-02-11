import copy
import datetime
from collections import OrderedDict
from unittest import mock

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
    maxDiff = 10000

    def setUp(self):
        super().setUp()
        self.campaign = CampaignRecipe.make(
            slug="testing-campaign",
            name='Testing campaign',
            mailing_list_type='campaign_monitor',
            mailing_list_id='12345abcde',
            pk=339,
            year=2019,
        )
        util.rebuild_denorm_models(models.Team.objects.filter(pk=1))
        self.client = Client(HTTP_HOST="testing-campaign.testserver")

        PriceLevelRecipe.make()
        self.user_attendance = UserAttendancePaidRecipe.make(
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
            userprofile=self.user_attendance.userprofile,
            campaign=self.campaign,
            company_admin_approved='approved',
        )

        UserAttendancePaidRecipe.make(team=self.user_attendance.team, approved_for_team='approved',)
        UserAttendancePaidRecipe.make(team=self.user_attendance.team, approved_for_team='approved',)
        util.rebuild_denorm_models(models.UserAttendance.objects.all())
        util.rebuild_denorm_models(models.Team.objects.all())
        Token.objects.filter(user=self.user_attendance.userprofile.user).update(key='d201a3c9e88ecd433fdbbc3a2e451cbd3f80c4ba')
        self.user_attendance.refresh_from_db()
        self.user_attendance.team.refresh_from_db()
        self.user_attendance.userprofile.user.refresh_from_db()
        self.campaign.refresh_from_db()

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

    def test_cm_add(self):
        ret_mailing_id = "344ass"
        createsend.Subscriber.add = mock.MagicMock(return_value=ret_mailing_id)
        mailing.add_or_update_user_synchronous(self.user_attendance)
        createsend.Subscriber.add.assert_called_once_with('12345abcde', 'test@test.cz', 'Testing User 1', self.custom_fields, True)
        self.assertEqual(self.user_attendance.userprofile.mailing_id, ret_mailing_id)
        self.assertEqual(self.user_attendance.userprofile.mailing_hash, '0ef7bf8842d0f25db6a7e108b8d46228')

        createsend.Subscriber.update = mock.MagicMock()
        mailing.add_or_update_user_synchronous(self.user_attendance)
        self.assertFalse(createsend.Subscriber.update.called)
        self.assertEqual(self.user_attendance.userprofile.mailing_hash, '0ef7bf8842d0f25db6a7e108b8d46228')

    def test_cm_update(self):
        ret_mailing_id = "344ass"
        self.user_attendance.userprofile.mailing_id = '344ass'
        custom_fields = copy.deepcopy(self.custom_fields)
        custom_fields[0] = OrderedDict((('Key', 'Mesto'), ('Value', 'other-city')))
        self.user_attendance.team.subsidiary.city = mommy.make('City', slug="other-city")
        self.user_attendance.team.subsidiary.save()
        createsend.Subscriber.get = mock.MagicMock()
        createsend.Subscriber.update = mock.MagicMock()
        mailing.add_or_update_user_synchronous(self.user_attendance)
        createsend.Subscriber.get.assert_called_once_with('12345abcde', ret_mailing_id)
        createsend.Subscriber.update.assert_called_once_with('test@test.cz', 'Testing User 1', custom_fields, True)
        self.assertEqual(self.user_attendance.userprofile.mailing_hash, '1e57792f94b9a95f1d6c812429873b40')

        self.user_attendance.userprofile.user.is_active = False
        self.user_attendance.userprofile.user.save()
        createsend.Subscriber.get = mock.MagicMock()
        createsend.Subscriber.delete = mock.MagicMock(return_value=ret_mailing_id)
        mailing.add_or_update_user_synchronous(self.user_attendance)
        createsend.Subscriber.get.assert_called_once_with('12345abcde', ret_mailing_id)
        createsend.Subscriber.delete.assert_called_once_with()
        self.assertEqual(self.user_attendance.userprofile.mailing_id, ret_mailing_id)
        self.assertEqual(self.user_attendance.userprofile.mailing_hash, None)

    eco_subscriber_data = {
        'subscriber_data': {
            'custom_fields': {
                'Mesto': 'testing-city',
                'Uid': 1128,
                'Stav_platby': 'done',
                'Pocet_lidi_v_tymu': 3,
                'Povoleni_odesilat_emaily': True,
                'Vstoupil_do_souteze': True,
                'Novacek': False,
                'Kampan': 339,
                'Aktivni': True,
                'Auth_token': 'd201a3c9e88ecd433fdbbc3a2e451cbd3f80c4ba',
                'Firemni_spravce': 'approved',
            },
            'surname': 'User 1',
            'email': 'test@test.cz',
            'name': 'Testing',
        },
    }

    def test_eco_add(self):
        self.user_attendance.campaign.mailing_list_type = 'ecomail'
        self.user_attendance.campaign.save()
        self.user_attendance.campaign.refresh_from_db()
        ret_mailing_id = "344ass"
        mailing.TOKENAPI = mock.Mock()
        mailing.TOKENAPI().lists().subscribe.post.return_value = {'id': ret_mailing_id}
        mailing.add_or_update_user_synchronous(self.user_attendance)
        self.assertEqual(self.user_attendance.userprofile.mailing_id, ret_mailing_id)

        mailing.TOKENAPI().lists().subscribe.post.assert_called_once_with(mock.ANY)
        expected_dict = mailing.TOKENAPI().lists().subscribe.post.call_args_list[0][0][0]
        eco_subscriber_data = copy.deepcopy(self.eco_subscriber_data)
        eco_subscriber_data['resubscribe'] = True
        self.assertDictEqual(expected_dict, eco_subscriber_data)
        self.assertEqual(self.user_attendance.userprofile.mailing_hash, '0ef7bf8842d0f25db6a7e108b8d46228')

        mailing.add_or_update_user_synchronous(self.user_attendance)
        self.assertFalse(getattr(mailing.TOKENAPI().lists(), "update-subscriber").put.called)
        self.assertEqual(self.user_attendance.userprofile.mailing_hash, '0ef7bf8842d0f25db6a7e108b8d46228')

    def test_eco_update(self):
        self.user_attendance.campaign.mailing_list_type = 'ecomail'
        self.user_attendance.campaign.save()
        self.user_attendance.campaign.refresh_from_db()
        ret_mailing_id = "344ass"
        self.user_attendance.userprofile.mailing_id = '344ass'
        self.user_attendance.team.subsidiary.city = mommy.make('City', slug="other-city")
        self.user_attendance.team.subsidiary.save()
        mailing.TOKENAPI = mock.Mock()
        mailing.TOKENAPI().lists().__call__("update-subscriber").put.return_value = {'id': ret_mailing_id}
        mailing.TOKENAPI().lists().unsubscribe._request.return_value = mock.Mock(status_code=200)

        mailing.add_or_update_user_synchronous(self.user_attendance)
        mailing.TOKENAPI().lists().__call__("update-subscriber").put.assert_called_once_with(mock.ANY)
        expected_dict = mailing.TOKENAPI().lists().__call__("update-subscriber").put.call_args_list[0][0][0]
        eco_subscriber_data = copy.deepcopy(self.eco_subscriber_data)
        eco_subscriber_data['email'] = 'test@test.cz'
        eco_subscriber_data['subscriber_data']['custom_fields']['Mesto'] = 'other-city'
        self.assertDictEqual(expected_dict, eco_subscriber_data)
        self.assertEqual(self.user_attendance.userprofile.mailing_hash, '1e57792f94b9a95f1d6c812429873b40')

        self.user_attendance.userprofile.user.is_active = False
        self.user_attendance.userprofile.user.save()
        mailing.add_or_update_user_synchronous(self.user_attendance)
        mailing.TOKENAPI().lists().unsubscribe._request.assert_called_once_with("DELETE", data={"email": "test@test.cz"})
        self.assertEqual(self.user_attendance.userprofile.mailing_id, None)
        self.assertEqual(self.user_attendance.userprofile.mailing_hash, None)
