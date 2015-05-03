# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0035_auto_20150430_1222'),
    ]

    operations = [
        migrations.CreateModel(
            name='Voucher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(default=b'rekola', max_length=10, verbose_name='typ voucheru', choices=[(b'rekola', 'ReKola')])),
                ('token', models.TextField(null=True, verbose_name='token')),
                ('user_attendance', models.ForeignKey(blank=True, to='dpnk.UserAttendance', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
