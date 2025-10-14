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
from django.core.validators import MinLengthValidator, RegexValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from vokativ import vokativ

from .occupation import Occupation
from .. import mailing, util
from ..model_mixins import WithGalleryMixin

logger = logging.getLogger(__name__)


class UserProfile(WithGalleryMixin, models.Model):
    """Uživatelský profil"""

    class Meta:
        verbose_name = _("Uživatelský profil")
        verbose_name_plural = _("Uživatelské profily")
        ordering = ["user__last_name", "user__first_name"]

        permissions = (("can_edit_all_cities", _("Může editovat všechna města")),)

    GENDER = [
        ("male", _("Muž")),
        ("female", _("Žena")),
    ]
    LANGUAGE = [
        ("cs", _("Čeština")),
        ("en", _("Angličtna")),
        ("sk", _("Slovenština")),
    ]
    RIDES_VIEWS = [
        ("calendar", _("Kalendář")),
        ("table", _("Tabulka")),
    ]
    NEWSLETTER = [
        ("challenge", _("Výzva")),
        ("events", _("Události")),
        ("mobility", _("Mobilita")),
        ("challenge-events", _("Výzva a události")),
        ("challenge-mobility", _("Výzva a mobilita")),
        ("events-mobility", _("Události a mobilita")),
        ("challenge-events-mobility", _("Výzva, události a mobilita")),
    ]
    AGE_GROUP = [(i, i) for i in range(util.today().year, util.today().year - 100, -1)]
    user = models.OneToOneField(
        User,
        related_name="userprofile",
        unique=True,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    nickname = models.CharField(
        _("Přezdívka"),
        help_text=_(
            "Chcete zůstat inkognito? Soutěžní přezdívka se zobrazuje ve veřejných výsledcích místo Vašeho jména."
        ),
        max_length=60,
        blank=True,
        null=True,
    )
    telephone = models.CharField(
        verbose_name=_("Telefonní číslo"),
        max_length=30,
        null=False,
        validators=[
            RegexValidator(
                r"^[0-9+ ]*$",
                _(
                    "Jak se do lesa volá, když nemáme správné číslo? Zkontrolujte si prosím vyplněný telefon."
                ),
            ),
            MinLengthValidator(
                9, message="Opravdu má Váš telefon %(show_value)s cifer?"
            ),
        ],
        help_text=_("Ozveme se, až bude balíček nachystaný."),
    )
    telephone_opt_in = models.NullBooleanField(
        verbose_name=_("Povolení telefonovat"),
        default=None,
    )
    language = models.CharField(
        verbose_name=_("Jazyk e-mailové komunikace"),
        help_text=_(
            "V tomto jazyce Vám budou přicházet e-maily z registračního systému"
        ),
        choices=LANGUAGE,
        max_length=16,
        null=False,
        default="cs",
    )
    default_rides_view = models.CharField(
        verbose_name=_("Defaultní předvolba vyplňování jízd"),
        choices=RIDES_VIEWS,
        max_length=16,
        null=True,
        blank=True,
        default=None,
    )
    mailing_id = models.CharField(
        verbose_name=_("ID uživatele v mailing listu"),
        max_length=128,
        db_index=True,
        default=None,
        # TODO:
        # unique=True,
        null=True,
        blank=True,
    )
    mailing_hash = models.TextField(
        verbose_name=_("Hash poslední synchronizace s mailingem"),
        default=None,
        null=True,
        blank=True,
    )
    sex = models.CharField(
        verbose_name=_("Pohlaví"),
        help_text=_(
            "Tato informace se nám bude hodit při rozřazování do výkonnostních kategorií."
        ),
        choices=GENDER,
        max_length=50,
        null=True,
        blank=True,
        default=None,
    )
    note = models.TextField(
        verbose_name=_("Interní poznámka"),
        null=True,
        blank=True,
    )
    administrated_cities = models.ManyToManyField(
        "City",
        related_name="city_admins",
        blank=True,
    )
    mailing_opt_in = models.NullBooleanField(
        verbose_name=_("Soutěžní e-maily"),
        help_text=_("Odběr e-mailů můžete kdykoliv v průběhu soutěže zrušit."),
        default=None,
    )
    occupation = models.ForeignKey(
        Occupation,
        verbose_name=_("Povolání"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    age_group = models.PositiveIntegerField(
        verbose_name=_("Ročník narození"),
        null=True,
        blank=True,
        choices=AGE_GROUP,
    )
    ecc_email = models.CharField(
        verbose_name=_("E-mail v ECC"),
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
    gallery = models.ForeignKey(
        "photologue.Gallery",
        verbose_name=_("Galerie fotek"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    newsletter = models.CharField(
        verbose_name=_("Odběr zpráv prostřednictvím e-mailů"),
        help_text=_("Odběr e-mailů můžete kdykoliv v průběhu soutěže zrušit."),
        max_length=30,
        choices=NEWSLETTER,
        null=True,
        blank=True,
    )

    @denormalized(models.IntegerField, default=0, skip={"gallery", "updated"})
    @depend_on_related("CompanyAdmin")
    # This is here to update related_admin property on UserAttendance model
    def company_admin_count(self):
        return self.company_admin.count()

    def get_sesame_token(self):
        from sesame.utils import get_token

        return get_token(self.user)

    def first_name(self):
        return self.user.first_name

    def last_name(self):
        return self.user.last_name

    def first_name_vokativ(self):
        woman = self.sex != "male"
        first_name = self.first_name()
        if len(first_name) > 0:
            return vokativ(first_name, last_name=False, woman=woman).title()

    def last_name_vokativ(self):
        woman = self.sex != "male"
        last_name = self.last_name()
        if len(last_name) > 0:
            return vokativ(last_name, last_name=True, woman=woman).title()

    def name(self, cs_vokativ=False):
        if self.nickname:
            return self.nickname
        else:
            if cs_vokativ:
                full_name = self.first_name_vokativ() + " " + self.last_name_vokativ()
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
                return "%s (%s)" % (full_name, self.nickname)
            else:
                return "%s (%s)" % (self.user.username, self.nickname)
        else:
            full_name = self.user.get_full_name()
            if full_name:
                return full_name
            else:
                return self.user.username

    def __str__(self):
        return self.name()

    def competition_edition_allowed(self, competition):
        return (
            not competition.city.exists()
            or not self.administrated_cities.filter(
                pk__in=competition.city.values_list("pk", flat=True)
            ).exists()
        )

    def profile_complete(self):
        return self.sex and self.first_name() and self.last_name() and self.user.email

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if (
            self.mailing_id
            and UserProfile.objects.exclude(pk=self.pk)
            .filter(mailing_id=self.mailing_id)
            .count()
            > 0
        ):
            logger.error("Mailing id %s is already used" % self.mailing_id)

        if self.pk is None:
            self.ecc_password = User.objects.make_random_password()
            self.ecc_email = "%s@dopracenakole.cz" % User.objects.make_random_password()

        super().save(force_insert, force_update, *args, **kwargs)


@receiver(post_save, sender=UserProfile)
def update_mailing_userprofile(sender, instance, created, **kwargs):
    if not getattr(
        instance, "don_save_mailing", False
    ):  # this signal was not caused by mailing id/hash update
        for user_attendance in instance.userattendance_set.all():
            if not kwargs.get("raw", False) and user_attendance.campaign:
                mailing.add_or_update_user(user_attendance)


@receiver(post_save, sender=UserProfile)
def clean_cache(sender, instance, created, **kwargs):
    if instance and kwargs.get("update_fields"):
        # Delete REST API cache
        cache = util.Cache(
            key=f"{util.register_challenge_serializer_base_cache_key_name}"
            f"{instance.id}"
        )
        if cache.data:
            del cache.data
