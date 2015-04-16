# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0022_auto_20150331_1132'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='company_pais_benefitial_fee',
            field=models.BooleanField(default=False, verbose_name='Moje firma si p\u0159eje podpo\u0159it Auto*Mat a zaplatit benefi\u010dn\xed startovn\xe9 (450 K\u010d za osobu).'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='invoice',
            name='order_number',
            field=models.BigIntegerField(null=True, verbose_name='Order number (optional)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='payment',
            name='session_id',
            field=models.CharField(null=True, default=None, max_length=50, blank=True, unique=True, verbose_name=b'Session ID'),
            preserve_default=True,
        ),
    ]
