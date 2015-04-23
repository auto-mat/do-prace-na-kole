# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0032_auto_20150422_1731'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='competition',
            name='city',
        ),
        migrations.RenameField(
            model_name='competition',
            old_name='cities',
            new_name='city',
        ),
    ]
