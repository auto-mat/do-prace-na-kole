# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0012_campaign_minimum_percentage'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='free_entry_cases_html',
            field=models.TextField(null=True, verbose_name='P\u0159\xedpady, kdy je startovn\xe9 zdarma', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='distance',
            field=models.FloatField(default=None, help_text='Average distance from home to work (in km in one direction)', null=True, verbose_name='Distance'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='track',
            field=django.contrib.gis.db.models.fields.LineStringField(srid=4326, blank=True, help_text='Zad\xe1v\xe1n\xed trasy ukon\u010d\xedte dvouklikem.<br/><br/>Trasa slou\u017e\xed k v\xfdpo\u010dtu vzd\xe1lenosti a pom\u016f\u017ee n\xe1m l\xe9pe ur\u010dit pot\u0159eby cyklist\u016f pohybu\xedc\xedch se ve m\u011bst\u011b. Va\u0161e cesta se zobraz\xed va\u0161im t\xfdmov\xfdm koleg\u016fm.<br/>Trasy v\u0161ech \xfa\u010dastn\xedk\u016f budou v anonymizovan\xe9 podob\u011b zobrazen\xe9 na \xfavodn\xed str\xe1nce.<br/><br/>Polohu za\u010d\xe1tku a konce trasy sta\u010d\xed zad\xe1vat s p\u0159esnost\xed 100m.', null=True, verbose_name='trasa', geography=True),
            preserve_default=True,
        ),
    ]
