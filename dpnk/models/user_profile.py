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
import logging

from denorm import denormalized, depend_on_related

from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from .occupation import Occupation
from .. import mailing, util

logger = logging.getLogger(__name__)


class UserProfile(models.Model):
    """Uživatelský profil"""

    class Meta:
        verbose_name = _(u"Uživatelský profil")
        verbose_name_plural = _(u"Uživatelské profily")
        ordering = ["user__last_name", "user__first_name"]

    GENDER = (
        ('unknown', _(u'-------')),
        ('male', _(u'Muž')),
        ('female', _(u'Žena')),
    )

    LANGUAGE = [
        ('cs', _(u"Čeština")),
        ('en', _(u"Angličtna")),
    ]

    user = models.OneToOneField(
        User,
        related_name='userprofile',
        unique=True,
        null=False,
        blank=False,
    )
    nickname = models.CharField(
        _(u'Zobrazené jméno'),
        help_text=_(u'Zobrazí se ve všech veřejných výpisech místo vašeho jména. Zadávejte takové jméno, podle kterého vás vaši kolegové poznají'),
        max_length=60,
        blank=True,
        null=True,
    )
    telephone = models.CharField(
        verbose_name=_(u"Telefon"),
        max_length=30,
        null=False,
    )
    language = models.CharField(
        verbose_name=_(u"Jazyk emailové komunikace"),
        help_text=_(u"Jazyk, ve kterém vám budou docházet emaily z registračního systému"),
        choices=LANGUAGE,
        max_length=16,
        null=False,
        default='cs',
    )
    mailing_id = models.CharField(
        verbose_name=_(u"ID uživatele v mailing listu"),
        max_length=128,
        db_index=True,
        default=None,
        # TODO:
        # unique=True,
        null=True,
        blank=True,
    )
    mailing_hash = models.TextField(
        verbose_name=_(u"Hash poslední synchronizace s mailingem"),
        default=None,
        null=True,
        blank=True,
    )
    sex = models.CharField(
        verbose_name=_(u"Pohlaví"),
        help_text=_(u"Slouží k zařazení do výkonnostních kategorií"),
        choices=GENDER,
        default='unknown',
        max_length=50,
    )
    note = models.TextField(
        verbose_name=_(u"Interní poznámka"),
        null=True,
        blank=True,
    )
    administrated_cities = models.ManyToManyField(
        'City',
        related_name="city_admins",
        blank=True,
    )
    mailing_opt_in = models.NullBooleanField(
        verbose_name=_(u"Přeji si dostávat emailem informace o akcích, událostech a dalších informacích souvisejících se soutěží."),
        help_text=_(u"Odběr emailů můžete kdykoliv v průběhu soutěže zrušit."),
        default=None,
    )
    personal_data_opt_in = models.BooleanField(
        verbose_name=_(u"Souhlas se zpracováním osobních údajů."),
        blank=False,
        default=False,
    )
    occupation = models.ForeignKey(
        Occupation,
        verbose_name=_("Profese"),
        help_text=_("Nepovinné, bude zobrazeno ve pro zajímavost výsledcích"),
        null=True,
        blank=True,
    )
    age_group = models.PositiveIntegerField(
        verbose_name=_("Ročník narození"),
        help_text=_("Nepovinné, slouží pouze pro účely statistky"),
        null=True,
        blank=True,
        choices=[(i, i) for i in range(util.today().year, util.today().year - 100, -1)],
    )
    ecc_email = models.CharField(
        verbose_name=_("Email v ECC"),
        max_length=128,
        db_index=True,
        default=None,
        unique=True,
        null=False,
        blank=True,
    )
    ecc_password = models.CharField(
        verbose_name=_("Heslo v ECC"),
        max_length=128,
        db_index=True,
        default=None,
        null=False,
        blank=True,
    )

    @denormalized(models.IntegerField, default=0)
    @depend_on_related('CompanyAdmin')
    # This is here to update related_admin property on UserAttendance model
    def company_admin_count(self):
        return self.company_admin.count()

    def first_name(self):
        return self.user.first_name

    def last_name(self):
        return self.user.last_name

    def name(self):
        if self.nickname:
            return self.nickname
        else:
            full_name = self.user.get_full_name()
            email = self.user.email
            if full_name:
                return full_name
            elif email:
                return email
            else:
                return self.user.username

    def name_for_trusted(self):
        if self.nickname:
            full_name = self.user.get_full_name()
            if full_name:
                return u"%s (%s)" % (full_name, self.nickname)
            else:
                return u"%s (%s)" % (self.user.username, self.nickname)
        else:
            full_name = self.user.get_full_name()
            if full_name:
                return full_name
            else:
                return self.user.username

    def __str__(self):
        return self.name()

    def competition_edition_allowed(self, competition):
        return not competition.city.exists() or not self.administrated_cities.filter(pk__in=competition.city.values_list("pk", flat=True)).exists()

    def profile_complete(self):
        return self.sex and self.first_name() and self.last_name() and self.user.email and self.personal_data_opt_in

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self.mailing_id and UserProfile.objects.exclude(pk=self.pk).filter(mailing_id=self.mailing_id).count() > 0:
            logger.error(u"Mailing id %s is already used" % self.mailing_id)

        if self.pk is None:
            self.ecc_password = User.objects.make_random_password()
            self.ecc_email = "%s@dopracenakole.cz" % User.objects.make_random_password()
        super(UserProfile, self).save(force_insert, force_update, *args, **kwargs)


@receiver(post_save, sender=UserProfile)
def update_mailing_userprofile(sender, instance, created, **kwargs):
    for user_attendance in instance.userattendance_set.all():
        if not kwargs.get('raw', False) and user_attendance.campaign:
            mailing.add_or_update_user(user_attendance)
