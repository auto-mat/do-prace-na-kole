# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0027_transform'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='active',
            field=models.BooleanField(default=True, verbose_name='Aktivn\xed'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='subsidiary',
            name='active',
            field=models.BooleanField(default=True, verbose_name='Aktivn\xed'),
            preserve_default=True,
        ),
    ]
