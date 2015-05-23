# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0043_auto_20150521_1629'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='required',
            field=models.BooleanField(default=True, verbose_name='Povinn\xe1 ot\xe1zka'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='question',
            name='comment_type',
            field=models.CharField(default=None, choices=[(None, 'Nic'), (b'text', 'Text'), (b'link', 'Odkaz'), (b'one-liner', 'Jeden \u0159\xe1dek textu')], max_length=16, blank=True, null=True, verbose_name='Typ koment\xe1\u0159e'),
            preserve_default=True,
        ),
    ]
