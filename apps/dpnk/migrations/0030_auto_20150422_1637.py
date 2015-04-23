# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0029_auto_20150421_1349'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaign',
            name='minimum_rides_base',
            field=models.PositiveIntegerField(default=25, help_text='Minimal rides count, with which is possible to reach 100% rides ridden', verbose_name='Minimal rides number base'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='campaign',
            name='package_depth',
            field=models.PositiveIntegerField(default=35, null=True, verbose_name='Package depth', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='campaign',
            name='package_height',
            field=models.PositiveIntegerField(default=1, null=True, verbose_name='Package height', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='campaign',
            name='package_weight',
            field=models.FloatField(default=0.25, null=True, verbose_name='Package weight', blank=True, validators=[django.core.validators.MaxValueValidator(1000), django.core.validators.MinValueValidator(0)]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='campaign',
            name='package_width',
            field=models.PositiveIntegerField(default=26, null=True, verbose_name='Package width', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='company',
            name='active',
            field=models.BooleanField(default=True, verbose_name='Active'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='date_from',
            field=models.DateField(default=None, help_text='The rides are counting from this date', null=True, verbose_name='Competition beginning date'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='date_to',
            field=models.DateField(default=None, help_text='After this date the competition will be closed (or fill questionnaire)', null=True, verbose_name='Competition end date'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gpxfile',
            name='direction',
            field=models.CharField(max_length=50, verbose_name='Trip direction', choices=[(b'trip_to', 'There'), (b'trip_from', 'Back')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gpxfile',
            name='file',
            field=models.FileField(upload_to=b'gpx_tracks', verbose_name='GPX track'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='gpxfile',
            name='trip_date',
            field=models.DateField(verbose_name='Trip date'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='invoice',
            name='company_pais_benefitial_fee',
            field=models.BooleanField(default=False, verbose_name='My company wants to support Auto*mat by beneficiary starting fee (450 K\u010d per person)'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='invoice',
            name='total_amount',
            field=models.FloatField(default=0, verbose_name='Total amount'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='active',
            field=models.BooleanField(default=True, verbose_name='Active'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_dpnk.transaction_set+', editable=False, to='contenttypes.ContentType', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='track',
            field=django.contrib.gis.db.models.fields.LineStringField(srid=4326, blank=True, help_text='\n<ul>\n   <li><strong>Zad\xe1v\xe1n\xed trasy zah\xe1j\xedte kliknut\xedm na tla\u010d\xedtko "Nakreslit trasu".</strong></li>\n   <li>Zm\u011bnu trasy provedete po p\u0159epnut\xed do re\u017eimu \xfaprav kliknut\xedm na trasu.</li>\n   <li>Trasu sta\u010d\xed zadat tak, \u017ee bude z\u0159ejm\xe9, kter\xfdmi ulicemi vede.</li>\n   <li>Zad\xe1n\xed p\u0159esn\u011bj\u0161\xedho pr\u016fb\u011bhu n\xe1m v\u0161ak m\u016f\u017ee pomoci l\xe9pe zjistit jak se lid\xe9 na kole pohybuj\xed.</li>\n   <li>Trasu bude mo\u017en\xe9 zm\u011bnit nebo up\u0159esnit i pozd\u011bji v pr\u016fb\u011bhu sout\u011b\u017ee.</li>\n   <li>Polohu za\u010d\xe1tku a konce trasy sta\u010d\xed zad\xe1vat s p\u0159esnost\xed 100m.</li>\n</ul>\nTrasa slou\u017e\xed k v\xfdpo\u010dtu vzd\xe1lenosti a pom\u016f\u017ee n\xe1m l\xe9pe ur\u010dit pot\u0159eby lid\xed pohybu\xedc\xedch se ve m\u011bst\u011b na kole. Va\u0161e cesta se zobraz\xed va\u0161im t\xfdmov\xfdm koleg\u016fm.\n<br/>Trasy v\u0161ech \xfa\u010dastn\xedk\u016f budou v anonymizovan\xe9 podob\u011b zobrazen\xe9 na \xfavodn\xed str\xe1nce.\n', null=True, verbose_name='track', geography=True),
            preserve_default=True,
        ),
    ]
