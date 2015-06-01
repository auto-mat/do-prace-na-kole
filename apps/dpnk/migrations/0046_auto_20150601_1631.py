# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0045_cityincampaign_allow_adding_rides'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='get_rides_count_denorm',
            field=models.IntegerField(null=True, editable=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userattendance',
            name='get_rides_count_denorm',
            field=models.IntegerField(null=True, editable=False),
            preserve_default=True,
        ),
    ]
