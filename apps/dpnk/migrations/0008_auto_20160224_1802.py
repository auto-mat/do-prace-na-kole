# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-24 18:02
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0007_auto_20160219_1120'),
    ]

    operations = [
        migrations.AddField(
            model_name='trip',
            name='commute_mode',
            field=models.CharField(blank=True, choices=[('bicycle', 'Na kole'), ('by_foot', 'Pěšky/běh'), ('no_work', 'Nepracoval'), ('by_other_vehicle', 'Jiný dopravní prostředek')], default=None, max_length=20, null=True, verbose_name='Mód dopravy'),
        ),
        migrations.AddField(
            model_name='trip',
            name='direction',
            field=models.CharField(blank=True, choices=[('trip_to', 'Tam'), ('trip_from', 'Zpět')], max_length=20, null=True, verbose_name='Směr cesty'),
        ),
        migrations.AlterUniqueTogether(
            name='trip',
            unique_together=set([('user_attendance', 'date', 'direction')]),
        ),
        migrations.AddField(
            model_name='trip',
            name='distance',
            field=models.FloatField(blank=True, default=None, null=True, validators=[django.core.validators.MaxValueValidator(1000), django.core.validators.MinValueValidator(0)], verbose_name='Ujetá vzdálenost'),
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='t_shirt_size',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='dpnk.TShirtSize', verbose_name='Velikost trička'),
        ),
    ]
