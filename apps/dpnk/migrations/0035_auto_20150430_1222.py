# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0034_auto_20150427_1352'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='gpxfile',
            options={'ordering': ('trip_date', 'direction'), 'verbose_name': 'GPX soubor', 'verbose_name_plural': 'GPX soubory'},
        ),
        migrations.AlterField(
            model_name='gpxfile',
            name='file',
            field=models.FileField(help_text='Zadat trasu nahr\xe1n\xedm souboru GPX', upload_to=b'gpx_tracks', null=True, verbose_name='GPX soubor', blank=True),
            preserve_default=True,
        ),
    ]
