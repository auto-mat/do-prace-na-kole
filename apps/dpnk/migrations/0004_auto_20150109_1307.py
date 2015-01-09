# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0003_remove_team_coordinator_campaign'),
    ]

    operations = [
        migrations.AddField(
            model_name='city',
            name='location',
            field=django.contrib.gis.db.models.fields.PointField(srid=4326, null=True, verbose_name='poloha m\u011bsta'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='track',
            field=django.contrib.gis.db.models.fields.LineStringField(srid=4326, geography=True, null=True, verbose_name='trasa', blank=True),
            preserve_default=True,
        ),
    ]
