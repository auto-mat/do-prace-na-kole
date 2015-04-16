# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0018_auto_20150316_1546'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAttendanceToBatch',
            fields=[
            ],
            options={
                'verbose_name': 'User for delivery batch',
                'proxy': True,
                'verbose_name_plural': 'Users for delivery batch',
            },
            bases=('dpnk.userattendance',),
        ),
        migrations.AddField(
            model_name='campaign',
            name='package_depth',
            field=models.PositiveIntegerField(default=35, null=True, verbose_name='Hloubka bal\xedku', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='campaign',
            name='package_height',
            field=models.PositiveIntegerField(default=1, null=True, verbose_name='V\xfd\u0161ka bal\xedku', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='campaign',
            name='package_width',
            field=models.PositiveIntegerField(default=26, null=True, verbose_name='\u0160\xed\u0159ka bal\xedku', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='company',
            name='address_city',
            field=models.CharField(default=b'', help_text='For example Jablonec n. N. or Praha 3-\u017di\u017ekov', max_length=50, verbose_name='Town'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='competition',
            name='public_answers',
            field=models.BooleanField(default=False, verbose_name='Public competition answers'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='phase',
            name='type',
            field=models.CharField(default=b'registration', max_length=16, verbose_name='Phase type', choices=[(b'registration', 'registration'), (b'late_admission', 'late registration fee'), (b'compet_entry', 'main competition entry'), (b'competition', 'competition'), (b'results', 'results'), (b'admissions', 'apply for competitions'), (b'invoices', 'invoice creation')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='address_city',
            field=models.CharField(default=b'', help_text='For example Jablonec n. N. or Praha 3-\u017di\u017ekov', max_length=50, verbose_name='Town'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Last change date', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='sex',
            field=models.CharField(default=b'unknown', help_text='For distinguishing in performance categories', max_length=50, verbose_name='Gender', choices=[(b'unknown', '-------'), (b'male', 'Male'), (b'female', 'Female')]),
            preserve_default=True,
        ),
    ]
