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
import gettext
import os

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import get_template


def _(string, locale):
    return gettext.translation(
        'django',
        os.path.join(os.path.dirname(__file__), 'locale'),
        languages=[locale],
        fallback=False,
    ).gettext(
        string,
    )


def approval_request_mail(user_attendance):
    for team_member in user_attendance.team.members():
        if user_attendance == team_member:
            continue
        language = user_attendance.userprofile.language
        template = get_template('email/approval_request_%s.html' % language)
        email = team_member.userprofile.user.email
        message = template.render({
            'team_member': team_member,
            'new_user': user_attendance,
            'SITE_URL': settings.SITE_URL,
        })
        subject = _("%s - žádost o ověření členství", language) % user_attendance.campaign
        send_mail(subject, message, None, [email], fail_silently=False)


def invitation_register_mail(inviting, invited):
    language = invited.userprofile.language
    template = get_template('email/invitation_%s.html' % language)
    email = invited.userprofile.user.email
    message = template.render({
        'inviting': inviting,
        'invited': invited,
        'lang_code': language,
        'email': email,
        'SITE_URL': settings.SITE_URL,
    })
    subject = _("%s - potvrzení registrace", language) % inviting.campaign
    send_mail(subject, message, None, [email], fail_silently=False)


def register_mail(user_attendance):
    language = user_attendance.userprofile.language
    subject = _("%s - potvrzení registrace", language) % user_attendance.campaign
    templates = {
        "cs": get_template('email/registration_cs.html'),
        "en": get_template('email/registration_en.html'),
    }
    email = user_attendance.userprofile.user.email
    if language == "cs":
        languages = ("cs", "en")
    else:
        languages = ("en", "cs")
    message = ""
    for language in languages:
        template = templates[language]
        message += template.render({
            'user': user_attendance,
            'language': language,
            'SITE_URL': settings.SITE_URL,
        })
        message += "\n --- \n"
    message += user_attendance.campaign.email_footer
    send_mail(subject, message, None, [email], fail_silently=False)


def team_membership_approval_mail(user_attendance):
    language = user_attendance.userprofile.language
    template = get_template('email/team_membership_approval_%s.html' % language)
    email = user_attendance.userprofile.user.email
    message = template.render({
        'user': user_attendance,
        'SITE_URL': settings.SITE_URL,
    })
    subject = _("%s - potvrzení ověření členství v týmu", language) % user_attendance.campaign
    send_mail(subject, message, None, [email], fail_silently=False)


def team_membership_denial_mail(user_attendance, denier, reason):
    language = user_attendance.userprofile.language
    template = get_template('email/team_membership_denial_%s.html' % language)
    email = user_attendance.userprofile.user.email
    message = template.render({
        'user': user_attendance,
        'denier': denier,
        'SITE_URL': settings.SITE_URL,
        'reason': reason,
    })
    subject = _("%s - ZAMÍTNUTÍ členství v týmu", language) % user_attendance.campaign
    send_mail(subject, message, None, [email], fail_silently=False)


def team_created_mail(user_attendance, team_name):
    language = user_attendance.userprofile.language
    template = get_template('email/team_created_%s.html' % language)
    email = user_attendance.userprofile.user.email
    message = template.render({
        'user': user_attendance,
        'team_name': team_name,
        'SITE_URL': settings.SITE_URL,
    })
    subject = _("%s - potvrzení vytvoření týmu", language) % user_attendance.campaign
    send_mail(subject, message, None, [email], fail_silently=False)


def invitation_mail(user_attendance, email):
    templates = {
        "cs": get_template('email/invitation_cs.html'),
        "en": get_template('email/invitation_en.html'),
    }

    if user_attendance.userprofile.language == "cs":
        languages = ("cs", "en")
    else:
        languages = ("en", "cs")
    message = ""
    for language in languages:
        template = templates[language]
        message += template.render({
            'inviting': user_attendance,
            'lang_code': language,
            'SITE_URL': settings.SITE_URL,
            'email': email,
        })
    if user_attendance.userprofile.language == "cs":
        subject = "%s - pozvánka do týmu (invitation to a team)" % user_attendance.campaign
    else:
        subject = "%s - invitation to a team (pozvánka do týmu)" % user_attendance.campaign
    send_mail(subject, message, None, [email], fail_silently=False)


