# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2015 o.s. Auto*Mat
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
import hashlib
import logging
import threading
from collections import OrderedDict

import createsend

from django.conf import settings

import slumber

logger = logging.getLogger(__name__)


class CampaignMonitor:

    def __init__(self, list_id):
        self.api_key = settings.MAILING_API_KEY
        self.list_id = list_id

    @classmethod
    def translate_fields(cls, custom_fields):
        ret_custom_fields = []
        for key, value in custom_fields.items():
            if key in ('first_name', 'last_name', 'email'):
                continue
            ret_custom_fields.append(OrderedDict((('Key', key), ('Value', value))))
        return ret_custom_fields

    def add(self, email, custom_fields):
        subscriber = createsend.Subscriber({'api_key': self.api_key})
        r = subscriber.add(
            self.list_id,
            email,
            " ".join([custom_fields['first_name'], custom_fields['last_name']]),
            self.translate_fields(custom_fields),
            True,
        )
        return r

    def update(self, mailing_id, email, custom_fields):
        subscriber = createsend.Subscriber({'api_key': self.api_key}, self.list_id, mailing_id)
        subscriber.get(self.list_id, mailing_id)
        subscriber.update(
            email,
            " ".join([custom_fields['first_name'], custom_fields['last_name']]),
            self.translate_fields(custom_fields),
            True,
        )
        return subscriber.email_address

    def delete(self, mailing_id, email):
        subscriber = createsend.Subscriber({'api_key': self.api_key}, self.list_id, mailing_id)
        subscriber.get(self.list_id, mailing_id)
        r = subscriber.delete()
        return r


class TOKENAPI(slumber.API):
    def __init__(self, *args, **kwargs):
        token = kwargs.pop('token', None)
        super(TOKENAPI, self).__init__(*args, **kwargs)
        if token is None:
            data = dict(
                zip(
                    ["username", "password"],
                    self._store["session"].auth,
                ),
            )
            token = self.token.post(data=data)["token"]
        self._store['session'].auth = None
        self._store['session'].headers['key'] = token

    def _get_resource(self, **kwargs):
        return self.resource_class(**kwargs)


class EcoMailing:
    def __init__(self, list_id):
        self.api_key = settings.ECOMAIL_MAILING_API_KEY
        self.list_id = list_id
        self.api = TOKENAPI("http://api2.ecomailapp.cz/", token=self.api_key, append_slash=False)

    @classmethod
    def translate_fields(cls, custom_fields):
        new_custom_fields = {i: custom_fields[i] for i in custom_fields if i not in ('first_name', 'last_name', 'email')}
        uid = new_custom_fields.pop('Id')
        ret_custom_fields = {}
        for k, v in (
            ('name', 'first_name'),
            ('surname', 'last_name'),
            ('email', 'email'),
            ('city', 'city'),
        ):
            if v in custom_fields:
                ret_custom_fields[k] = custom_fields.pop(v)

        ret_custom_fields['custom_fields'] = new_custom_fields
        ret_custom_fields['custom_fields']['Uid'] = uid
        return ret_custom_fields

    def update(self, mailing_id, email, custom_fields):
        return_data = self.api.lists(self.list_id).__call__("update-subscriber").put(
            {
                "email": email,
                "subscriber_data": self.translate_fields(custom_fields),
            },
        )
        return return_data['id']

    def add(self, email, custom_fields):
        return_data = self.api.lists(self.list_id).subscribe.post(
            {
                "subscriber_data": self.translate_fields(custom_fields),
                "resubscribe": True,
            },
        )
        return return_data['id']

    def delete(self, mailing_id, email):
        resp = self.api.lists(self.list_id).unsubscribe._request(
            "DELETE",
            data={"email": email},
        )
        if not 200 <= resp.status_code <= 299:
            raise Exception("Not unsubscribed")
        return None


def get_custom_fields(user_attendance):
    user = user_attendance.get_userprofile().user
    city = None
    payment_status = None
    is_new_user = None
    entered_competition = None
    team_member_count = None

    if user_attendance.team:
        city = user_attendance.team.subsidiary.city.slug
    payment_status = user_attendance.payment_status

    is_new_user = user_attendance.other_user_attendances(user_attendance.campaign).count() < 0
    entered_competition = user_attendance.entered_competition()
    team_member_count = user_attendance.team_member_count()
    mailing_approval = user_attendance.userprofile.mailing_opt_in and user_attendance.personal_data_opt_in

    company_admin = user_attendance.related_company_admin
    company_admin_approved = company_admin.company_admin_approved if company_admin else False

    custom_fields = OrderedDict([
        ('first_name', user.first_name),
        ('last_name', user.last_name),
        ('email', user.email),
        ('Mesto', city),
        ('Firemni_spravce', company_admin_approved),
        ('Stav_platby', payment_status),
        ('Aktivni', user.is_active),
        ('Auth_token', user.auth_token.key),
        ('Id', user.pk),
        ('Novacek', is_new_user),
        ('Kampan', user_attendance.campaign.pk),
        ('Vstoupil_do_souteze', entered_competition),
        ('Pocet_lidi_v_tymu', team_member_count),
        ('Povoleni_odesilat_emaily', mailing_approval),
    ])
    return custom_fields


