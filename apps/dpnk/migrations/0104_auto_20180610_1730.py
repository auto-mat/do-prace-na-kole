# Generated by Django 2.0.3 on 2018-06-10 17:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0103_auto_20180527_1501'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='last_sync_time',
            field=models.DateTimeField(blank=True, default=None, null=True, verbose_name='Poslední synchronizace'),
        ),
    ]