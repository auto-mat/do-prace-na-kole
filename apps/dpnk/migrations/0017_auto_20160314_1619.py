# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-14 16:19
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0016_auto_20160305_1744'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='company',
            options={'ordering': ('name',), 'verbose_name': 'Organizace', 'verbose_name_plural': 'Organizace'},
        ),
        migrations.AlterModelOptions(
            name='companyadmin',
            options={'verbose_name': 'Koordinátor organizace', 'verbose_name_plural': 'Koordinátoři organizací'},
        ),
        migrations.AlterModelOptions(
            name='subsidiary',
            options={'verbose_name': 'Pobočka organizace', 'verbose_name_plural': 'Pobočky organizací'},
        ),
        migrations.AlterField(
            model_name='campaign',
            name='admission_fee_company',
            field=models.FloatField(default=0, verbose_name='Včasné startovné pro organizace'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='benefitial_admission_fee_company',
            field=models.FloatField(default=0, verbose_name='Benefiční startovné pro organizace'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='late_admission_fee_company',
            field=models.FloatField(default=0, verbose_name='Pozdní startovné pro organizace'),
        ),
        migrations.AlterField(
            model_name='choice',
            name='choice_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dpnk.ChoiceType', verbose_name='Typ volby'),
        ),
        migrations.AlterField(
            model_name='company',
            name='address_recipient',
            field=models.CharField(blank=True, default='', help_text='Např. „odštěpný závod Brno“, „oblastní pobočka Liberec“, „Přírodovědecká fakulta“ atp.', max_length=50, null=True, verbose_name='Název pobočky (celé organizace, závodu, kanceláře, fakulty) na adrese'),
        ),
        migrations.AlterField(
            model_name='company',
            name='name',
            field=models.CharField(help_text='Např. „Výrobna, a.s.“, „Příspěvková, p.o.“, „Nevládka, z.s.“, „Univerzita Karlova“', max_length=60, unique=True, verbose_name='Název organizace'),
        ),
        migrations.AlterField(
            model_name='companyadmin',
            name='administrated_company',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='company_admin', to='dpnk.Company', verbose_name='Koordinovaná organizace'),
        ),
        migrations.AlterField(
            model_name='companyadmin',
            name='will_pay_opt_in',
            field=models.BooleanField(default=False, verbose_name='Uživatel potvrdil, že bude plati za zaměstnance.'),
        ),
        migrations.AlterField(
            model_name='competition',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='dpnk.Company', verbose_name='Soutěž pouze pro organizace'),
        ),
        migrations.AlterField(
            model_name='competition',
            name='company_competitors',
            field=models.ManyToManyField(blank=True, related_name='competitions', to='dpnk.Company', verbose_name='Přihlášené soutěžící organizace'),
        ),
        migrations.AlterField(
            model_name='competition',
            name='competitor_type',
            field=models.CharField(choices=[('single_user', 'Jednotliví soutěžící'), ('liberos', 'Liberos'), ('team', 'Týmy'), ('company', 'Soutěž organizací')], help_text='Určuje, zdali bude soutěž týmová, nebo pro jednotlivce. Ostatní volby vybírejte jen pokud víte, k čemu slouží.', max_length=16, verbose_name='Typ soutěžícího'),
        ),
        migrations.AlterField(
            model_name='deliverybatch',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deliverybatch_create', to=settings.AUTH_USER_MODEL, verbose_name='author'),
        ),
        migrations.AlterField(
            model_name='deliverybatch',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deliverybatch_update', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
        migrations.AlterField(
            model_name='gpxfile',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='gpxfile_create', to=settings.AUTH_USER_MODEL, verbose_name='author'),
        ),
        migrations.AlterField(
            model_name='gpxfile',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='gpxfile_update', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoice_create', to=settings.AUTH_USER_MODEL, verbose_name='author'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dpnk.Company', verbose_name='Organizace'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='company_pais_benefitial_fee',
            field=models.BooleanField(default=False, verbose_name='Moje organizace si přeje podpořit Auto*Mat a zaplatit benefiční startovné.'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoice_update', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='pay_type',
            field=models.CharField(blank=True, choices=[('mp', 'mPenize - mBank'), ('kb', 'MojePlatba'), ('rf', 'ePlatby pro eKonto'), ('pg', 'GE Money Bank'), ('pv', 'Sberbank (Volksbank)'), ('pf', 'Fio banka'), ('cs', 'PLATBA 24 – Česká spořitelna'), ('era', 'Era - Poštovní spořitelna'), ('cb', 'ČSOB'), ('c', 'Kreditní karta přes GPE'), ('bt', 'bankovní převod'), ('pt', 'převod přes poštu'), ('sc', 'superCASH'), ('psc', 'PaySec'), ('mo', 'Mobito'), ('t', 'testovací platba'), ('fa', 'faktura mimo PayU'), ('fc', 'organizace platí fakturou'), ('am', 'člen Klubu přátel Auto*Matu'), ('amw', 'kandidát na členství v Klubu přátel Auto*Matu'), ('fe', 'neplatí startovné')], max_length=50, null=True, verbose_name='Typ platby'),
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='address_recipient',
            field=models.CharField(blank=True, default='', help_text='Např. „odštěpný závod Brno“, „oblastní pobočka Liberec“, „Přírodovědecká fakulta“ atp.', max_length=50, null=True, verbose_name='Název pobočky (celé organizace, závodu, kanceláře, fakulty) na adrese'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transaction_create', to=settings.AUTH_USER_MODEL, verbose_name='author'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='status',
            field=models.PositiveIntegerField(choices=[(1, 'Nová'), (2, 'Zrušena'), (7, 'Odmítnuta'), (4, 'Zahájena'), (5, 'Očekává potvrzení'), (7, 'Platba zamítnuta, prostředky nemožno vrátit, řeší PayU'), (99, 'Platba přijata'), (888, 'Nesprávný status -- kontaktovat PayU'), (1005, 'Platba akceptována organizací'), (1006, 'Faktura vystavena'), (1007, 'Faktura zaplacena'), (20001, 'Nový'), (20002, 'Přijat k sestavení'), (20003, 'Sestaven'), (20004, 'Odeslán'), (20005, 'Doručení potvrzeno'), (20006, 'Dosud nedoručeno'), (20007, 'Reklamován'), (40001, 'Oprava v cykloservisu'), (30002, 'Potvrzen vstup do soutěže')], default=0, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transaction_update', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='track',
            field=django.contrib.gis.db.models.fields.MultiLineStringField(blank=True, geography=True, help_text='\n<ul>\n   <li><strong>Zadávání trasy zahájíte kliknutím na tlačítko "Nakreslit trasu", ukončíte kliknutím na cílový bod.</strong></li>\n   <li>Změnu trasy provedete po přepnutí do režimu úprav kliknutím na trasu.</li>\n   <li>Trasu stačí zadat tak, že bude zřejmé, kterými ulicemi vede.</li>\n   <li>Zadání přesnějšího průběhu nám však může pomoci lépe zjistit jak se lidé na kole pohybují.</li>\n   <li>Trasu bude možné změnit nebo upřesnit i později v průběhu soutěže.</li>\n   <li>Polohu začátku a konce trasy stačí zadávat s přesností 100m.</li>\n</ul>\nTrasa slouží k výpočtu vzdálenosti a pomůže nám lépe určit potřeby lidí pohybuících se ve městě na kole. Vaše cesta se zobrazí vašim týmovým kolegům.\n<br/>Trasy všech účastníků budou v anonymizované podobě zobrazené na úvodní stránce.\n', null=True, srid=4326, verbose_name='trasa'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='language',
            field=models.CharField(choices=[('cs', 'Čeština'), ('en', 'Angličtna')], default='cs', help_text='Jazyk, ve kterém vám budou docházet emaily z registračního systému', max_length=16, verbose_name='Jazyk emailové komunikace'),
        ),
        migrations.AlterUniqueTogether(
            name='companyadmin',
            unique_together=set([('user', 'campaign')]),
        ),
    ]
