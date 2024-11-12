# Generated by Django 2.2.28 on 2024-11-12 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0175_auto_20240605_0948'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='pay_type',
            field=models.CharField(blank=True, choices=[('mp', 'mPenize - mBank'), ('mps', 'mPenize - mBank'), ('kb', 'MojePlatba'), ('rf', 'ePlatby pro eKonto'), ('pg', 'GE Money Bank'), ('pv', 'Sberbank (Volksbank)'), ('pf', 'Fio banka'), ('pfs', 'Fio banka'), ('cs', 'Česká spořitelna'), ('css', 'Česká spořitelna'), ('era', 'Era - Poštovní spořitelna'), ('cb', 'ČSOB'), ('c', 'Kreditní karta přes GPE'), ('bt', 'bankovní převod'), ('pt', 'převod přes poštu'), ('sc', 'superCASH'), ('psc', 'PaySec'), ('mo', 'Mobito'), ('uc', 'UniCredit'), ('t', 'testovací platba'), ('fa', 'faktura mimo PayU'), ('fc', 'platba přes firemního koordinátora'), ('am', 'člen Klubu přátel AutoMatu'), ('amw', 'kandidát na členství v Klubu přátel AutoMatu'), ('fe', 'neplatí startovné'), ('rbczs', 'Raiffeisen Bank'), ('rf', 'Raiffeisen Bank'), ('cbs', 'Československá obchodní banka'), ('kb', 'Komerční banka'), ('kbs', 'Komerční banka'), ('mons', 'MONETA Money Bank'), ('dpcz', 'Pay later with Twisto - Czech')], max_length=50, null=True, verbose_name='Typ platby'),
        ),
    ]
