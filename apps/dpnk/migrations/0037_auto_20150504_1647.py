# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0036_voucher'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='voucher',
            options={'verbose_name': 'Voucher', 'verbose_name_plural': 'Vouchery'},
        ),
        migrations.AddField(
            model_name='gpxfile',
            name='from_application',
            field=models.BooleanField(default=False, verbose_name='Nahr\xe1no z aplikace'),
            preserve_default=True,
        ),
    ]
