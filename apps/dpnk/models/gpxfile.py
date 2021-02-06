# -*- coding: utf-8 -*-

###################################
#
# DEPRECATED!
#
#
###################################

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

from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Length
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from django_gpxpy import gpx_parse

from .commute_mode import CommuteMode
from .trip import Trip
from .user_attendance import UserAttendance
from .util import MAP_DESCRIPTION


def normalize_gpx_filename(instance, filename):
    return "-".join(
        [
            "gpx_tracks/dpnk-%s/track" % instance.user_attendance.campaign.pk,
            datetime.datetime.now().strftime("%Y-%m-%d"),
            slugify(filename),
        ]
    )


@with_author
class GpxFile(models.Model):
    file = models.FileField(
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
    DIRECTIONS = [
        ("trip_to", _(u"Tam")),
        ("trip_from", _(u"Zpět")),
    ]
    DIRECTIONS_DICT = dict(DIRECTIONS)
    trip_date = models.DateField(
        verbose_name=_(u"Datum vykonání cesty"), null=False, blank=False,
    )
    direction = models.CharField(
        verbose_name=_(u"Směr cesty"),
        choices=DIRECTIONS,
        max_length=50,
        null=False,
        blank=False,
    )
    trip = models.OneToOneField(Trip, null=True, blank=True, on_delete=models.CASCADE,)
    track = models.MultiLineStringField(
        verbose_name=_(u"trasa"),
        help_text=MAP_DESCRIPTION,
        srid=4326,
        null=True,
        blank=True,
        geography=True,
    )
    distance = models.PositiveIntegerField(
        verbose_name=_("Vzdálenost v metrech"), null=True, blank=True,
    )
    duration = models.PositiveIntegerField(
        verbose_name=_("Doba v sekundách"), null=True, blank=True,
    )
    source_application = models.CharField(
        verbose_name=_("Zdrojová aplikace"), max_length=255, null=True, blank=True,
    )
    user_attendance = models.ForeignKey(
        UserAttendance, null=False, blank=False, on_delete=models.CASCADE,
    )
    commute_mode = models.ForeignKey(
        "CommuteMode",
        verbose_name=_("Mód dopravy"),
        on_delete=models.CASCADE,
        default=1,
        null=False,
        blank=False,
    )
    from_application = models.BooleanField(
        verbose_name=_(u"Nahráno z aplikace"), default=False, null=False,
    )
    created = models.DateTimeField(
        verbose_name=_(u"Datum vytvoření"), auto_now_add=True, null=True,
    )
    updated = models.DateTimeField(
        verbose_name=_(u"Datum poslední změny"), auto_now=True, null=True,
    )
    ecc_last_upload = models.DateTimeField(
        verbose_name=_(u"Datum posledního nahrátí do ECC"), null=True, blank=True,
    )

    class Meta:
        verbose_name = _(u"GPX soubor")
        verbose_name_plural = _(u"GPX soubory")
        unique_together = (
            ("user_attendance", "trip_date", "direction"),
            ("trip", "direction"),
        )
        ordering = ("trip_date", "direction")

    def length(self):
        length = GpxFile.objects.annotate(length=Length("track")).get(pk=self.pk).length
        if length:
            return round(length.km, 2)

    def clean(self):
        if self.file:
            if self.file.name.endswith(".gz"):
                track_file = gzip.open(self.file)
            else:
                track_file = self.file
            try:
                track_file = track_file.read().decode("utf-8")
            except UnicodeDecodeError:
                raise ValidationError(
                    {
                        "file": _(
                            "Chyba při načítání GPX souboru. Jste si jistí, že jde o GPX soubor?"
                        )
                    }
                )
            self.track_clean = gpx_parse.parse_gpx(track_file)


@receiver(pre_save, sender=GpxFile)
def set_trip(sender, instance, *args, **kwargs):
    by_other_vehicle = CommuteMode.objects.get(slug="by_other_vehicle")
    if not instance.trip:
        trip, created = Trip.objects.get_or_create(
            user_attendance=instance.user_attendance,
            date=instance.trip_date,
            direction=instance.direction,
            defaults={
                "commute_mode": instance.commute_mode
                if instance.user_attendance.campaign.day_active(instance.trip_date)
                else by_other_vehicle,
            },
        )
        instance.trip = trip


@receiver(post_save, sender=GpxFile)
def set_trip_post(sender, instance, *args, **kwargs):
    if instance.trip and instance.trip.active():
        length = instance.distance / 1000.0 if instance.distance else instance.length()
        if length:
            instance.trip.distance = length
            instance.trip.save()
