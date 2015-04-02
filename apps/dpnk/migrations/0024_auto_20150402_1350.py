# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0023_auto_20150331_1137'),
    ]

    operations = [
        migrations.CreateModel(
            name='GpxFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(upload_to=b'gpx_tracks', verbose_name='GPX trasa')),
                ('trip_date', models.DateField(verbose_name='Datum vykon\xe1n\xed cesty')),
                ('direction', models.CharField(max_length=50, verbose_name='Sm\u011br cesty', choices=[(b'trip_to', 'There'), (b'trip_from', 'Back')])),
                ('trip', models.ForeignKey(blank=True, to='dpnk.Trip', null=True)),
                ('user_attendance', models.ForeignKey(to='dpnk.UserAttendance')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='gpxfile',
            unique_together=set([('trip', 'direction'), ('user_attendance', 'trip_date', 'direction')]),
        ),
    ]
