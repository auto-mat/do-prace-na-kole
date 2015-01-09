# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0004_auto_20150109_1307'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trip',
            name='distance_from',
            field=models.FloatField(default=None, null=True, verbose_name='Distance ridden from work', blank=True, validators=[django.core.validators.MaxValueValidator(1000), django.core.validators.MinValueValidator(0)]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='trip',
            name='distance_to',
            field=models.FloatField(default=None, null=True, verbose_name='Distance ridden to work', blank=True, validators=[django.core.validators.MaxValueValidator(1000), django.core.validators.MinValueValidator(0)]),
            preserve_default=True,
        ),
    ]
