# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0033_remove_competition_city'),
    ]

    operations = [
        migrations.AddField(
            model_name='gpxfile',
            name='track',
            field=django.contrib.gis.db.models.fields.LineStringField(srid=4326, geography=True, null=True, verbose_name='track', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='competitor_type',
            field=models.CharField(help_text='Ur\u010duje, zdali bude sout\u011b\u017e t\xfdmov\xe1, nebo pro jednotlivce. Ostatn\xed volby vyb\xedrejte jen pokud v\xedte, k \u010demu slou\u017e\xed.', max_length=16, verbose_name='Competitor type', choices=[(b'single_user', 'Individual competitors'), (b'liberos', 'Liberos'), (b'team', 'Teams'), (b'company', 'Company competition')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='date_from',
            field=models.DateField(default=None, help_text='The rides are counting from this date', null=True, verbose_name='Competition beginning date', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='date_to',
            field=models.DateField(default=None, help_text='After this date the competition will be closed (or fill questionnaire)', null=True, verbose_name='Competition end date', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='sex',
            field=models.CharField(default=None, choices=[(b'unknown', '-------'), (b'male', 'Male'), (b'female', 'Female')], max_length=50, blank=True, help_text='Pokud chcete odd\u011blit v\xfdsledky pro mu\u017ee a \u017eeny, je pot\u0159eba vypsat dv\u011b sout\u011b\u017ee - jednu pro mu\u017ee a druhou pro \u017eeny. Jinak nechte pr\xe1zdn\xe9.', null=True, verbose_name='Competition is only for selected gender'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='type',
            field=models.CharField(help_text='Ur\u010duje, zdali bude sout\u011b\u017e v\xfdkonnostn\xed (na ujetou vzd\xe1lenost), nebo na pravidelnost. Volba "Dotazn\xedk" slou\u017e\xed pro kreativn\xed sout\u011b\u017ee, cyklozam\u011bstnavatele roku a dal\u0161\xed dotazn\xedky; je nutn\xe9 definovat ot\xe1zky.', max_length=16, verbose_name='Type', choices=[(b'length', 'Distance ridden'), (b'frequency', 'Bike rides regularity'), (b'questionnaire', 'Questionnaire')]),
            preserve_default=True,
        ),
    ]
