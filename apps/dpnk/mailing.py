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
import createsend
from django.conf import settings
#import models
import logging
import threading
logger = logging.getLogger(__name__)


class Mailing:

    def __init__(self, api_key):
        createsend.CreateSend.api_key = api_key

    def add(self, list_id, name, surname, email, custom_fields):
        subscriber = createsend.Subscriber()
        r = subscriber.add(list_id, email,
                           " ".join([name, surname]),
                           custom_fields,
                           True)
        return r

    def update(self, list_id, mailing_id, name, surname, email, custom_fields):
        subscriber = createsend.Subscriber(list_id, mailing_id)
        subscriber.get(list_id, mailing_id)
        subscriber.update(email,
                          " ".join([name, surname]),
                          custom_fields,
                          True)
        return subscriber.email_address

    def delete(self, list_id, mailing_id):
        subscriber = createsend.Subscriber(list_id, mailing_id)
        subscriber.get(list_id, mailing_id)
        r = subscriber.delete()
        return r

mailing = Mailing(api_key=settings.MAILING_API_KEY)


def get_custom_fields(user_attendance):
    user = user_attendance.get_userprofile().user
    city = None
    payment_status = None
    is_new_user = None
    entered_competition = None
    team_member_count = None

    if isinstance(user_attendance, models.UserAttendance) and models.is_competitor(user):
        if user_attendance.team:
            city = user_attendance.team.subsidiary.city.name
        payment_status = user_attendance.payment()['status']

        is_new_user = user_attendance.other_user_attendances(user_attendance.campaign).count() > 0
        entered_competition = user_attendance.entered_competition()
        team_member_count = user_attendance.team_member_count()

    company_admin = models.get_company_admin(user, user_attendance.campaign) is not None

    custom_fields = [
        {'Key': "Mesto", 'Value': city},
        {'Key': "Firemni_spravce", 'Value': company_admin},
        {'Key': "Stav_platby", 'Value': payment_status},
        {'Key': "Aktivni", 'Value': user.is_active},
        {'Key': "Novacek", 'Value': is_new_user},
        {'Key': "Kampan", 'Value': user_attendance.campaign.name},
        {'Key': "Vstoupil_do_souteze", 'Value': entered_competition},
        {'Key': "Pocet_lidi_v_tymu", 'Value': team_member_count},
    ]
    return custom_fields


def update_mailing_id(user_attendance, mailing_id, mailing_hash):
    userprofile = user_attendance.get_userprofile()
    userprofile.mailing_id = mailing_id
    userprofile.mailing_hash = mailing_hash
    userprofile.save()


def add_user(user_attendance):
    user = user_attendance.get_userprofile().user
    custom_fields = get_custom_fields(user_attendance)

    # Register into mailing list
    try:
        list_id = user_attendance.campaign.mailing_list_id
        mailing_id = mailing.add(list_id, user.first_name, user.last_name, user.email, custom_fields)
        mailing_hash = hash(str((list_id, user.first_name, user.last_name, user.email, custom_fields)))
    except Exception:
        update_mailing_id(user_attendance, None, None)
        raise
    else:
        logger.info(u'User %s with email %s added to mailing list with id %s, custom_fields: %s' % (user, user.email, mailing_id, custom_fields))
        update_mailing_id(user_attendance, mailing_id, mailing_hash)


def update_user(user_attendance, ignore_hash):
    user = user_attendance.get_userprofile().user
    userprofile = user_attendance.get_userprofile()
    custom_fields = get_custom_fields(user_attendance)
    mailing_id = userprofile.mailing_id

    # Register into mailing list
    try:
        list_id = user_attendance.campaign.mailing_list_id
        mailing_hash = hash(str((list_id, user.first_name, user.last_name, user.email, custom_fields)))
        if ignore_hash or userprofile.mailing_hash != mailing_hash:
            new_mailing_id = mailing.update(list_id, mailing_id, user.first_name, user.last_name, user.email, custom_fields)
            logger.info(u'User %s (%s) with email %s updated in mailing list with id %s, custom_fields: %s' % (userprofile, userprofile.user, user.email, mailing_id, custom_fields))
            update_mailing_id(user_attendance, new_mailing_id, mailing_hash)
    except createsend.BadRequest as e:
        if e.data.Code == 203:
            add_user(user_attendance)
    except Exception:
        update_mailing_id(user_attendance, None, None)
        raise


def delete_user(user_attendance):
    user = user_attendance.get_userprofile().user
    mailing_id = user_attendance.get_userprofile().mailing_id

    if not mailing_id:
        return

    # Unregister from mailing list
    try:
        list_id = user_attendance.campaign.mailing_list_id
        new_mailing_id = mailing.delete(list_id, mailing_id)
    except Exception:
        update_mailing_id(user_attendance, None, None)
        raise
    else:
        logger.info(u'User %s with email %s deleted from mailing list with id %s' % (user, user.email, mailing_id))
        update_mailing_id(user_attendance, new_mailing_id, None)


def add_or_update_user_synchronous(user_attendance, ignore_hash=False):
    if not user_attendance.campaign.mailing_list_enabled:
        return

    user = user_attendance.get_userprofile().user

    try:
        if not user.is_active:
            delete_user(user_attendance)
        else:
            if models.is_competitor(user) and user_attendance.get_userprofile().mailing_id:
                update_user(user_attendance, ignore_hash)
            else:
                add_user(user_attendance)
    except:
        logger.exception("Problem occured during mailing list record actualization")


class MailingThread(threading.Thread):
    def __init__(self, user_attendance, ignore_hash, **kwargs):
        self.user_attendance = user_attendance
        self.ignore_hash = ignore_hash
        super(MailingThread, self).__init__(**kwargs)

    def run(self):
        add_or_update_user_synchronous(self.user_attendance, self.ignore_hash)


def add_or_update_user(user_attendance, ignore_hash=False):
    MailingThread(user_attendance, ignore_hash).start()
