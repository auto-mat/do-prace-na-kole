# Generated by Django 2.0.3 on 2018-08-06 11:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0112_auto_20180806_1057'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaign',
            name='extra_agreement_text',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Další text pro uživatelské souhlas'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='extra_agreement_text_cs',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Další text pro uživatelské souhlas'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='extra_agreement_text_dsnkcs',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Další text pro uživatelské souhlas'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='extra_agreement_text_en',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Další text pro uživatelské souhlas'),
        ),
    ]
