# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0011_campaign_minimum_rides_base'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='minimum_percentage',
            field=models.PositiveIntegerField(default=66, verbose_name='Minim\xe1ln\xed procento pro kvalifikaci do pravidelnostn\xed sout\u011b\u017ee'),
            preserve_default=True,
        ),
    ]
