# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='trip',
            name='is_working_day',
            field=models.BooleanField(default=False, verbose_name='pracovn\xed den'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userattendance',
            name='track',
            field=django.contrib.gis.db.models.fields.LineStringField(srid=4326, null=True, verbose_name='trasa', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='sex',
            field=models.CharField(default=None, choices=[(b'unknown', '-------'), (b'male', 'Mu\u017e'), (b'female', '\u017dena')], max_length=50, blank=True, null=True, verbose_name='Sout\u011b\u017e pouze pro pohlav\xed'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='trip',
            name='trip_from',
            field=models.NullBooleanField(default=None, verbose_name='Trip from work'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='trip',
            name='trip_to',
            field=models.NullBooleanField(default=None, verbose_name='Trip to work'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='sex',
            field=models.CharField(default=b'unknown', max_length=50, verbose_name='Pohlav\xed', choices=[(b'unknown', '-------'), (b'male', 'Mu\u017e'), (b'female', '\u017dena')]),
            preserve_default=True,
        ),
    ]
