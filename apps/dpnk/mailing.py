import createsend
from django.conf import settings
import models
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
                           custom_fields
                           , True)
        return r

    def update(self, list_id, mailing_id, name, surname, email, custom_fields):
        subscriber = createsend.Subscriber(list_id, mailing_id)
        subscriber.get(list_id, mailing_id)
        r = subscriber.update(email,
                           " ".join([name, surname]),
                           custom_fields
                           , True)
        return r

    def delete(self, list_id, mailing_id):
        subscriber = createsend.Subscriber(list_id, mailing_id)
        subscriber.get(list_id, mailing_id)
        r = subscriber.delete()
        return r

mailing = Mailing(api_key=settings.MAILING_API_KEY)

def get_custom_fields(user_attendance):
    user = user_attendance.userprofile.user
    city = None
    payment_status = None
    if models.is_competitor(user):
        if user_attendance.team:
            city = user_attendance.team.subsidiary.city_in_campaign.city.name
        payment_status = user_attendance.payment()['status']

    team_coordinator = models.is_team_coordinator(user_attendance)
    company_admin = models.get_company_admin(user, user_attendance.campaign) == None
    is_new_user = user_attendance.other_user_attendances(user_attendance.campaign).count() > 0

    custom_fields = [ 
                       { 'Key': "Mesto", 'Value': city } ,
                       { 'Key': "Tymovy_koordinator", 'Value': team_coordinator } ,
                       { 'Key': "Firemni_spravce", 'Value': company_admin } ,
                       { 'Key': "Stav_platby", 'Value': payment_status } ,
                       { 'Key': "Aktivni", 'Value': user.is_active } ,
                       { 'Key': "Novacek", 'Value': is_new_user } ,
                   ]
    return custom_fields

def update_mailing_id(user, mailing_id):
    if mailing_id:
        user.userprofile.mailing_id = mailing_id
        user.userprofile.save()

def add_user(user_attendance):
    user = user_attendance.userprofile.user
    custom_fields = get_custom_fields(user_attendance)

    # Register into mailing list
    try:
        list_id = user_attendance.campaign.mailing_list_id
        mailing_id = mailing.add(list_id, user.first_name, user.last_name, user.email, custom_fields)
    except Exception, e:
        logger.error(u'Can\'t add user %s with email %s to mailing list: %s' % (user, user.email, str(e)))
    else:
        logger.info(u'User %s with email %s added to mailing list with id %s, custom_fields: %s' % (user, user.email, mailing_id, custom_fields))
        update_mailing_id(user, mailing_id)

def update_user(user_attendance):
    user = user_attendance.userprofile.user
    userprofile = user_attendance.userprofile
    custom_fields = get_custom_fields(user_attendance)
    mailing_id = userprofile.mailing_id

    # Register into mailing list
    try:
        list_id = user_attendance.campaign.mailing_list_id
        mailing_id = mailing.update(list_id, mailing_id, user.first_name, user.last_name, user.email, custom_fields)
    except Exception, e:
        logger.error(u'Can\'t update user %s: email: %s, mailing_id: %s to mailing list: %s' % (userprofile.user, user.email, mailing_id, str(e)))
    else:
        logger.info(u'User %s with email %s updated in mailing list with id %s, custom_fields: %s' % (userprofile.user, user.email, mailing_id, custom_fields))
        update_mailing_id(user, mailing_id)

def delete_user(user_attendance):
    mailing_id = None
    if models.is_competitor(user):
        mailing_id = user.get_profile().mailing_id
    elif models.is_company_admin(user):
        mailing_id = user.company_admin.mailing_id
        add_user(user)

    if not mailing_id:
        return

    # Unregister from mailing list
    try:
        list_id = user_attendance.campaign.mailing_list_id
        mailing_id = mailing.delete(list_id, mailing_id)
    except Exception, e:
        logger.error(u'Can\'t delete user %s with email %s to mailing list: %s' % (user, user.email, str(e)))
    else:
        logger.info(u'User %s with email %s deleted from mailing list with id %s' % (user, user.email, mailing_id))
        update_mailing_id(user, mailing_id)

class MailingThread(threading.Thread):
    def __init__(self, user_attendance, **kwargs):
        self.user_attendance = user_attendance
        super(MailingThread, self).__init__(**kwargs)

    def run(self):
        user = self.user_attendance.userprofile.user
        if not user.is_active:
            delete_user(self.user_attendance)
        else:
            if models.is_competitor(user) and user.get_profile().mailing_id:
                update_user(self.user_attendance)
            else:
                add_user(self.user_attendance)


def add_or_update_user(user_attendance):
    if not user_attendance.campaign.mailing_list_enabled:
        return

    MailingThread(user_attendance).start()
