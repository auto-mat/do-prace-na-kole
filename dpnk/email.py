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

from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

import html2text

from . import util


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
            _("Máte nového člena"),
            'approval_request_%s.html',
            context,
        )


def register_mail(user_attendance):
    campaign_mail(
        user_attendance,
        _("Potvrzení registrace"),
        'registration_%s.html',
    )


def team_membership_approval_mail(user_attendance):
    campaign_mail(
        user_attendance,
        _("Jste členem týmu"),
        'team_membership_approval_%s.html',
    )


def team_membership_denial_mail(user_attendance, denier, reason):
    context = {
        'denier': denier,
        'reason': reason,
    }
    campaign_mail(
        user_attendance,
        _("Nemůžete se přidat k týmu"),
        'team_membership_denial_%s.html',
        context,
    )


def team_created_mail(user_attendance, team_name):
    context = {
        'team_name': team_name,
    }
    campaign_mail(
        user_attendance,
        _("Máte nový tým"),
        'team_created_%s.html',
        context,
    )


def invitation_mail(user_attendance, email, invited=None):
    context = {
        'inviting': user_attendance,
        'invited': invited,
    }
    campaign_mail(
        user_attendance,
        _("Pozvánka"),
        'invitation_%s.html',
        context,
        email=email,
    )


def payment_confirmation_mail(user_attendance):
    campaign_mail(
        user_attendance,
        _("Startovné je uhrazeno"),
        'payment_confirmation_%s.html',
    )


def payment_confirmation_company_mail(user_attendance):
    context = {
        'company': user_attendance.team.subsidiary.company if user_attendance.team else _(u"(není vybraná)", user_attendance.userprofile.language),
    }
    campaign_mail(
        user_attendance,
        _("Jste ve hře"),
        'payment_confirmation_company_%s.html',
        context,
    )


def company_admin_register_competitor_mail(user_attendance):
    context = {
        'company': user_attendance.team.subsidiary.company,
    }
    campaign_mail(
        user_attendance,
        _("Potvrzení registrace firemního koordinátora"),
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
        _("Potvrzení registrace firemního koordinátora"),
        'company_admin_register_competitor_%s.html',
    )


def company_admin_approval_mail(company_admin):
    company_admin_mail(
        company_admin,
        _("Jste firemní koordinátor"),
        'company_admin_approval_%s.html',
    )


def company_admin_rejected_mail(company_admin):
    company_admin_mail(
        company_admin,
        _("Špatné zprávy"),
        'company_admin_rejected_%s.html',
    )


def unfilled_rides_mail(user_attendance, days_unfilled):
    campaign_mail(
        user_attendance,
        _("Poslední šance doplnit jízdy"),
        'unfilled_rides_notification_%s.html',
        {'days_unfilled': days_unfilled},
    )


def new_invoice_mail(invoice):
    invoice_mail(
        invoice,
        _("Nová faktura vystavena"),
        'new_invoice_notification_%s.html',
    )


def unpaid_invoice_mail(invoice):
    invoice_mail(
        invoice,
        _("Nezaplacená faktura"),
        'unpaid_invoice_notification_%s.html',
    )


def invoice_mail(invoice, subject, template):
    extra_context = {
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


def campaign_mail(user_attendance, subject, template_path, extra_context=None, email=None, userprofile=None, campaign=None):
    if extra_context is None:
        extra_context = {}
    if userprofile is None:
        userprofile = user_attendance.userprofile
    if campaign is None:
        campaign = user_attendance.campaign
    if email is None:
        email = userprofile.user.email
    subject = "[" + str(campaign) + "] " + _(subject, userprofile.language)
    context = {
        'user_attendance': user_attendance,
        'absolute_uri': util.get_base_url(slug=(user_attendance.campaign if user_attendance else campaign).slug),
        'email': email,
        'lang_code': userprofile.language,
        'subject': subject,
    }
    context.update(extra_context)
    template = get_template('email/' + template_path % userprofile.language)
    message = template.render(context)

    # Uncoment this to check to generate email files in dpnk-test-messages
    # with open('dpnk-test-messages/%s.html' % template_path % userprofile.language, "w") as f:
    #     f.write(message)
    txt_summary = html2text.html2text(message)
    email = EmailMultiAlternatives(
        subject=subject,
        body=txt_summary,
        to=[email],
    )
    email.attach_alternative(message, "text/html")
    email.send(fail_silently=False)
