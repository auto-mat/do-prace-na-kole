# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0008_auto_20150216_0903'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subsidiary',
            options={'verbose_name': 'Pobo\u010dka firmy', 'verbose_name_plural': 'Pobo\u010dky firem'},
        ),
        migrations.AlterModelOptions(
            name='userattendance',
            options={'verbose_name': '\xda\u010dastn\xedk kampan\u011b', 'verbose_name_plural': '\xda\u010dastn\xedci kampan\u011b'},
        ),
        migrations.AlterField(
            model_name='phase',
            name='type',
            field=models.CharField(default=b'registration', max_length=16, verbose_name='Phase type', choices=[(b'registration', 'registration'), (b'late_admission', 'pozdn\xed startovn\xe9'), (b'compet_entry', 'main competition entry'), (b'competition', 'competition'), (b'results', 'results'), (b'admissions', 'apply for competitions')]),
            preserve_default=True,
        ),
    ]
