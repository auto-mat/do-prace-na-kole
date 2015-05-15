# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.contrib.gis.geos import MultiLineString

def change_line_to_multiline(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    GpxFile  = apps.get_model("dpnk", "GpxFile")
    for track in GpxFile.objects.all():
        if track.track:
            track.multi_track = MultiLineString([track.track, ])
            track.save()

class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0038_auto_20150515_1659'),
    ]

    operations = [
        migrations.RunPython(change_line_to_multiline),
    ]
