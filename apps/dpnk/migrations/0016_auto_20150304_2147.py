# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0015_city_cyklistesobe_slug'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='companyadmin',
            options={'verbose_name': 'Company coordinator', 'verbose_name_plural': 'Company coordinators'},
        ),
        migrations.AlterModelOptions(
            name='subsidiary',
            options={'verbose_name': 'Subdivision', 'verbose_name_plural': 'Subdivisions'},
        ),
        migrations.AlterModelOptions(
            name='userattendance',
            options={'verbose_name': 'Campaign attendee', 'verbose_name_plural': 'Campaign attendees'},
        ),
        migrations.AlterModelOptions(
            name='userprofile',
            options={'ordering': ['user__last_name', 'user__first_name'], 'verbose_name': 'User profile', 'verbose_name_plural': 'User profiles'},
        ),
        migrations.AddField(
            model_name='userattendance',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userattendance',
            name='updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datum posledn\xed zm\u011bny', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='campaign',
            name='admission_fee',
            field=models.FloatField(default=0, verbose_name='Early registration fee'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='campaign',
            name='admission_fee_company',
            field=models.FloatField(default=0, verbose_name='Early registration fee for companies'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='campaign',
            name='benefitial_admission_fee',
            field=models.FloatField(default=0, verbose_name='Beneficiary registration fee'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='campaign',
            name='free_entry_cases_html',
            field=models.TextField(null=True, verbose_name='Free registration cases', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='campaign',
            name='late_admission_fee',
            field=models.FloatField(default=0, verbose_name='Late starting fee'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='campaign',
            name='late_admission_fee_company',
            field=models.FloatField(default=0, verbose_name='Late registration fee for companies'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='campaign',
            name='minimum_percentage',
            field=models.PositiveIntegerField(default=66, verbose_name='Minimal percentage for competition qualification'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='campaign',
            name='minimum_rides_base',
            field=models.PositiveIntegerField(default=25, verbose_name='Minimal rides number base'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='campaign',
            name='previous_campaign',
            field=models.ForeignKey(verbose_name='Previous campaign', blank=True, to='dpnk.Campaign', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='campaign',
            name='trip_plus_distance',
            field=models.PositiveIntegerField(default=5, help_text='How much can competitor increase his/her ride against ordinary distance (in km)', null=True, verbose_name='Maximal distance increase', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='city',
            name='cyklistesobe_slug',
            field=models.CharField(max_length=40, null=True, verbose_name='Name of group on Cyklist\xe9 sob\u011b website'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='city',
            name='location',
            field=django.contrib.gis.db.models.fields.PointField(srid=4326, null=True, verbose_name='city position'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='city',
            field=models.ForeignKey(verbose_name='Competition is only for selected city', blank=True, to='dpnk.City', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='company',
            field=models.ForeignKey(verbose_name='Competition is only for selected company', blank=True, to='dpnk.Company', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='sex',
            field=models.CharField(default=None, choices=[(b'unknown', '-------'), (b'male', 'Male'), (b'female', 'Female')], max_length=50, blank=True, null=True, verbose_name='Competition is only for selected gender'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='without_admission',
            field=models.BooleanField(default=True, help_text='Questionnaire is usually with admission, frequency and regularity without admission.', verbose_name='Competition is without admission'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='payment',
            name='pay_type',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Payment type', choices=[(b'mp', 'mPenize - mBank'), (b'kb', 'MojePlatba'), (b'rf', 'ePlatby pro eKonto'), (b'pg', 'GE Money Bank'), (b'pv', 'Sberbank (Volksbank)'), (b'pf', 'Fio banka'), (b'cs', 'PLATBA 24 \u2013 \u010cesk\xe1 spo\u0159itelna'), (b'era', 'Era - Po\u0161tovn\xed spo\u0159itelna'), (b'cb', '\u010cSOB'), (b'c', 'Credit card via GPE'), (b'bt', 'bank transfer'), (b'pt', 'transfer by post office'), (b'sc', 'superCASH'), (b'psc', 'PaySec'), (b'mo', 'Mobito'), (b't', 'testing payment'), (b'fa', 'invoice outside PayU'), (b'fc', 'company pays by invoice'), (b'am', 'Auto*Mat Friends Club member'), (b'amw', 'Auto*Mat Friends Club member wannabe'), (b'fe', 'pay no registration fee')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='phase',
            name='type',
            field=models.CharField(default=b'registration', max_length=16, verbose_name='Phase type', choices=[(b'registration', 'registration'), (b'late_admission', 'late registration fee'), (b'compet_entry', 'main competition entry'), (b'competition', 'competition'), (b'results', 'results'), (b'admissions', 'apply for competitions')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='trip',
            name='is_working_ride_from',
            field=models.BooleanField(default=False, verbose_name='working trip from work'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='trip',
            name='is_working_ride_to',
            field=models.BooleanField(default=False, verbose_name='working trip to work'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='track',
            field=django.contrib.gis.db.models.fields.LineStringField(srid=4326, blank=True, help_text='Finnish your track with doubleclick<br/><br/>Track is used to count distance and helps us to better define cyclists needs for motion in the city. Your track will be displayed to your colleagues.<br/>Tracks of all atendees will be displayed anonymously on front page.<br/><br/>It is enough to fill in the location of start and end of track with 100m accuracy.', null=True, verbose_name='track', geography=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='language',
            field=models.CharField(default=b'cs', help_text='Language, in whitch will be delivered emails from registration system', max_length=16, verbose_name='Email language', choices=[(b'cs', 'Czech'), (b'en', 'English')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='nickname',
            field=models.CharField(help_text='Will be displayed instead of your name in all public outputs. Fill in such name, that your coleauges know that it is You.', max_length=60, null=True, verbose_name='Displayed name', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='sex',
            field=models.CharField(default=b'unknown', help_text='Slou\u017e\xed k za\u0159azen\xed do v\xfdkonnostn\xedch sout\u011b\u017e\xed', max_length=50, verbose_name='Gende', choices=[(b'unknown', '-------'), (b'male', 'Male'), (b'female', 'Female')]),
            preserve_default=True,
        ),
    ]
