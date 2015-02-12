# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0006_auto_20150126_1732'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userattendance',
            name='distance',
            field=models.FloatField(default=None, help_text='Average distance from home to work (in km in one direction)', null=True, verbose_name='Distance', blank=True),
            preserve_default=True,
        ),
    ]
