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
import datetime

from bulk_update.manager import BulkUpdateManager

from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from .. import util


class Trip(models.Model):
    """Cesty"""
    DIRECTIONS = [
        ('trip_to', _(u"Tam")),
        ('trip_from', _(u"Zpět")),
    ]
    DIRECTIONS_DICT = dict(DIRECTIONS)
    MODES = [
        ('bicycle', _("Kolo")),
        ('by_foot', _("Chůze/běh")),
        ('by_other_vehicle', _("Jinak")),
        ('no_work', _("Žádná cesta")),
    ]

    class Meta:
        verbose_name = _(u"Cesta")
        verbose_name_plural = _(u"Cesty")
        unique_together = (("user_attendance", "date", "direction"),)
        ordering = ('date', '-direction')
    objects = BulkUpdateManager()

    user_attendance = models.ForeignKey(
        'UserAttendance',
        related_name="user_trips",
        null=True,
        blank=False,
        default=None,
    )
    direction = models.CharField(
        verbose_name=_(u"Směr cesty"),
        choices=DIRECTIONS,
        max_length=20,
        default=None,
        null=False,
        blank=False,
    )
    date = models.DateField(
        verbose_name=_(u"Datum cesty"),
        default=datetime.date.today,
        null=False,
    )
    commute_mode = models.CharField(
        verbose_name=_(u"Mód dopravy"),
        choices=MODES,
        max_length=20,
        default=None,
        null=False,
        blank=False,
    )
    distance = models.FloatField(
        verbose_name=_(u"Ujetá vzdálenost"),
        null=True,
        blank=True,
        default=None,
        validators=[
            MaxValueValidator(1000),
            MinValueValidator(0),
        ],
    )

    def active(self):
        return util.day_active(self.date, self.user_attendance.campaign)

    def has_gpxfile(self):
        return hasattr(self, "gpxfile")


@receiver(post_save, sender=Trip)
def trip_post_save(sender, instance, **kwargs):
    if instance.user_attendance and not hasattr(instance, "dont_recalculate"):
        from .. import results
        results.recalculate_result_competitor(instance.user_attendance)
