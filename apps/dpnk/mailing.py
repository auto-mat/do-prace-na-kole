import createsend
from django.conf import settings
import models
import logging
logger = logging.getLogger(__name__)

class Mailing:

    def __init__(self, api_key, list_id):
        createsend.CreateSend.api_key = api_key
        self.list_id = list_id

    def add(self, name, surname, email, custom_fields):
        subscriber = createsend.Subscriber()
        r = subscriber.add(self.list_id, email,
                           " ".join([name, surname]),
                           custom_fields
                           , True)
        return r

    def update(self, mailing_id, name, surname, email, custom_fields):
        subscriber = createsend.Subscriber(self.list_id, mailing_id)
        subscriber.get(self.list_id, mailing_id)
        r = subscriber.update(email,
                           " ".join([name, surname]),
                           custom_fields
                           , True)
        return r

    def delete(self, mailing_id):
        subscriber = createsend.Subscriber(self.list_id, mailing_id)
        subscriber.get(self.list_id, mailing_id)
        r = subscriber.delete()
        return r

mailing = Mailing(api_key=settings.MAILING_API_KEY, list_id=settings.MAILING_LIST_ID)

def get_custom_fields(user):
    if models.is_competitor(user):
        userprofile = user.get_profile()
        city = userprofile.team.subsidiary.city.name
        payment_status = userprofile.payment()['status']
    else:
        city = None
        payment_status = None

    is_competitor = models.is_competitor(user)
    team_coordinator = models.is_team_coordinator(user)
    company_admin = models.is_company_admin(user)

    custom_fields = [ 
                       { 'Key': "Mesto", 'Value': city } ,
                       { 'Key': "je_soutezici", 'Value': is_competitor } ,
                       { 'Key': "Tymovy_koordinator", 'Value': team_coordinator } ,
                       { 'Key': "Firemni_spravce", 'Value': company_admin } ,
                       { 'Key': "Stav_platby", 'Value': payment_status } ,
                       { 'Key': "Aktivni", 'Value': user.is_active } ,
                   ]
    return custom_fields

def update_mailing_id(user,mailing_id):
    if mailing_id:
        if models.is_competitor(user):
            user.userprofile.mailing_id = mailing_id
            user.userprofile.save()
        if models.is_company_admin(user):
            user.company_admin.mailing_id = mailing_id
            user.company_admin.save()

def add_user(user):
    custom_fields = get_custom_fields(user)

    # Register into mailing list
    try:
        mailing_id = mailing.add(user.first_name, user.last_name, user.email, custom_fields)
    except Exception, e:
        logger.error(u'Can\'t add user %s with email %s to mailing list: %s' % (user, user.email, str(e)))
    else:
        logger.info(u'User %s with email %s added to mailing list with id %s, custom_fields: %s' % (user, user.email, mailing_id, custom_fields))
        update_mailing_id(user, mailing_id)

def update_user(user):
    userprofile = user.get_profile()
    custom_fields = get_custom_fields(user)
    mailing_id = userprofile.mailing_id

    # Register into mailing list
    try:
        mailing_id = mailing.update(mailing_id, user.first_name, user.last_name, user.email, custom_fields)
    except Exception, e:
        logger.error(u'Can\'t update user %s with email %s to mailing list: %s' % (userprofile.user, user.email, str(e)))
    else:
        logger.info(u'User %s with email %s updated in mailing list with id %s, custom_fields: %s' % (userprofile.user, user.email, mailing_id, custom_fields))
        update_mailing_id(user, mailing_id)

def delete_user(user):
    mailing_id = None
    if models.is_competitor(user):
        mailing_id = user.get_profile().mailing_id
    elif is_company_admin(user):
        mailing_id = user.company_admin.mailing_id
        add_user(user)

    if not mailing_id:
        return

    # Unregister from mailing list
    try:
        mailing_id = mailing.delete(mailing_id)
    except Exception, e:
        logger.error(u'Can\'t delete user %s with email %s to mailing list: %s' % (user, user.email, str(e)))
    else:
        logger.info(u'User %s with email %s deleted from mailing list with id %s' % (user, user.email, mailing_id))
        update_mailing_id(user, mailing_id)

def add_or_update_user(user):
    if not user.is_active:
        delete_user(user)
    else:
        if models.is_competitor(user) and user.get_profile().mailing_id:
            update_user(user)
        else:
            add_user(user)

