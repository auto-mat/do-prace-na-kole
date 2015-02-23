# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0010_auto_20150223_0914'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='minimum_rides_base',
            field=models.PositiveIntegerField(default=25, verbose_name='Minim\xe1ln\xed z\xe1klad po\u010dtu j\xedzd'),
            preserve_default=True,
        ),
    ]
