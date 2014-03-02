# -*- coding: utf-8 -*-
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2013 o.s. Auto*Mat
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
from django.template.loader import get_template
from django.core.mail import send_mail
from django.template import Context
from django.conf import settings
from django.utils.translation import gettext as _
import models

def approval_request_mail(user_attendance):
    template = get_template('email/approval_request.html')
    email = user_attendance.team.coordinator_campaign.userprofile.user.email
    message = template.render(Context({ 'coordinator': user_attendance.team.coordinator_campaign.userprofile.user,
        'user': user_attendance,
        'SITE_URL': settings.SITE_URL,
        }))
    send_mail(_("Do práce na kole 2013 - žádost o ověření členství"), message, None, [email], fail_silently=False)

def register_mail(user):
    template = get_template('email/registration.html')
    email = user.email
    message = template.render(Context({ 'user': user,
        'SITE_URL': settings.SITE_URL,
        }))
    send_mail(_("Do práce na kole 2013 - potvrzení registrace"), message, None, [email], fail_silently=False)

def team_membership_approval_mail(user):
    template = get_template('email/team_membership_approval.html')
    email = user.email
    message = template.render(Context({ 'user': user,
        'SITE_URL': settings.SITE_URL,
        }))
    send_mail(_("Do práce na kole 2013 - potvrzení ověření členství v týmu"), message, None, [email], fail_silently=False)

def team_membership_denial_mail(user, reason):
    template = get_template('email/team_membership_denial.html')
    email = user.email
    message = template.render(Context({ 'user': user,
        'SITE_URL': settings.SITE_URL,
        'reason': reason,
        }))
    send_mail(_("Do práce na kole 2013 - ZAMÍTNUTÍ členství v týmu"), message, None, [email], fail_silently=False)

def team_created_mail(user):
    template = get_template('email/team_created.html')
    email = user.email
    message = template.render(Context({ 'user': user,
        'SITE_URL': settings.SITE_URL,
        }))
    send_mail(_("Do práce na kole 2013 - potvrzení registrace"), message, None, [email], fail_silently=False)

def invitation_mail(user, emails):
    template = get_template('email/invitation.html')
    for email in emails:
        if len(email) != 0:
            message = template.render(Context({ 'user': user,
                'SITE_URL': settings.SITE_URL,
                'email': email,
                }))
            send_mail(_("Do práce na kole 2013 - pozvánka do týmu"), message, None, [email], fail_silently=False)

def payment_confirmation_mail(user):
    template = get_template('email/payment_confirmation.html')
    email = user.email
    message = template.render(Context({
                'user': user,
                'SITE_URL': settings.SITE_URL}))
    send_mail(_("Do práce na kole 2013 - přijetí platby"), message, None, [email], fail_silently=False)

def payment_confirmation_company_mail(user):
    template = get_template('email/payment_comfirmation_company.html')
    email = user.email
    message = template.render(Context({
                'user': user,
                'company': models.get_company(user),
                'SITE_URL': settings.SITE_URL}))
    send_mail(_("Do práce na kole 2013 - přijetí platby"), message, None, [email], fail_silently=False)

def company_admin_register_competitor_mail(user):
    template = get_template('email/company_admin_register_competitor.html')
    email = user.email
    message = template.render(Context({ 'user': user,
        'company': models.get_company(user),
        'SITE_URL': settings.SITE_URL,
        }))
    send_mail(_("Do práce na kole 2013 - firemní správce - potvrzení registrace"), message, None, [email], fail_silently=False)

def company_admin_register_no_competitor_mail(user):
    template = get_template('email/company_admin_register_no_competitor.html')
    email = user.email
    message = template.render(Context({ 'user': user,
        'company': models.get_company(user),
        'SITE_URL': settings.SITE_URL,
        }))
    send_mail(_("Do práce na kole 2013 - firemní správce - potvrzení registrace"), message, None, [email], fail_silently=False)

def company_admin_approval_mail(user):
    template = get_template('email/company_admin_approval.html')
    email = user.email
    message = template.render(Context({ 'user': user,
        'company': models.get_company(user),
        'SITE_URL': settings.SITE_URL,
        }))
    send_mail(_("Do práce na kole 2013 - firemní správce - schválení správcovství firmy"), message, None, [email], fail_silently=False)

def company_admin_rejected_mail(user):
    template = get_template('email/company_admin_rejected.html')
    email = user.email
    message = template.render(Context({ 'user': user,
        'company': models.get_company(user),
        'SITE_URL': settings.SITE_URL,
        }))
    send_mail(_("Do práce na kole 2013 - firemní správce - zamítnutí správcovství firmy"), message, None, [email], fail_silently=False)
