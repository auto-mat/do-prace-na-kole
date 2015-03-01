# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0014_campaign_previous_campaign'),
    ]

    operations = [
        migrations.AddField(
            model_name='city',
            name='cyklistesobe_slug',
            field=models.CharField(max_length=40, null=True, verbose_name='Jm\xe9no skupiny na webu Cyklist\xe9 sob\u011b'),
            preserve_default=True,
        ),
    ]
