# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0007_auto_20150212_1526'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cityincampaign',
            name='admission_fee',
        ),
        migrations.RemoveField(
            model_name='cityincampaign',
            name='admission_fee_company',
        ),
        migrations.AddField(
            model_name='campaign',
            name='admission_fee',
            field=models.FloatField(default=0, verbose_name='V\u010dasn\xe9 startovn\xe9'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='campaign',
            name='admission_fee_company',
            field=models.FloatField(default=0, verbose_name='V\u010dasn\xe9 startovn\xe9 pro firmy'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='campaign',
            name='benefitial_admission_fee',
            field=models.FloatField(default=0, verbose_name='Benefi\u010dn\xed startovn\xe9'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='campaign',
            name='late_admission_fee',
            field=models.FloatField(default=0, verbose_name='Pozdn\xed startovn\xe9'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='campaign',
            name='late_admission_fee_company',
            field=models.FloatField(default=0, verbose_name='Pozdn\xed startovn\xe9 pro firmy'),
            preserve_default=True,
        ),
    ]
