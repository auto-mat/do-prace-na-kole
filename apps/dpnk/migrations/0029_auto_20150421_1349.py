# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0028_auto_20150421_1141'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='address_psc',
            field=models.IntegerField(default=None, help_text='For example 130 00', null=True, verbose_name='ZIP code (PS\u010c)', validators=[django.core.validators.MaxValueValidator(99999), django.core.validators.MinValueValidator(10000)]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='address_psc',
            field=models.IntegerField(default=None, help_text='For example 130 00', null=True, verbose_name='ZIP code (PS\u010c)', validators=[django.core.validators.MaxValueValidator(99999), django.core.validators.MinValueValidator(10000)]),
            preserve_default=True,
        ),
    ]
