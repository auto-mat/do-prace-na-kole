# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0005_auto_20150109_1317'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trip',
            name='is_working_day',
        ),
        migrations.AddField(
            model_name='trip',
            name='is_working_ride_from',
            field=models.BooleanField(default=False, verbose_name='pracovn\xed cesta z pr\xe1ce'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='trip',
            name='is_working_ride_to',
            field=models.BooleanField(default=False, verbose_name='pracovn\xed cesta do pr\xe1ce'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='payment',
            name='pay_type',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Payment type', choices=[(b'mp', 'mPenize - mBank'), (b'kb', 'MojePlatba'), (b'rf', 'ePlatby pro eKonto'), (b'pg', 'GE Money Bank'), (b'pv', 'Sberbank (Volksbank)'), (b'pf', 'Fio banka'), (b'cs', 'PLATBA 24 \u2013 \u010cesk\xe1 spo\u0159itelna'), (b'era', 'Era - Po\u0161tovn\xed spo\u0159itelna'), (b'cb', '\u010cSOB'), (b'c', 'Credit card via GPE'), (b'bt', 'bank transfer'), (b'pt', 'transfer by post office'), (b'sc', 'superCASH'), (b'psc', 'PaySec'), (b'mo', 'Mobito'), (b't', 'testing payment'), (b'fa', 'invoice outside PayU'), (b'fc', 'company pays by invoice'), (b'am', '\u010dlen Klubu p\u0159\xe1tel Auto*matu'), (b'amw', 'kandid\xe1t na \u010dlenstv\xed v Klubu p\u0159\xe1tel Auto*matu'), (b'fe', 'neplat\xed startovn\xe9')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='language',
            field=models.CharField(default=b'cs', help_text='Jazyk, ve kter\xe9m v\xe1m budou doch\xe1zet emaily z registra\u010dn\xedho syst\xe9mu', max_length=16, verbose_name='Jazyk email\u016f', choices=[(b'cs', 'Czech'), (b'en', 'English')]),
            preserve_default=True,
        ),
    ]
