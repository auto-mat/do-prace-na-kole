# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-03-23 16:21
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0053_auto_20170319_1017'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='company_address_city',
            field=models.CharField(blank=True, default='', help_text='Např. „Jablonec n. N.“ nebo „Praha 3, Žižkov“', max_length=50, null=True, verbose_name='Město'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='company_address_district',
            field=models.CharField(blank=True, default='', max_length=50, null=True, verbose_name='Městská část'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='company_address_psc',
            field=models.IntegerField(blank=True, default=None, help_text='Např.: „130 00“', null=True, validators=[django.core.validators.MaxValueValidator(99999), django.core.validators.MinValueValidator(10000)], verbose_name='PSČ'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='company_address_recipient',
            field=models.CharField(blank=True, default='', help_text='Např. „odštěpný závod Brno“, „oblastní pobočka Liberec“, „Přírodovědecká fakulta“ atp. Nemá-li vaše organizace pobočky, pak nechte pole prázdné.', max_length=50, null=True, verbose_name='Název pobočky (závodu, kanceláře, fakulty), nepovinné pole'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='company_address_street',
            field=models.CharField(blank=True, default='', help_text='Např. „Šeříková“ nebo „Nám. W. Churchilla“', max_length=50, null=True, verbose_name='Ulice'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='company_address_street_number',
            field=models.CharField(blank=True, default='', help_text='Např. „2965/12“ nebo „156“', max_length=10, null=True, verbose_name='Číslo domu'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='company_dic',
            field=models.CharField(blank=True, default='', max_length=15, null=True, verbose_name='DIČ organizace'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='company_ico',
            field=models.PositiveIntegerField(blank=True, default=None, null=True, verbose_name='IČO organizace'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='company_name',
            field=models.CharField(blank=True, help_text='Název organizace. Pokud je prázdné, vyplní se všechny údaje podle nastavené organizace.', max_length=60, null=True, verbose_name='Název organizace'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='payback_date',
            field=models.DateField(blank=True, null=True, verbose_name='Datum splatnosti'),
        ),
        migrations.AlterField(
            model_name='companyadmin',
            name='can_confirm_payments',
            field=models.BooleanField(default=True, verbose_name='Může potvrzovat platby'),
        ),
        migrations.AlterField(
            model_name='companyadmin',
            name='company_admin_approved',
            field=models.CharField(choices=[('approved', 'Odsouhlasený'), ('undecided', 'Nerozhodnuto'), ('denied', 'Zamítnutý')], default='approved', max_length=16, verbose_name='Schválena funkce firemního koordinátora'),
        ),
        migrations.AlterField(
            model_name='competition',
            name='sex',
            field=models.CharField(blank=True, choices=[('male', 'Muž'), ('female', 'Žena')], default=None, help_text='Pokud chcete oddělit výsledky pro muže a ženy, je potřeba vypsat dvě soutěže - jednu pro muže a druhou pro ženy. Jinak nechte prázdné.', max_length=50, null=True, verbose_name='Soutěž pouze pro pohlaví'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='exposure_date',
            field=models.DateField(blank=True, null=True, verbose_name='Den vystavení daňového dokladu'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='taxable_date',
            field=models.DateField(blank=True, null=True, verbose_name='Den uskutečnění zdanitelného plnění'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='sex',
            field=models.CharField(choices=[('unknown', '---------'), ('male', 'Muž'), ('female', 'Žena')], default='unknown', help_text='Slouží k zařazení do výkonnostních kategorií', max_length=50, verbose_name='Pohlaví'),
        ),
    ]
