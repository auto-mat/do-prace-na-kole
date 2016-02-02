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
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


def approval_request_mail(user_attendance):
    for team_member in user_attendance.team.members():
        if user_attendance == team_member:
            continue
        template = get_template('email/approval_request_%s.html' % user_attendance.userprofile.language)
        email = team_member.userprofile.user.email
        message = template.render({
            'team_member': team_member,
            'new_user': user_attendance,
            'SITE_URL': settings.SITE_URL,
        })
        send_mail(_(u"%s - žádost o ověření členství" % user_attendance.campaign), message, None, [email], fail_silently=False)


def invitation_register_mail(inviting, invited):
    template = get_template('email/invitation_%s.html' % invited.userprofile.language)
    email = invited.userprofile.user.email
    if not invited:
        lang_code = inviting.userprofile.language
    else:
        lang_code = inviting.userprofile.language
    message = template.render({
        'inviting': inviting,
        'invited': invited,
        'lang_code': lang_code,
        'email': email,
        'SITE_URL': settings.SITE_URL,
    })
    send_mail(_(u"%s - potvrzení registrace" % inviting.campaign), message, None, [email], fail_silently=False)


def register_mail(user_attendance):
    template = get_template('email/registration_%s.html' % user_attendance.userprofile.language)
    email = user_attendance.userprofile.user.email
    message = template.render({
        'user': user_attendance,
        'SITE_URL': settings.SITE_URL,
    })
    send_mail(_(u"%s - potvrzení registrace" % user_attendance.campaign), message, None, [email], fail_silently=False)


def team_membership_approval_mail(user_attendance):
    template = get_template('email/team_membership_approval_%s.html' % user_attendance.userprofile.language)
    email = user_attendance.userprofile.user.email
    message = template.render({
        'user': user_attendance,
        'SITE_URL': settings.SITE_URL,
    })
    send_mail(_(u"%s - potvrzení ověření členství v týmu" % user_attendance.campaign), message, None, [email], fail_silently=False)


def team_membership_denial_mail(user_attendance, denier, reason):
    template = get_template('email/team_membership_denial_%s.html' % user_attendance.userprofile.language)
    email = user_attendance.userprofile.user.email
    message = template.render({
        'user': user_attendance,
        'denier': denier,
        'SITE_URL': settings.SITE_URL,
        'reason': reason,
    })
    send_mail(_(u"%s - ZAMÍTNUTÍ členství v týmu" % user_attendance.campaign), message, None, [email], fail_silently=False)


def team_created_mail(user_attendance):
    template = get_template('email/team_created_%s.html' % user_attendance.userprofile.language)
    email = user_attendance.userprofile.user.email
    message = template.render({
        'user': user_attendance,
        'SITE_URL': settings.SITE_URL,
    })
    send_mail(_(u"%s - potvrzení vytvoření týmu" % user_attendance.campaign), message, None, [email], fail_silently=False)


def invitation_mail(user_attendance, email):
    template = get_template('email/invitation_%s.html' % user_attendance.userprofile.language)
    if len(email) != 0:
        message = template.render({
            'inviting': user_attendance,
            'lang_code': user_attendance.userprofile.language,
            'SITE_URL': settings.SITE_URL,
            'email': email,
        })
        send_mail(_(u"%s - pozvánka do týmu" % user_attendance.campaign), message, None, [email], fail_silently=False)


def payment_confirmation_mail(user_attendance):
    template = get_template('email/payment_confirmation_%s.html' % user_attendance.userprofile.language)
    email = user_attendance.userprofile.user.email
    message = template.render({
        'user': user_attendance,
        'SITE_URL': settings.SITE_URL})
    send_mail(_(u"%s - přijetí platby") % user_attendance.campaign, message, None, [email], fail_silently=False)


def payment_confirmation_company_mail(user_attendance):
    template = get_template('email/payment_comfirmation_company_%s.html' % user_attendance.userprofile.language)
    email = user_attendance.userprofile.user.email
    message = template.render({
        'user': user_attendance,
        'company': user_attendance.team.subsidiary.company if user_attendance.team else _(u"(není vybraná)"),
        'SITE_URL': settings.SITE_URL})
    send_mail(_(u"%s - přijetí platby" % user_attendance.campaign), message, None, [email], fail_silently=False)


def company_admin_register_competitor_mail(user_attendance):
    template = get_template('email/company_admin_register_competitor_%s.html' % user_attendance.userprofile.language)
    email = user_attendance.userprofile.user.email
    message = template.render({
        'user': user_attendance,
        'company': user_attendance.team.subsidiary.company,
        'SITE_URL': settings.SITE_URL,
    })
    send_mail(_(u"%s - firemní koordinátor - potvrzení registrace" % user_attendance.campaign), message, None, [email], fail_silently=False)


def company_admin_register_no_competitor_mail(company_admin, company):
    template = get_template('email/company_admin_register_no_competitor_%s.html' % company_admin.get_userprofile().language)
    email = company_admin.user.email
    message = template.render({
        'company_admin': company_admin,
        'company': company,
        'SITE_URL': settings.SITE_URL,
    })
    send_mail(_(u"%s - firemní koordinátor - potvrzení registrace" % company_admin.campaign), message, None, [email], fail_silently=False)


def company_admin_approval_mail(company_admin):
    template = get_template('email/company_admin_approval_%s.html' % company_admin.get_userprofile().language)
    email = company_admin.user.email
    message = template.render({
        'company_admin': company_admin,
        'company': company_admin.administrated_company,
        'SITE_URL': settings.SITE_URL,
    })
    send_mail(_(u"%s - firemní koordinátor - schválení správcovství firmy" % company_admin.campaign), message, None, [email], fail_silently=False)


def company_admin_rejected_mail(company_admin):
    template = get_template('email/company_admin_rejected_%s.html' % company_admin.get_userprofile().language)
    email = company_admin.user.email
    message = template.render({
        'company_admin': company_admin,
        'company': company_admin.administrated_company,
        'SITE_URL': settings.SITE_URL,
    })
    send_mail(_(u"%s - firemní koordinátor - zamítnutí správcovství firmy" % company_admin.campaign), message, None, [email], fail_silently=False)
