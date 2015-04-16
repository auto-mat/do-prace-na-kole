# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0026_transform'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='administrated_cities',
        ),
        migrations.RenameField(
            model_name='userprofile',
            old_name='administrated_cities_tmp',
            new_name='administrated_cities',
        ),
    ]
