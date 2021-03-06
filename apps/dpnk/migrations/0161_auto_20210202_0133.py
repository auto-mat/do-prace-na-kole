# Generated by Django 2.2.17 on 2021-02-02 01:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0160_auto_20210117_2211'),
    ]

    operations = [
        migrations.AddField(
            model_name='competitionresult',
            name='distance',
            field=models.FloatField(blank=True, default=0, null=True, verbose_name='Počet ekologických cest'),
        ),
        migrations.AddField(
            model_name='competitionresult',
            name='frequency',
            field=models.FloatField(blank=True, default=0, null=True, verbose_name='Pravidelnost'),
        ),
    ]
