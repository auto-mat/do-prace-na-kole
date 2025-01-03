# Generated by Django 2.2.28 on 2025-01-03 09:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0183_auto_20250103_0551'),
    ]

    operations = [
        migrations.CreateModel(
            name='PayUOrderedProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60, verbose_name='Jméno objednávaného produktu')),
                ('unit_price', models.PositiveIntegerField(verbose_name='Jednotková cena')),
                ('quantity', models.PositiveIntegerField(verbose_name='Množství')),
            ],
            options={
                'verbose_name': 'Objednávaný produkt',
                'verbose_name_plural': 'Objednávané produkty',
            },
        ),
        migrations.AddField(
            model_name='payment',
            name='payu_ordered_product',
            field=models.ManyToManyField(blank=True, help_text='PayU objednávaný produkt(y) - RTWBB startovné, RTWBB dar', to='dpnk.PayUOrderedProduct', verbose_name='PayU objednávaný produkt'),
        ),
    ]
