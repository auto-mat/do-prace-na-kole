# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import dpnk.models


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0047_auto_20151111_1234'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='mailing_opt_in',
            field=models.BooleanField(help_text='Odběr emailů můžete kdykoliv v průběhu soutěže zrušit.', verbose_name='Přeji si dostávat emailem informace o akcích, událostech a dalších informacích souvisejících se soutěží.', default=False),
        ),
        migrations.AlterField(
            model_name='answer',
            name='attachment',
            field=models.FileField(upload_to='questionaire/', max_length=600, blank=True),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='email_footer',
            field=models.TextField(null=True, max_length=5000, verbose_name='Patička uživatelských emailů', default='', blank=True),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='mailing_list_id',
            field=models.CharField(max_length=60, verbose_name='ID mailing listu', default='', blank=True),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='slug',
            field=models.SlugField(default='', verbose_name='Doména v URL', unique=True),
        ),
        migrations.AlterField(
            model_name='company',
            name='address_city',
            field=models.CharField(max_length=50, help_text='Např. Jablonec n. N. nebo Praha 3-Žižkov', verbose_name='Město', default=''),
        ),
        migrations.AlterField(
            model_name='company',
            name='address_district',
            field=models.CharField(null=True, max_length=50, verbose_name='Městská část', default='', blank=True),
        ),
        migrations.AlterField(
            model_name='company',
            name='address_recipient',
            field=models.CharField(null=True, help_text='Např. odštěpný závod Brno, oblastní pobočka Liberec, Přírodovědecká fakulta atp.', max_length=50, verbose_name='Název společnosti (pobočky, závodu, kanceláře, fakulty) na adrese', default='', blank=True),
        ),
        migrations.AlterField(
            model_name='company',
            name='address_street',
            field=models.CharField(max_length=50, help_text='Např. Šeříková nebo Nám. W. Churchilla', verbose_name='Ulice', default=''),
        ),
        migrations.AlterField(
            model_name='company',
            name='address_street_number',
            field=models.CharField(max_length=10, help_text='Např. 2965/12 nebo 156', verbose_name='Číslo domu', default=''),
        ),
        migrations.AlterField(
            model_name='company',
            name='dic',
            field=models.CharField(null=True, max_length=10, verbose_name='DIČ', default='', blank=True),
        ),
        migrations.AlterField(
            model_name='companyadmin',
            name='company_admin_approved',
            field=models.CharField(choices=[('approved', 'Odsouhlasený'), ('undecided', 'Nerozhodnuto'), ('denied', 'Zamítnutý')], max_length=16, verbose_name='Správcovství organizace schváleno', default='undecided'),
        ),
        migrations.AlterField(
            model_name='companyadmin',
            name='motivation_company_admin',
            field=models.TextField(null=True, help_text='Napište nám prosím, jakou zastáváte u Vašeho zaměstnavatele pozici', max_length=5000, verbose_name='Zaměstnanecká pozice', default='', blank=True),
        ),
        migrations.AlterField(
            model_name='competition',
            name='competitor_type',
            field=models.CharField(choices=[('single_user', 'Jednotliví soutěžící'), ('liberos', 'Liberos'), ('team', 'Týmy'), ('company', 'Soutěž firem')], max_length=16, help_text='Určuje, zdali bude soutěž týmová, nebo pro jednotlivce. Ostatní volby vybírejte jen pokud víte, k čemu slouží.', verbose_name='Typ soutěžícího'),
        ),
        migrations.AlterField(
            model_name='competition',
            name='sex',
            field=models.CharField(null=True, help_text='Pokud chcete oddělit výsledky pro muže a ženy, je potřeba vypsat dvě soutěže - jednu pro muže a druhou pro ženy. Jinak nechte prázdné.', choices=[('unknown', '-------'), ('male', 'Muž'), ('female', 'Žena')], max_length=50, verbose_name='Soutěž pouze pro pohlaví', default=None, blank=True),
        ),
        migrations.AlterField(
            model_name='competition',
            name='slug',
            field=models.SlugField(default='', verbose_name='Doména v URL', unique=True),
        ),
        migrations.AlterField(
            model_name='competition',
            name='type',
            field=models.CharField(choices=[('length', 'Ujetá vzdálenost'), ('frequency', 'Pravidelnost jízd na kole'), ('questionnaire', 'Dotazník')], max_length=16, help_text='Určuje, zdali bude soutěž výkonnostní (na ujetou vzdálenost), nebo na pravidelnost. Volba "Dotazník" slouží pro kreativní soutěže, cyklozaměstnavatele roku a další dotazníky; je nutné definovat otázky.', verbose_name='Typ'),
        ),
        migrations.AlterField(
            model_name='competition',
            name='url',
            field=models.URLField(null=True, help_text='Odkaz na stránku, kde budou pravidla a podrobné informace o soutěži', verbose_name='Odkaz na stránku soutěže', default='', blank=True),
        ),
        migrations.AlterField(
            model_name='gpxfile',
            name='direction',
            field=models.CharField(choices=[('trip_to', 'Tam'), ('trip_from', 'Zpět')], max_length=50, verbose_name='Směr cesty'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='order_id',
            field=models.CharField(null=True, max_length=50, verbose_name='Order ID', default='', blank=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='pay_type',
            field=models.CharField(choices=[('mp', 'mPenize - mBank'), ('kb', 'MojePlatba'), ('rf', 'ePlatby pro eKonto'), ('pg', 'GE Money Bank'), ('pv', 'Sberbank (Volksbank)'), ('pf', 'Fio banka'), ('cs', 'PLATBA 24 – Česká spořitelna'), ('era', 'Era - Poštovní spořitelna'), ('cb', 'ČSOB'), ('c', 'Kreditní karta přes GPE'), ('bt', 'bankovní převod'), ('pt', 'převod přes poštu'), ('sc', 'superCASH'), ('psc', 'PaySec'), ('mo', 'Mobito'), ('t', 'testovací platba'), ('fa', 'faktura mimo PayU'), ('fc', 'firma platí fakturou'), ('am', 'člen Klubu přátel Auto*Matu'), ('amw', 'kandidát na členství v Klubu přátel Auto*Matu'), ('fe', 'neplatí startovné')], null=True, max_length=50, verbose_name='Typ platby', blank=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='session_id',
            field=models.CharField(null=True, unique=True, max_length=50, verbose_name='Session ID', default=None, blank=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='trans_id',
            field=models.CharField(null=True, max_length=50, verbose_name='Transaction ID', blank=True),
        ),
        migrations.AlterField(
            model_name='phase',
            name='type',
            field=models.CharField(choices=[('registration', 'registrační'), ('late_admission', 'pozdní startovné'), ('compet_entry', 'vstup do soutěže (zastaralé)'), ('payment', 'placení startovného'), ('competition', 'soutěžní'), ('results', 'výsledková'), ('admissions', 'přihlašovací do soutěží'), ('invoices', 'vytváření faktur')], max_length=16, verbose_name='Typ fáze', default='registration'),
        ),
        migrations.AlterField(
            model_name='question',
            name='comment_type',
            field=models.CharField(null=True, choices=[(None, 'Nic'), ('text', 'Text'), ('link', 'Odkaz'), ('one-liner', 'Jeden řádek textu')], max_length=16, verbose_name='Typ komentáře', default=None, blank=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='type',
            field=models.CharField(choices=[('text', 'Text'), ('choice', 'Výběr odpovědi'), ('multiple-choice', 'Výběr z více odpovědí')], max_length=16, verbose_name='Typ', default='text'),
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='address_city',
            field=models.CharField(max_length=50, help_text='Např. Jablonec n. N. nebo Praha 3-Žižkov', verbose_name='Město', default=''),
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='address_district',
            field=models.CharField(null=True, max_length=50, verbose_name='Městská část', default='', blank=True),
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='address_recipient',
            field=models.CharField(null=True, help_text='Např. odštěpný závod Brno, oblastní pobočka Liberec, Přírodovědecká fakulta atp.', max_length=50, verbose_name='Název společnosti (pobočky, závodu, kanceláře, fakulty) na adrese', default='', blank=True),
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='address_street',
            field=models.CharField(max_length=50, help_text='Např. Šeříková nebo Nám. W. Churchilla', verbose_name='Ulice', default=''),
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='address_street_number',
            field=models.CharField(max_length=10, help_text='Např. 2965/12 nebo 156', verbose_name='Číslo domu', default=''),
        ),
        migrations.AlterField(
            model_name='team',
            name='invitation_token',
            field=models.CharField(default='', max_length=100, unique=True, validators=[dpnk.models.validate_length], verbose_name='Token pro pozvánky'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='description',
            field=models.TextField(null=True, verbose_name='Popis', default='', blank=True),
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='approved_for_team',
            field=models.CharField(choices=[('approved', 'Odsouhlasený'), ('undecided', 'Nerozhodnuto'), ('denied', 'Zamítnutý')], max_length=16, verbose_name='Souhlas týmu', default='undecided'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='language',
            field=models.CharField(choices=[('cs', 'Čeština'), ('en', 'Angličtna')], max_length=16, help_text='Jazyk, ve kterém vám budou docházet emaily z registračního systému', verbose_name='Jazyk emailů', default='cs'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='sex',
            field=models.CharField(choices=[('unknown', '-------'), ('male', 'Muž'), ('female', 'Žena')], max_length=50, help_text='Slouží k zařazení do výkonnostních kategorií', verbose_name='Pohlaví', default='unknown'),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='type',
            field=models.CharField(choices=[('rekola', 'ReKola')], max_length=10, verbose_name='typ voucheru', default='rekola'),
        ),
    ]
