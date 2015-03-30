# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0020_campaign_package_weight'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='company_pais_benefitial_fee',
            field=models.BooleanField(default=False, verbose_name='Beneficiary registration fee'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='invoice',
            name='total_amount',
            field=models.FloatField(default=0, verbose_name='Celkov\xe1 \u010d\xe1stka'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='city',
            field=models.ForeignKey(verbose_name='Competing town', to='dpnk.City', help_text="Rozhoduje o tom, kde budete sout\u011b\u017eit - vizte <a href='http://www.dopracenakole.net/pravidla' target='_blank'>pravidla sout\u011b\u017ee</a>"),
            preserve_default=True,
        ),
    ]
