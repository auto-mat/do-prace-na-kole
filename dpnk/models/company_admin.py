# -*- coding: utf-8 -*-

# Author: Hynek Hanke <hynek.hanke@auto-mat.cz>
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2016 o.s. Auto*Mat
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

from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _

from .user_profile import UserProfile
from ..email import company_admin_approval_mail, company_admin_rejected_mail


class CompanyAdmin(models.Model):
    """Profil firemního koordinátora"""

    COMPANY_APPROVAL = (
        ('approved', _(u"Odsouhlasený")),
        ('undecided', _(u"Nerozhodnuto")),
        ('denied', _(u"Zamítnutý")),
    )

    class Meta:
        verbose_name = _("Firemní koordinátor")
        verbose_name_plural = _(u"Firemní koordinátoři")
        unique_together = (
            ("userprofile", "campaign"),
        )

    userprofile = models.ForeignKey(
        UserProfile,
        verbose_name=_(u"Uživatelský profil"),
        related_name='company_admin',
        null=False,
        blank=False,
    )

    company_admin_approved = models.CharField(
        verbose_name=_("Schválena funkce firemního koordinátora"),
        choices=COMPANY_APPROVAL,
        max_length=16,
        null=False,
        default='approved',
    )

    motivation_company_admin = models.TextField(
        verbose_name=_(u"Zaměstnanecká pozice"),
        help_text=_("Napište nám prosím, jakou zastáváte u vašeho zaměstnavatele pozici"),
        default="",
        max_length=5000,
        null=True,
        blank=True,
    )

    administrated_company = models.ForeignKey(
        "Company",
        related_name="company_admin",
        verbose_name=_(u"Koordinovaná organizace"),
        null=True,
        blank=False,
    )

    campaign = models.ForeignKey(
        'Campaign',
        null=False,
        blank=False,
    )

    note = models.TextField(
        verbose_name=_(u"Interní poznámka"),
        max_length=500,
        null=True,
        blank=True,
    )

    can_confirm_payments = models.BooleanField(
        verbose_name=_(u"Může potvrzovat platby"),
        default=True,
        null=False,
    )
    will_pay_opt_in = models.BooleanField(
        verbose_name=_(u"Uživatel potvrdil, že bude plati za zaměstnance."),
        blank=False,
        default=False,
    )

    def is_approved(self):
        return self.company_admin_approved == 'approved'

    def company_has_invoices(self):
        return self.administrated_company.invoice_set.filter(campaign=self.campaign).exists()

    def user_attendance(self):
        from .user_attendance import UserAttendance
        try:
            return self.userprofile.userattendance_set.get(campaign=self.campaign)
        except UserAttendance.DoesNotExist:
            return None

    def get_userprofile(self):
        return self.userprofile

    def __str__(self):
        return self.userprofile.user.get_full_name()

    def save(self, *args, **kwargs):
        status_before_update = None
        if self.id:
            status_before_update = CompanyAdmin.objects.get(pk=self.id).company_admin_approved
        super().save(*args, **kwargs)

        if status_before_update != self.company_admin_approved:
            if self.company_admin_approved == 'approved':
                company_admin_approval_mail(self)
            elif self.company_admin_approved == 'denied':
                company_admin_rejected_mail(self)
