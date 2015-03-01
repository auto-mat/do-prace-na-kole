# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0013_auto_20150227_0807'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='previous_campaign',
            field=models.ForeignKey(verbose_name='P\u0159edchoz\xed kampa\u0148', blank=True, to='dpnk.Campaign', null=True),
            preserve_default=True,
        ),
    ]
