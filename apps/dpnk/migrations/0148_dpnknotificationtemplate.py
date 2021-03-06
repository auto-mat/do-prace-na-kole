# Generated by Django 2.2.11 on 2020-03-26 20:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0147_auto_20200325_1442'),
    ]

    operations = [
        migrations.CreateModel(
            name='DpnkNotificationTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('verb', models.CharField(max_length=255)),
                ('verb_en', models.CharField(max_length=255, null=True)),
                ('verb_cs', models.CharField(max_length=255, null=True)),
                ('verb_dsnkcs', models.CharField(max_length=255, null=True)),
                ('url', models.CharField(max_length=255)),
                ('icon', models.FileField(max_length=255, upload_to='')),
                ('slug', models.CharField(max_length=60, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
