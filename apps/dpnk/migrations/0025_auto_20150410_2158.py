# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0024_auto_20150402_1350'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='administrated_cities_tmp',
            field=models.ManyToManyField(related_name='city_admins', null=True, to='dpnk.City', blank=True),
            preserve_default=True,
        ),
    ]
