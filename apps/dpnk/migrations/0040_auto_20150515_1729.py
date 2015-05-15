# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0039_line_to_multiline'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gpxfile',
            name='track',
        ),
        migrations.RenameField(
            model_name='gpxfile',
            old_name='multi_track',
            new_name='track',
        ),
    ]
