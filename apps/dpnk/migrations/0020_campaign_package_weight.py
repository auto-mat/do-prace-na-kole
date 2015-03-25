# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0019_auto_20150325_1450'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='package_weight',
            field=models.FloatField(default=0.25, null=True, verbose_name='V\xe1ha bal\xedku', blank=True, validators=[django.core.validators.MaxValueValidator(1000), django.core.validators.MinValueValidator(0)]),
            preserve_default=True,
        ),
    ]
