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

from .company import Company
from .team import Team
from .user_attendance import UserAttendance


class CompetitionResult(models.Model):
    """Výsledek soutěže"""
    class Meta:
        verbose_name = _(u"Výsledek soutěže")
        verbose_name_plural = _(u"Výsledky soutěží")
        unique_together = (("user_attendance", "competition"), ("team", "competition"))

    user_attendance = models.ForeignKey(
        UserAttendance,
        related_name="competitions_results",
        null=True,
        blank=True,
        default=None,
    )
    team = models.ForeignKey(
        Team,
        related_name="competitions_results",
        null=True,
        blank=True,
        default=None,
    )
    company = models.ForeignKey(
        Company,
        related_name="company_results",
        null=True,
        blank=True,
        default=None,
    )
    competition = models.ForeignKey(
        'Competition',
        related_name="results",
        null=False,
        blank=False,
    )
    result = models.DecimalField(
        verbose_name=_(u"Výsledek"),
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
        default=None,
        db_index=True,
    )
    result_divident = models.FloatField(
        verbose_name=_("Dělenec"),
        null=True,
        blank=True,
        default=None,
    )
    result_divisor = models.FloatField(
        verbose_name=_("Dělitel"),
        null=True,
        blank=True,
        default=None,
    )
    created = models.DateTimeField(
        verbose_name=_(u"Datum vytvoření"),
        auto_now_add=True,
        null=True,
    )
    updated = models.DateTimeField(
        verbose_name=_(u"Datum poslední změny"),
        auto_now=True,
        null=True,
    )

    def get_sequence_range(self):
        """
        Return range of places of this result.
        Means, that the competitor is placed on one or more places.
        """
        lower_range = CompetitionResult.objects.filter(
            competition=self.competition,
            result__gt=self.result,
        ).count() + 1
        upper_range = CompetitionResult.objects.filter(
            competition=self.competition,
            result__gte=self.result,
        ).count()
        return lower_range, upper_range

    def get_team(self):
        if self.competition.competitor_type in ['liberos', 'single_user']:
            return self.user_attendance.team
        if self.competition.competitor_type == 'team':
            return self.team

    def get_company(self):
        if self.competition.competitor_type == 'company':
            return self.company
        team = self.get_team()
        if team:
            return team.subsidiary.company

    def get_subsidiary(self):
        return "%s / %s" % (self.get_street(), self.get_company())

    def get_street(self):
        team = self.get_team()
        if team:
            return team.subsidiary.address_street

    def get_city(self):
        team = self.get_team()
        if team:
            return team.subsidiary.city

    def get_result(self):
        """ Get result in kilometers rounded to reasonable number of decimal places. """
        return round(self.result, 1)

    def get_result_percentage(self):
        """
        Get result as percentage of all rides.
        @return percentage in rounded integer
        """
        if self.result:
            return round(self.result * 100, 1)
        else:
            return 0

    def __str__(self):
        if self.competition.competitor_type == 'team':
            if self.team:
                return "%s" % self.team.name
        elif self.competition.competitor_type == 'company':
            if self.company:
                return "%s" % self.company.name
        else:
            if self.user_attendance:
                return "%s" % self.user_attendance.userprofile.name()
        return ""

    def user_attendances(self):
        competition = self.competition
        if competition.competitor_type == 'single_user' or competition.competitor_type == 'libero':
            return [self.user_attendance]
        elif competition.competitor_type == 'team':
            return self.team.members()
        elif competition.competitor_type == 'company':
            return UserAttendance.objects.filter(team__subsidiary__company=self.company)
