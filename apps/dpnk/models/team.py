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
import math
import random
import re
import string

from author.decorators import with_author

from cache_utils.decorators import cached

from denorm import denormalized, depend_on_related

from django import forms
from django.conf import settings
from django.contrib.gis.db import models
from django.core.validators import MinLengthValidator
from django.utils.translation import ugettext_lazy as _

from memoize import mproperty

from .phase import Phase
from .subsidiary import Subsidiary, SubsidiaryInCampaign
from .team_diploma import TeamDiploma
from .. import util
from ..model_mixins import WithGalleryMixin

logger = logging.getLogger(__name__)


@with_author
class Team(WithGalleryMixin, models.Model):
    """Profil týmu"""

    class Meta:
        verbose_name = _("Tým")
        verbose_name_plural = _("Týmy")
        ordering = ("name",)
        unique_together = (("name", "campaign"),)

    name = models.CharField(
        verbose_name=_("Název týmu"),
        max_length=50,
        null=True,
        unique=False,
    )
    subsidiary = models.ForeignKey(
        Subsidiary,
        verbose_name=_("Pobočka"),
        related_name="teams",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    invitation_token = models.CharField(
        verbose_name=_("Token pro pozvánky"),
        default="",
        max_length=100,
        null=False,
        blank=False,
        unique=True,
        validators=[MinLengthValidator(25)],
    )
    campaign = models.ForeignKey(
        "Campaign",
        verbose_name=_("Kampaň"),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    gallery = models.ForeignKey(
        "photologue.Gallery",
        verbose_name=_("Galerie týmových fotek"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    icon = models.ForeignKey(
        "photologue.Photo",
        verbose_name=_("Ikona"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def icon_url(self):
        try:
            return self.lead_photo().image.url
        except AttributeError:
            return None

    def lead_photo(self):
        try:
            return self.get_gallery().photos.order_by("-date_added")[0]
        except IndexError:
            return None

    def subsidiary_in_campaign(self):
        return SubsidiaryInCampaign(self.subsidiary, self.campaign)

    @denormalized(
        models.IntegerField,
        verbose_name=_("Počet přihlášených členů týmu"),
        null=True,
        blank=False,
        db_index=True,
        default=None,
        skip={"invitation_token"},
    )
    @depend_on_related("UserAttendance", skip={"created", "updated"})
    def member_count(self):
        member_count = self.members.count()
        if self.campaign.too_much_members(member_count):
            logger.error("Too many members in team", extra={"team": self})
        return member_count

    @denormalized(
        models.IntegerField,
        verbose_name=_("Počet zaplacených členů týmu"),
        null=True,
        blank=False,
        db_index=True,
        default=None,
        skip={"invitation_token"},
    )
    @depend_on_related("UserAttendance", skip={"created", "updated"})
    def paid_member_count(self):
        member_count = self.paid_members().count()
        return member_count

    def is_full(self):
        if self.member_count is not None:
            return self.member_count >= self.campaign.max_team_members

    @denormalized(
        models.IntegerField,
        verbose_name=_("Počet neschválených členů týmu"),
        null=True,
        blank=False,
        db_index=True,
        default=None,
        skip={"invitation_token"},
    )
    @depend_on_related("UserAttendance", skip={"created", "updated"})
    def unapproved_member_count(self):
        member_count = self.unapproved_members().count()
        return member_count

    def unapproved_members(self):
        return self.users.filter(
            userprofile__user__is_active=True, approved_for_team="undecided"
        )

    def all_members(self):
        """Return all members of this team, including unapproved."""
        return self.users.filter(userprofile__user__is_active=True)

    def undenied_members(self):
        """Return approved members of this team."""
        return self.users.filter(userprofile__user__is_active=True,).exclude(
            approved_for_team="denied",
        )

    @property
    def members(self):
        """Return approved members of this team."""
        return self.users.filter(
            approved_for_team="approved",
            userprofile__user__is_active=True,
        ).order_by("id")

    def paid_members(self):
        """Return approved members of this team."""
        return self.members.filter(
            payment_status__in=("done", "no_admission"),
        )

    @denormalized(models.IntegerField, null=True, skip={"invitation_token"})
    @depend_on_related("UserAttendance", skip={"created", "updated"})
    def get_rides_count_denorm(self):
        rides_count = 0
        for member in self.members:
            rides_count += member.get_rides_count()
        return rides_count

    def get_working_trips_count(self):
        return sum(
            [member.get_working_rides_base_count() for member in self.paid_members()]
        )

    def get_remaining_rides_count(self):
        """Return number of rides, that are remaining to the end of competition"""
        members = self.paid_members().count()
        if members:
            return members * self.paid_members().first().get_remaining_rides_count()
        else:
            return 0

    def get_remaining_max_theoretical_frequency_percentage(self):
        """Return maximal frequency that can be achieved till end of the competition"""
        remaining_rides = self.get_remaining_rides_count()
        rides_count = self.get_rides_count_denorm
        working_rides_base = self.get_working_trips_count()
        return (
            (rides_count + remaining_rides)
            / (working_rides_base + remaining_rides)
            * 100
        )

    def get_missing_rides_for_minimum_percentage(self):
        """Return number of eco rides that would have to be done till end of competition to fullfill mimimal percentage"""
        minimal_percentage = self.campaign.minimum_percentage / 100
        rides_count = self.get_rides_count_denorm
        working_rides_base = self.get_working_trips_count()
        return math.ceil(
            (rides_count - minimal_percentage * working_rides_base)
            / (minimal_percentage - 1)
        )

    def get_frequency_result_(self):
        from .. import results

        return results.get_team_frequency(
            self.paid_members(), self.campaign.phase("competition")
        )

    def get_frequency_(self):
        members = self.paid_members()
        count = len(members)
        if count == 0:
            return 0, 0
        return sum([mem.frequency for mem in members]) / count, count

    def get_frequency(self):
        return self.get_frequency_()[0]

    def get_eco_trip_count(self):
        return sum([member.eco_trip_count() for member in self.paid_members()])

    def get_emissions(self, distance=None):
        return util.get_emissions(self.get_length())

    @denormalized(models.FloatField, null=True, skip={"updated", "created"})
    @depend_on_related("UserAttendance", skip={"created", "updated"})
    def frequency(self):
        return self.get_frequency()

    def get_frequency_percentage(self):
        return (self.frequency or 0) * 100

    def get_length(self):
        return sum([member.trip_length_total for member in self.paid_members()])

    @denormalized(models.TextField, null=True, skip={"invitation_token"})
    @depend_on_related("UserAttendance", skip={"created", "updated"})
    def name_with_members(self):
        members = self.members
        if members:
            names = [u.userprofile.name() for u in members]
            names.sort()
            return "%s (%s)" % (self.name, ", ".join(names))
        else:
            return self.name

    sandwich_model = TeamDiploma

    def get_sandwich_type(self):
        return self.campaign.team_diploma_sandwich_type

    def diploma(self):
        try:
            return TeamDiploma.objects.get(obj=self)
        except TeamDiploma.DoesNotExist:
            return None

    def get_diploma_pdf_url(self):
        diploma = self.diploma()
        if diploma:
            if re.match(r"http:|https", settings.MEDIA_URL):
                return diploma.pdf.url
            else:
                return f"{setting.MEDIA_URL}{diploma.pdf.url}"
        return diploma

    def __str__(self):
        return "%s" % self.name_with_members

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self.invitation_token == "":
            while True:
                invitation_token = "".join(
                    random.choice(string.ascii_uppercase + string.digits)
                    for x in range(30)
                )
                if not Team.objects.filter(invitation_token=invitation_token).exists():
                    self.invitation_token = invitation_token
                    break

        super().save(force_insert, force_update, *args, **kwargs)


class TeamName(Team):
    class Meta:
        proxy = True

    def __str__(self):
        if self.name:
            return self.name
        else:
            return "[%s]" % self.subsidiary.__str__()


class TeamAdminForm(forms.ModelForm):
    """Form for team in admin"""

    def __init__(self, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        self.fields["name"].required = False
        return ret_val

    class Meta:
        model = Team
        fields = (
            "name",
            "subsidiary",
            "campaign",
            "icon",
        )  # Required for fast loading after @with_author was added


def pre_user_team_changed(sender, instance, changed_fields=None, **kwargs):
    team_model_denorm_fields = ["member_count", "unapproved_member_count"]
    field, (old, new) = next(iter(changed_fields.items()))
    if old:
        Team.objects.get(pk=old).save(update_fields=team_model_denorm_fields)
    if new:
        new_team = Team.objects.get(pk=new)
        new_team.save(update_fields=team_model_denorm_fields)
    # TODO: rewrite this as a UserAttendance.is_approved() function
    if (instance.team or instance.team_id) and new_team.member_count == 0:
        instance.approved_for_team = "approved"
    else:
        instance.approved_for_team = "undecided"


def post_user_team_changed(sender, instance, changed_fields=None, **kwargs):
    from .. import results

    field, (old, new) = next(iter(changed_fields.items()))
    old_team = Team.objects.get(pk=old) if old else None
    new_team = Team.objects.get(pk=new) if new else None
    if new_team:
        results.recalculate_results_team(new_team)

    if old_team:
        results.recalculate_results_team(old_team)

    results.recalculate_result_competitor(instance)