def update_mailing_id(user_attendance, mailing_id, mailing_hash):
    userprofile = user_attendance.get_userprofile()
    userprofile.mailing_id = mailing_id
    userprofile.mailing_hash = mailing_hash
    userprofile.don_save_mailing = True
    userprofile.save()
    userprofile.don_save_mailing = False


def get_mailing(user_attendance):
    if user_attendance.campaign.mailing_list_type == 'ecomail':
        Mailing = EcoMailing
    elif user_attendance.campaign.mailing_list_type == 'campaign_monitor':
        Mailing = CampaignMonitor
    else:
        return
    return Mailing(list_id=user_attendance.campaign.mailing_list_id)


def get_hash(user_attendance, custom_fields):
    user = user_attendance.get_userprofile().user
    list_id = user_attendance.campaign.mailing_list_id
    return hashlib.md5(
        str((list_id, user.first_name, user.last_name, user.email, CampaignMonitor.translate_fields(custom_fields))).encode('utf-8'),
    ).hexdigest()


def add_user(user_attendance):
    user = user_attendance.get_userprofile().user
    custom_fields = get_custom_fields(user_attendance)

    mailing = get_mailing(user_attendance)
    if mailing is None:
        return

    # Register into mailing list
    try:
        mailing_id = mailing.add(user.email, custom_fields)
        mailing_hash = get_hash(user_attendance, custom_fields)
    except Exception:
        update_mailing_id(user_attendance, None, None)
        raise
    else:
        logger.info(
            'User added to mailing list',
            extra={'user': user, 'email': user.email, 'mailing_id': mailing_id, 'custom_fields': custom_fields},
        )
        update_mailing_id(user_attendance, mailing_id, mailing_hash)


def update_user(user_attendance, ignore_hash):
    user = user_attendance.get_userprofile().user
    userprofile = user_attendance.get_userprofile()
    custom_fields = get_custom_fields(user_attendance)
    mailing_id = userprofile.mailing_id

    mailing = get_mailing(user_attendance)
    if mailing is None:
        return

    # Register into mailing list
    try:
        mailing_hash = get_hash(user_attendance, custom_fields)
        if ignore_hash or userprofile.mailing_hash != mailing_hash:
            new_mailing_id = mailing.update(mailing_id, user.email, custom_fields)
            logger.info(
                'User updated in mailing list',
                extra={'userprofile': userprofile, 'user': user, 'email': user.email, 'mailing_id': mailing_id, 'custom_fields': custom_fields},
            )
            update_mailing_id(user_attendance, new_mailing_id, mailing_hash)
    except createsend.BadRequest as e:
        if e.data.Code == 203:
            add_user(user_attendance)
    except slumber.exceptions.HttpNotFoundError:
        add_user(user_attendance)
    except Exception as e:
        logger.exception("Problem occured during mailing list record update", extra={'content': getattr(e, 'content', '')})
        update_mailing_id(user_attendance, None, None)
        raise


def delete_user(user_attendance):
    user = user_attendance.get_userprofile().user
    mailing_id = user_attendance.get_userprofile().mailing_id

    mailing = get_mailing(user_attendance)
    if mailing is None:
        return

    if not mailing_id:
        return

    # Unregister from mailing list
    try:
        new_mailing_id = mailing.delete(mailing_id, user.email)
    except Exception as e:
        logger.exception("Problem occured during mailing list record deletion", extra={'content': getattr(e, 'content', '')})
        update_mailing_id(user_attendance, None, None)
        raise
    else:
        logger.info('User deleted from mailing list', extra={'user': user, 'email': user.email, 'mailing_id': mailing_id})
        update_mailing_id(user_attendance, new_mailing_id, None)


def add_or_update_user_synchronous(user_attendance, ignore_hash=False):
    userprofile = user_attendance.get_userprofile()
    user = userprofile.user

    try:
        if user.is_active and userprofile.mailing_opt_in and user_attendance.personal_data_opt_in:
            if user_attendance.get_userprofile().mailing_id:
                update_user(user_attendance, ignore_hash)
            else:
                add_user(user_attendance)
        else:
            delete_user(user_attendance)
    except Exception as e:
        logger.exception("Problem occured during mailing list record actualization", extra={'content': getattr(e, 'content', '')})


class MailingThread(threading.Thread):
    def __init__(self, user_attendance, ignore_hash, **kwargs):
        self.user_attendance = user_attendance
        self.ignore_hash = ignore_hash
        super().__init__(**kwargs)

    def run(self):
        add_or_update_user_synchronous(self.user_attendance, self.ignore_hash)


def add_or_update_user(user_attendance, ignore_hash=False):
    if user_attendance.campaign.mailing_list_enabled:
        MailingThread(user_attendance, ignore_hash).start()
