# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import dpnk.models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0037_auto_20150504_1647'),
    ]

    operations = [
        migrations.AddField(
            model_name='gpxfile',
            name='multi_track',
            field=django.contrib.gis.db.models.fields.MultiLineStringField(srid=4326, geography=True, null=True, verbose_name='track', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gpxfile',
            name='file',
            field=models.FileField(help_text='Zadat trasu nahr\xe1n\xedm souboru GPX', upload_to=dpnk.models.normalize_gpx_filename, null=True, verbose_name='GPX soubor', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='phase',
            name='type',
            field=models.CharField(default=b'registration', max_length=16, verbose_name='Phase type', choices=[(b'registration', 'registration'), (b'late_admission', 'late registration fee'), (b'compet_entry', 'vstup do sout\u011b\u017ee (zastaral\xe9)'), (b'payment', 'placen\xed startovn\xe9ho'), (b'competition', 'competition'), (b'results', 'results'), (b'admissions', 'apply for competitions'), (b'invoices', 'invoice creation')]),
            preserve_default=True,
        ),
    ]
