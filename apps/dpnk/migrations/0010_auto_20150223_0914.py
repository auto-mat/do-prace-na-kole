# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0009_auto_20150219_2229'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='companyadmin',
            options={'verbose_name': 'Firemn\xed koordin\xe1tor', 'verbose_name_plural': 'Firemn\xed koordin\xe1to\u0159i'},
        ),
        migrations.AddField(
            model_name='userprofile',
            name='nickname',
            field=models.CharField(help_text='Zobraz\xed se ve v\u0161ech ve\u0159ejn\xfdch v\xfdpisech m\xedsto va\u0161eho jm\xe9na. Zad\xe1vejte takov\xe9 jm\xe9no, podle kter\xe9ho v\xe1s va\u0161i kolegov\xe9 poznaj\xed', max_length=60, null=True, verbose_name='Zobrazen\xe9 jm\xe9no', blank=True),
            preserve_default=True,
        ),
    ]
