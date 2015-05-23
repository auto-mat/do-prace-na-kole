# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0040_auto_20150515_1729'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='comment_type',
            field=models.CharField(default=None, max_length=16, null=True, verbose_name='Typ koment\xe1\u0159e', choices=[(None, 'Nic'), (b'text', 'Text'), (b'link', 'Odkaz'), (b'one-liner', 'Jeden \u0159\xe1dek textu')]),
            preserve_default=True,
        ),
    ]
