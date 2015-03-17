# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0017_auto_20150314_0800'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='sequence_number',
            field=models.PositiveIntegerField(verbose_name='Invoice sequence number'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='track',
            field=django.contrib.gis.db.models.fields.LineStringField(srid=4326, blank=True, help_text='\n<ul>\n   <li><strong>Zad\xe1v\xe1n\xed trasy ukon\u010d\xedte dvouklikem.</strong></li>\n   <li>Zad\xe1v\xe1n\xed trasy zah\xe1j\xedte jedn\xedm kliknut\xedm, ta\u017een\xedm posouv\xe1te mapu.</li>\n   <li>Zm\u011bnu trasy provedete po p\u0159epnut\xed do re\u017eimu \xfaprav kliknut\xedm na trasu.</li>\n   <li>Trasu sta\u010d\xed zadat tak, \u017ee bude z\u0159ejm\xe9, kter\xfdmi ulicemi vede.</li>\n   <li>Zad\xe1n\xed p\u0159esn\u011bj\u0161\xedho pr\u016fb\u011bhu n\xe1m v\u0161ak m\u016f\u017ee pomoci l\xe9pe zjistit jak se lid\xe9 na kole pohybuj\xed.</li>\n   <li>Trasu bude mo\u017en\xe9 zm\u011bnit nebo up\u0159esnit i pozd\u011bji v pr\u016fb\u011bhu sout\u011b\u017ee.</li>\n   <li>Polohu za\u010d\xe1tku a konce trasy sta\u010d\xed zad\xe1vat s p\u0159esnost\xed 100m.</li>\n</ul>\nTrasa slou\u017e\xed k v\xfdpo\u010dtu vzd\xe1lenosti a pom\u016f\u017ee n\xe1m l\xe9pe ur\u010dit pot\u0159eby lid\xed pohybu\xedc\xedch se ve m\u011bst\u011b na kole. Va\u0161e cesta se zobraz\xed va\u0161im t\xfdmov\xfdm koleg\u016fm.\n<br/>Trasy v\u0161ech \xfa\u010dastn\xedk\u016f budou v anonymizovan\xe9 podob\u011b zobrazen\xe9 na \xfavodn\xed str\xe1nce.\n', null=True, verbose_name='track', geography=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='invoice',
            unique_together=set([('sequence_number', 'campaign')]),
        ),
    ]
