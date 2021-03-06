# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-21 15:39
from __future__ import unicode_literals

from django.db import migrations, models
import dpnk.models.gpxfile


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0077_auto_20170524_0937'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='answer',
            managers=[
            ],
        ),
        migrations.AddField(
            model_name='invoice',
            name='note',
            field=models.TextField(blank=True, null=True, verbose_name='Interní poznámka'),
        ),
        migrations.AlterField(
            model_name='gpxfile',
            name='file',
            field=models.FileField(blank=True, help_text="Zadat trasu nahráním souboru GPX. Pro vytvoření GPX souboru s trasou můžete použít vyhledávání na naší <a href='https://mapa.prahounakole.cz/#hledani' target='_blank'>mapě</a>.", max_length=512, null=True, upload_to=dpnk.models.gpxfile.normalize_gpx_filename, verbose_name='GPX soubor'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='status',
            field=models.PositiveIntegerField(choices=[(20001, 'Nový'), (20002, 'Přijat k sestavení'), (20003, 'Sestaven'), (20004, 'Odeslán'), (20005, 'Doručení potvrzeno'), (20006, 'Dosud nedoručeno'), (20007, 'Reklamován'), (1, 'Nová'), (2, 'Zrušena'), (7, 'Odmítnuta'), (4, 'Zahájena'), (5, 'Očekává potvrzení'), (7, 'Platba zamítnuta, prostředky nemožno vrátit, řeší PayU'), (99, 'Platba přijata'), (888, 'Nesprávný status -- kontaktovat PayU'), (1005, 'Platba akceptována organizací'), (1008, 'Partner má startovné zdarma'), (1006, 'Faktura vystavena'), (1007, 'Faktura zaplacena'), (40001, 'Oprava v cykloservisu'), (30002, 'Potvrzen vstup do soutěže')], default=0, verbose_name='Status'),
        ),
    ]