def payment_confirmation_mail(user_attendance):
    language = user_attendance.userprofile.language
    template = get_template('email/payment_confirmation_%s.html' % language)
    email = user_attendance.userprofile.user.email
    message = template.render(
        {
            'user': user_attendance,
            'SITE_URL': settings.SITE_URL,
        },
    )
    subject = _("%s - přijetí platby", language) % user_attendance.campaign
    send_mail(subject, message, None, [email], fail_silently=False)


def payment_confirmation_company_mail(user_attendance):
    language = user_attendance.userprofile.language
    template = get_template('email/payment_comfirmation_company_%s.html' % language)
    email = user_attendance.userprofile.user.email
    message = template.render(
        {
            'user': user_attendance,
            'company': user_attendance.team.subsidiary.company if user_attendance.team else _(u"(není vybraná)", language),
            'SITE_URL': settings.SITE_URL,
        },
    )
    subject = _("%s - přijetí platby", language) % user_attendance.campaign
    send_mail(subject, message, None, [email], fail_silently=False)


def company_admin_register_competitor_mail(user_attendance):
    language = user_attendance.userprofile.language
    template = get_template('email/company_admin_register_competitor_%s.html' % language)
    email = user_attendance.userprofile.user.email
    message = template.render({
        'user': user_attendance,
        'company': user_attendance.team.subsidiary.company,
        'SITE_URL': settings.SITE_URL,
    })
    subject = _("%s - firemní koordinátor - potvrzení registrace", language) % user_attendance.campaign
    send_mail(subject, message, None, [email], fail_silently=False)


def company_admin_register_no_competitor_mail(company_admin, company):
    language = company_admin.get_userprofile().language
    template = get_template('email/company_admin_register_no_competitor_%s.html' % language)
    email = company_admin.userprofile.user.email
    message = template.render({
        'company_admin': company_admin,
        'company': company,
        'SITE_URL': settings.SITE_URL,
    })
    subject = _("%s - firemní koordinátor - potvrzení registrace", language) % company_admin.campaign
    send_mail(subject, message, None, [email], fail_silently=False)


def company_admin_approval_mail(company_admin):
    language = company_admin.get_userprofile().language
    template = get_template('email/company_admin_approval_%s.html' % language)
    email = company_admin.userprofile.user.email
    message = template.render({
        'company_admin': company_admin,
        'company': company_admin.administrated_company,
        'SITE_URL': settings.SITE_URL,
    })
    subject = _("%s - firemní koordinátor - schválení správcovství organizace", language) % company_admin.campaign
    send_mail(subject, message, None, [email], fail_silently=False)


def company_admin_rejected_mail(company_admin):
    language = company_admin.get_userprofile().language
    template = get_template('email/company_admin_rejected_%s.html' % language)
    email = company_admin.userprofile.user.email
    message = template.render({
        'company_admin': company_admin,
        'company': company_admin.administrated_company,
        'SITE_URL': settings.SITE_URL,
    })
    subject = _("%s - firemní koordinátor - zamítnutí správcovství organizace", language) % company_admin.campaign
    send_mail(subject, message, None, [email], fail_silently=False)


def unfilled_rides_mail(user_attendance, days_unfilled):
    language = user_attendance.userprofile.language
    template = get_template('email/unfilled_rides_notification_%s.html' % language)
    email = user_attendance.userprofile.user.email
    message = template.render({
        'user_attendance': user_attendance,
        'days_unfilled': days_unfilled,
        'lang_code': language,
        'SITE_URL': settings.SITE_URL,
    })
    subject = _("%s - připomenutí nevyplněných jízd", language) % user_attendance.campaign
    send_mail(subject, message, None, [email], fail_silently=False)
