# Generated by Django 2.2.20 on 2021-05-03 23:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0161_auto_20210202_0133'),
    ]

    operations = [
        migrations.AlterField(
            model_name='competitionresult',
            name='distance',
            field=models.FloatField(blank=True, default=0, null=True, verbose_name='Vzdalenost'),
        ),
    ]
