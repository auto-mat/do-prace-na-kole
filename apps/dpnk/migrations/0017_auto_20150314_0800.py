# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0016_auto_20150304_2147'),
    ]

    operations = [
        migrations.AddField(
            model_name='userattendance',
            name='dont_want_insert_track',
            field=models.BooleanField(default=False, verbose_name="I don't want to fill in my track."),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='campaign',
            name='minimum_rides_base',
            field=models.PositiveIntegerField(default=25, help_text='Minim\xe1ln\xed po\u010det j\xedzd, kter\xe9 je nutn\xe9 si zapsat, aby bylo mo\u017en\xe9 dos\xe1hnout 100% j\xedzd', verbose_name='Minimal rides number base'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='company',
            name='address_city',
            field=models.CharField(default=b'', help_text='Nap\u0159. Jablonec n. N. nebo Praha 3-\u017di\u017ekov', max_length=50, verbose_name='Town'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='phase',
            name='type',
            field=models.CharField(default=b'registration', max_length=16, verbose_name='Phase type', choices=[(b'registration', 'registration'), (b'late_admission', 'late registration fee'), (b'compet_entry', 'main competition entry'), (b'competition', 'competition'), (b'results', 'results'), (b'admissions', 'apply for competitions'), (b'invoices', 'vytv\xe1\u0159en\xed faktur')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='address_city',
            field=models.CharField(default=b'', help_text='Nap\u0159. Jablonec n. N. nebo Praha 3-\u017di\u017ekov', max_length=50, verbose_name='Town'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='distance',
            field=models.FloatField(default=None, help_text='Average distance from home to work (in km in one direction)', null=True, verbose_name='Distance', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='track',
            field=django.contrib.gis.db.models.fields.LineStringField(srid=4326, blank=True, help_text='<strong>Zad\xe1v\xe1n\xed trasy ukon\u010d\xedte dvouklikem.</strong><br/><br/>Trasa slou\u017e\xed k v\xfdpo\u010dtu vzd\xe1lenosti a pom\u016f\u017ee n\xe1m l\xe9pe ur\u010dit pot\u0159eby lid\xed pohybu\xedc\xedch se ve m\u011bst\u011b na kole. Va\u0161e cesta se zobraz\xed va\u0161im t\xfdmov\xfdm koleg\u016fm.<br/>Trasy v\u0161ech \xfa\u010dastn\xedk\u016f budou v anonymizovan\xe9 podob\u011b zobrazen\xe9 na \xfavodn\xed str\xe1nce.<br/><br/>Polohu za\u010d\xe1tku a konce trasy sta\u010d\xed zad\xe1vat s p\u0159esnost\xed 100m.', null=True, verbose_name='track', geography=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='sex',
            field=models.CharField(default=b'unknown', help_text='Slou\u017e\xed k za\u0159azen\xed do v\xfdkonnostn\xedch kategori\xed', max_length=50, verbose_name='Gende', choices=[(b'unknown', '-------'), (b'male', 'Male'), (b'female', 'Female')]),
            preserve_default=True,
        ),
    ]
