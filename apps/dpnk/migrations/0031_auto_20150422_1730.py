# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0030_auto_20150422_1637'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='cities',
            field=models.ManyToManyField(help_text='Sout\u011b\u017e bude prob\xedhat ve vybran\xfdch m\u011bstech. Pokud z\u016fstane pr\xe1zdn\xe9, sout\u011b\u017e prob\xedh\xe1 ve v\u0161ech m\u011bstech.', to='dpnk.City', null=True, verbose_name='Sout\u011b\u017e pouze pro m\u011bsta', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='city',
            field=models.ForeignKey(related_name='competitions', verbose_name='Competition is only for selected city', blank=True, to='dpnk.City', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='url',
            field=models.URLField(default=b'', blank=True, help_text='Odkaz na str\xe1nku, kde budou pravidla a podrobn\xe9 informace o sout\u011b\u017ei', null=True, verbose_name='Odkaz na str\xe1nku sout\u011b\u017ee'),
            preserve_default=True,
        ),
    ]
