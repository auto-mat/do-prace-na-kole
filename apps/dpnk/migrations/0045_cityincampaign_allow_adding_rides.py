# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0044_auto_20150521_1822'),
    ]

    operations = [
        migrations.AddField(
            model_name='cityincampaign',
            name='allow_adding_rides',
            field=models.BooleanField(default=True, verbose_name='povolit zapisov\xe1n\xed j\xedzd'),
            preserve_default=True,
        ),
    ]
