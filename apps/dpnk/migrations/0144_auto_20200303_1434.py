# Generated by Django 2.2.10 on 2020-03-03 14:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0143_auto_20200206_1603'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='address_recipient',
            field=models.CharField(blank=True, default='', help_text='Vyplňte pouze pokud Vaše interní předpisy vyžadují jméno toho, kdo je za vyřízení faktury zodpovědný.', max_length=50, null=True, verbose_name='Adresát na faktuře'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='company_address_recipient',
            field=models.CharField(blank=True, default='', help_text='Vyplňte pouze pokud Vaše interní předpisy vyžadují jméno toho, kdo je za vyřízení faktury zodpovědný.', max_length=50, null=True, verbose_name='Adresát na faktuře'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='company_pais_benefitial_fee',
            field=models.BooleanField(default=False, verbose_name='Moje organizace si přeje podpořit AutoMat a zaplatit benefiční startovné.'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='pay_type',
            field=models.CharField(blank=True, choices=[('mp', 'mPenize - mBank'), ('kb', 'MojePlatba'), ('rf', 'ePlatby pro eKonto'), ('pg', 'GE Money Bank'), ('pv', 'Sberbank (Volksbank)'), ('pf', 'Fio banka'), ('cs', 'Česká spořitelna'), ('era', 'Era - Poštovní spořitelna'), ('cb', 'ČSOB'), ('c', 'Kreditní karta přes GPE'), ('bt', 'bankovní převod'), ('pt', 'převod přes poštu'), ('sc', 'superCASH'), ('psc', 'PaySec'), ('mo', 'Mobito'), ('uc', 'UniCredit'), ('t', 'testovací platba'), ('fa', 'faktura mimo PayU'), ('fc', 'platba přes firemního koordinátora'), ('am', 'člen Klubu přátel AutoMatu'), ('amw', 'kandidát na členství v Klubu přátel AutoMatu'), ('fe', 'neplatí startovné')], max_length=50, null=True, verbose_name='Typ platby'),
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='address_recipient',
            field=models.CharField(blank=True, default='', help_text='Vyplňte pouze pokud Vaše interní předpisy vyžadují jméno toho, kdo je za vyřízení faktury zodpovědný.', max_length=50, null=True, verbose_name='Pracoviště'),
        ),
    ]
