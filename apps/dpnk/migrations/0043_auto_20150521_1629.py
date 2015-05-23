# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0042_auto_20150521_1629'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='with_comment',
        ),
    ]
