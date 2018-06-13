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


def _(string, locale=None):
    if locale is None:
        return string
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
        context = {
            'team_member': team_member,
            'new_user': user_attendance,
        }
        campaign_mail(
            team_member,
            _("žádost o ověření členství"),
            'approval_request_%s.html',
            context,
        )


def invitation_register_mail(inviting, invited):
    context = {
        'inviting': inviting,
        'invited': invited,
    }
    campaign_mail(
        invited,
        _("potvrzení registrace"),
        'invitation_%s.html',
        context,
    )


def register_mail(user_attendance):
    campaign_mail(
        user_attendance,
        _("potvrzení registrace"),
        'registration_%s.html',
        all_langs=True,
    )


def team_membership_approval_mail(user_attendance):
    campaign_mail(
        user_attendance,
        _("potvrzení ověření členství v týmu"),
        'team_membership_approval_%s.html',
    )


def team_membership_denial_mail(user_attendance, denier, reason):
    context = {
        'denier': denier,
        'reason': reason,
    }
    campaign_mail(
        user_attendance,
        _("ZAMÍTNUTÍ členství v týmu"),
        'team_membership_denial_%s.html',
        context,
    )


def team_created_mail(user_attendance, team_name):
    context = {
        'team_name': team_name,
    }
    campaign_mail(
        user_attendance,
        _("potvrzení vytvoření týmu"),
        'team_created_%s.html',
        context,
    )


def invitation_mail(user_attendance, email):
    context = {
        'inviting': user_attendance,
    }
    campaign_mail(
        user_attendance,
        _("pozvánka do týmu"),
        'invitation_%s.html',
        context,
        all_langs=True,
        email=email,
    )


def payment_confirmation_mail(user_attendance):
    campaign_mail(
        user_attendance,
        _("přijetí platby"),
        'payment_confirmation_%s.html',
    )


def payment_confirmation_company_mail(user_attendance):
    context = {
        'company': user_attendance.team.subsidiary.company if user_attendance.team else _(u"(není vybraná)", user_attendance.userprofile.language),
    }
    campaign_mail(
        user_attendance,
        _("přijetí platby"),
        'payment_confirmation_company_%s.html',
        context,
    )


def company_admin_register_competitor_mail(user_attendance):
    context = {
        'company': user_attendance.team.subsidiary.company,
    }
    campaign_mail(
        user_attendance,
        _("firemní koordinátor - potvrzení registrace"),
        'company_admin_register_competitor_%s.html',
        context,
    )


def company_admin_mail(company_admin, subject, template):
    context = {
        'company_admin': company_admin,
        'company': company_admin.administrated_company,
    }
    campaign_mail(
        company_admin.user_attendance(),
        subject,
        template,
        context,
        userprofile=company_admin.userprofile,
        campaign=company_admin.campaign,
    )


def company_admin_register_no_competitor_mail(company_admin):
    company_admin_mail(
        company_admin,
        _("firemní koordinátor - potvrzení registrace"),
        'company_admin_register_no_competitor_%s.html',
    )


def company_admin_approval_mail(company_admin):
    company_admin_mail(
        company_admin,
        _("firemní koordinátor - schválení správcovství organizace"),
        'company_admin_approval_%s.html',
    )


def company_admin_rejected_mail(company_admin):
    company_admin_mail(
        company_admin,
        _("firemní koordinátor - zamítnutí správcovství organizace"),
        'company_admin_rejected_%s.html',
    )


def unfilled_rides_mail(user_attendance, days_unfilled):
    campaign_mail(
        user_attendance,
        _("připomenutí nevyplněných jízd"),
        'unfilled_rides_notification_%s.html',
        {'days_unfilled': days_unfilled},
    )


def new_invoice_mail(invoice):
    invoice_mail(
        invoice,
        _("byla Vám vystavena faktura"),
        'new_invoice_notification_%s.html',
    )


def unpaid_invoice_mail(invoice):
    invoice_mail(
        invoice,
        _("připomenutí nezaplacené faktury"),
        'unpaid_invoice_notification_%s.html',
    )


def invoice_mail(invoice, subject, template):
    extra_context = {
        'invoice_url': invoice.invoice_pdf.url,
        'invoice': invoice,
    }
    if not invoice.paid():
        for admin in invoice.company.company_admin.filter(campaign=invoice.campaign):
            campaign_mail(
                admin.user_attendance(),
                subject,
                template,
                extra_context,
            )


def campaign_mail(user_attendance, subject, template_path, extra_context=None, all_langs=False, email=None, userprofile=None, campaign=None):
    if extra_context is None:
        extra_context = {}
    if userprofile is None:
        userprofile = user_attendance.userprofile
    if campaign is None:
        campaign = user_attendance.campaign
    if email is None:
        email = userprofile.user.email
    context = {
        'user_attendance': user_attendance,
        'SITE_URL': settings.SITE_URL,
        'email': email,
    }
    context.update(extra_context)
    included_langs = set()
    if all_langs:
        langs = [userprofile.language, 'cs', 'en']
    else:
        langs = [userprofile.language]
    message = ""
    subjects = []
    for language in langs:
        if language not in included_langs:
            included_langs.add(language)
            subjects.append(_(subject, language))
            template = get_template('email/' + template_path % language)
            context['lang_code'] = language
            message += template.render(context)
    subject = str(campaign) + " - " + " / ".join(subjects)
    send_mail(subject, message, None, [email], fail_silently=False)
