# Generated by Django 2.2.12 on 2020-05-28 21:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('donation_chooser', '0002_charitativeorganization_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='charitativeorganization',
            options={'ordering': ('order', 'name')},
        ),
    ]
