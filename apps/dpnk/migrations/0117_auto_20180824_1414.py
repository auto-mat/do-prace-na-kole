# Generated by Django 2.0.6 on 2018-08-24 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0116_auto_20180814_1808'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaign',
            name='mailing_list_enabled',
            field=models.NullBooleanField(default=False, verbose_name='Povolit mailing list'),
        ),
    ]
