# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0002_auto_20150106_1045'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='team',
            name='coordinator_campaign',
        ),
    ]
