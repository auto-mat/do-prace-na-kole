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
import gzip

from author.decorators import with_author

from bulk_update.manager import BulkUpdateManager

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models.signals import pre_save, post_save  # noqa
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from django_gpxpy import gpx_parse

from .util import MAP_DESCRIPTION
from .. import util


def normalize_gpx_filename(instance, filename):
    return '-'.join([
        'gpx_tracks/dpnk-%s/track' % instance.user_attendance.campaign.pk,
        datetime.datetime.now().strftime("%Y-%m-%d"),
        slugify(filename),
    ])


@with_author
class Trip(models.Model):
    """Jízdy"""
    DIRECTIONS = [
        ('trip_to', _(u"Tam")),
        ('trip_from', _(u"Zpět")),
    ]
    DIRECTIONS_DICT = dict(DIRECTIONS)

    class Meta:
        verbose_name = _("Jízda")
        verbose_name_plural = _("Jízdy")
        unique_together = (("user_attendance", "date", "direction"),)
        ordering = ('date', '-direction')
    objects = BulkUpdateManager()

    user_attendance = models.ForeignKey(
        'UserAttendance',
        related_name="user_trips",
        null=True,
        blank=False,
        default=None,
        on_delete=models.CASCADE,
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
    commute_mode = models.ForeignKey(
        'CommuteMode',
        verbose_name=_("Dopravní prostředek"),
        on_delete=models.CASCADE,
        default=1,
        null=False,
        blank=False,
    )
    track = models.MultiLineStringField(
        verbose_name=_(u"trasa"),
        help_text=MAP_DESCRIPTION,
        srid=4326,
        null=True,
        blank=True,
        geography=True,
    )
    gpx_file = models.FileField(
        verbose_name=_(u"GPX soubor"),
        help_text=_(
            mark_safe(
                "Zadat trasu nahráním souboru GPX. "
                "Pro vytvoření GPX souboru s trasou můžete použít vyhledávání na naší "
                "<a href='https://mapa.prahounakole.cz/#hledani' target='_blank'>mapě</a>."
            ),
        ),
        upload_to=normalize_gpx_filename,
        blank=True,
        null=True,
        max_length=512,
    )
    distance = models.FloatField(
        verbose_name=_(u"Ujetá vzdálenost (Km)"),
        null=True,
        blank=True,
        default=None,
        validators=[
            MaxValueValidator(1000),
            MinValueValidator(0),
        ],
    )
    duration = models.PositiveIntegerField(
        verbose_name=_("Doba v sekundách"),
        null=True,
        blank=True,
    )
    from_application = models.BooleanField(
        verbose_name=_(u"Nahráno z aplikace"),
        default=False,
        null=False,
    )
    source_application = models.CharField(
        verbose_name=_("Zdrojová aplikace"),
        max_length=255,
        null=True,
        blank=True,
    )
    source_id = models.CharField(
        verbose_name=_("Identifikátor v původní aplikaci"),
        max_length=255,
        null=True,
        blank=True,
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

    def active(self):
        return self.user_attendance.campaign.day_active(self.date)

    def get_commute_mode_display(self):
        if self.commute_mode.slug == 'no_work' and self.date > util.today():
            return _('Dovolená')
        return str(self.commute_mode)


@receiver(pre_save, sender=Trip)
def trip_pre_save(sender, instance, **kwargs):
    if instance.gpx_file and not instance.track:
        if instance.gpx_file.name.endswith(".gz"):
            track_file = gzip.open(instance.gpx_file)
        else:
            track_file = instance.gpx_file
        try:
            track_file = track_file.read().decode("utf-8")
        except UnicodeDecodeError:
            raise ValidationError({'gpx_file': _('Chyba při načítání GPX souboru. Jste si jistí, že jde o GPX soubor?')})
        instance.track = gpx_parse.parse_gpx(track_file)
    track = instance.track
    if not instance.distance and track:
        instance.distance = round(util.get_multilinestring_length(track), 2)


@receiver(post_save, sender=Trip)
def trip_post_save(sender, instance, **kwargs):
    if instance.user_attendance and not hasattr(instance, "dont_recalculate"):
        from .. import results
        results.recalculate_result_competitor(instance.user_attendance)
