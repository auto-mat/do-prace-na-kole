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
import random
import string

from denorm import denormalized, depend_on_related

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from .phase import Phase
from .subsidiary import Subsidiary

logger = logging.getLogger(__name__)


def validate_length(value, min_length=25):
    str_len = len(str(value))
    if str_len < min_length:
        raise ValidationError(_(u"Řetězec by neměl být kratší než %(min)s znaků a delší než %(max)s znaků") % {'min': min_length, 'max': str_len})


class Team(models.Model):
    """Profil týmu"""

    class Meta:
        verbose_name = _(u"Tým")
        verbose_name_plural = _(u"Týmy")
        ordering = ('name',)
        unique_together = (("name", "campaign"),)

    name = models.CharField(
        verbose_name=_(u"Název týmu"),
        max_length=50, null=True,
        unique=False,
    )
    subsidiary = models.ForeignKey(
        Subsidiary,
        verbose_name=_(u"Pobočka"),
        related_name='teams',
        null=False,
        blank=False,
    )
    invitation_token = models.CharField(
        verbose_name=_(u"Token pro pozvánky"),
        default="",
        max_length=100,
        null=False,
        blank=False,
        unique=True,
        validators=[validate_length],
    )
    campaign = models.ForeignKey(
        "Campaign",
        verbose_name=_(u"Kampaň"),
        null=False,
        blank=False,
    )

    @denormalized(
        models.IntegerField,
        verbose_name=_(u"Počet právoplatných členů týmu"),
        null=True,
        blank=False,
        db_index=True,
        default=None,
        skip={'invitation_token'})
    @depend_on_related('UserAttendance', skip={'created', 'updated'})
    def member_count(self):
        member_count = self.members().count()
        if self.campaign.too_much_members(member_count):
            logger.error("Too many members in team", extra={'team': self})
        return member_count

    def is_full(self):
        if self.member_count is not None:
            return self.member_count >= self.campaign.max_team_members

    @denormalized(
        models.IntegerField,
        verbose_name=_(u"Počet neschválených členů týmu"),
        null=True,
        blank=False,
        db_index=True,
        default=None,
        skip={'invitation_token'})
    @depend_on_related('UserAttendance', skip={'created', 'updated'})
    def unapproved_member_count(self):
        member_count = self.unapproved_members().count()
        return member_count

    def unapproved_members(self):
        return self.users.filter(userprofile__user__is_active=True, approved_for_team='undecided')

    def all_members(self):
        """ Return all members of this team, including unapproved. """
        return self.users.filter(userprofile__user__is_active=True)

    def undenied_members(self):
        """ Return approved members of this team. """
        return self.users.filter(
            userprofile__user__is_active=True,
        ).exclude(
            approved_for_team='denied',
        )

    def members(self):
        """ Return approved members of this team. """
        return self.users.filter(
            approved_for_team='approved',
            payment_status__in=('done', 'no_admission'),
            userprofile__user__is_active=True,
        ).order_by("id")

    @denormalized(models.IntegerField, null=True, skip={'invitation_token'})
    @depend_on_related('UserAttendance', skip={'created', 'updated'})
    def get_rides_count_denorm(self):
        rides_count = 0
        for member in self.members():
            rides_count += member.get_rides_count()
        return rides_count

    def get_working_trips_count(self):
        trip_count = 0
        for member in self.members():
            from .. import results
            trip_count += results.get_working_trips_count(member, self.campaign.phase("competition"))
        return trip_count

    def get_frequency(self):
        from .. import results
        try:
            return results.get_team_frequency(self.members(), self.campaign.phase("competition"))[2]
        except Phase.DoesNotExist:
            return 0

    @denormalized(models.FloatField, null=True, skip={'updated', 'created'})
    @depend_on_related('UserAttendance', skip={'created', 'updated'})
    def frequency(self):
        return self.get_frequency()

    def get_frequency_percentage(self):
        return (self.frequency or 0) * 100

    def get_length(self):
        from .. import results
        return results.get_team_length(self, self.campaign.phase("competition"))[2]

    @denormalized(models.TextField, null=True, skip={'invitation_token'})
    @depend_on_related('UserAttendance', skip={'created', 'updated'})
    def name_with_members(self):
        return u"%s (%s)" % (self.name, u", ".join([u.userprofile.name() for u in self.members()]))

    def __str__(self):
        return "%s" % self.name_with_members

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self.invitation_token == "":
            while True:
                invitation_token = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(30))
                if not Team.objects.filter(invitation_token=invitation_token).exists():
                    self.invitation_token = invitation_token
                    break

        super(Team, self).save(force_insert, force_update, *args, **kwargs)


class TeamName(Team):
    class Meta:
        proxy = True

    def __str__(self):
        return self.name


def pre_user_team_changed(sender, instance, changed_fields=None, **kwargs):
    field, (old, new) = next(iter(changed_fields.items()))
    new_team = Team.objects.get(pk=new) if new else None
    if new_team and new_team.campaign != instance.campaign:
        logger.error(u"UserAttendance %s campaign doesn't match team campaign" % instance)
    if instance.team and new_team.member_count == 0:
        instance.approved_for_team = 'approved'
    else:
        instance.approved_for_team = 'undecided'


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
