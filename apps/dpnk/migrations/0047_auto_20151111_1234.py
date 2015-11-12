# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import dpnk.models
import django.contrib.gis.db.models.fields
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0046_auto_20150601_1631'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='answer',
            options={'ordering': ('user_attendance__team__subsidiary__city', 'pk'), 'verbose_name': 'Odpov\u011b\u010f', 'verbose_name_plural': 'Odpov\u011bdi'},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={'verbose_name': 'kampa\u0148', 'verbose_name_plural': 'kampan\u011b'},
        ),
        migrations.AlterModelOptions(
            name='choice',
            options={'verbose_name': 'Nab\xeddka k anketn\xedm ot\xe1zce', 'verbose_name_plural': 'Nab\xeddky k anketn\xedm ot\xe1zk\xe1m'},
        ),
        migrations.AlterModelOptions(
            name='choicetype',
            options={'verbose_name': 'Typ volby', 'verbose_name_plural': 'Typ volby'},
        ),
        migrations.AlterModelOptions(
            name='city',
            options={'ordering': ('name',), 'verbose_name': 'M\u011bsto', 'verbose_name_plural': 'M\u011bsta'},
        ),
        migrations.AlterModelOptions(
            name='cityincampaign',
            options={'ordering': ('campaign', 'city__name'), 'verbose_name': 'M\u011bsto v kampani', 'verbose_name_plural': 'M\u011bsta v kampani'},
        ),
        migrations.AlterModelOptions(
            name='commontransaction',
            options={'verbose_name': 'Obecn\xe1 transakce', 'verbose_name_plural': 'Obecn\xe9 transakce'},
        ),
        migrations.AlterModelOptions(
            name='company',
            options={'ordering': ('name',), 'verbose_name': 'Firma', 'verbose_name_plural': 'Firmy'},
        ),
        migrations.AlterModelOptions(
            name='companyadmin',
            options={'verbose_name': 'Firemn\xed koordin\xe1tor', 'verbose_name_plural': 'Firemn\xed koordin\xe1to\u0159i'},
        ),
        migrations.AlterModelOptions(
            name='competition',
            options={'ordering': ('-campaign', 'type', 'name'), 'verbose_name': 'Sout\u011b\u017e', 'verbose_name_plural': 'Sout\u011b\u017ee'},
        ),
        migrations.AlterModelOptions(
            name='competitionresult',
            options={'verbose_name': 'V\xfdsledek sout\u011b\u017ee', 'verbose_name_plural': 'V\xfdsledky sout\u011b\u017e\xed'},
        ),
        migrations.AlterModelOptions(
            name='deliverybatch',
            options={'verbose_name': 'D\xe1vka objedn\xe1vek', 'verbose_name_plural': 'D\xe1vky objedn\xe1vek'},
        ),
        migrations.AlterModelOptions(
            name='invoice',
            options={'verbose_name': 'Faktura', 'verbose_name_plural': 'Faktury'},
        ),
        migrations.AlterModelOptions(
            name='packagetransaction',
            options={'verbose_name': 'Transakce bal\xedku', 'verbose_name_plural': 'Transakce bal\xedku'},
        ),
        migrations.AlterModelOptions(
            name='payment',
            options={'verbose_name': 'Platebn\xed transakce', 'verbose_name_plural': 'Platebn\xed transakce'},
        ),
        migrations.AlterModelOptions(
            name='phase',
            options={'verbose_name': 'f\xe1ze kampan\u011b', 'verbose_name_plural': 'f\xe1ze kampan\u011b'},
        ),
        migrations.AlterModelOptions(
            name='question',
            options={'ordering': ('order',), 'verbose_name': 'Anketn\xed ot\xe1zka', 'verbose_name_plural': 'Anketn\xed ot\xe1zky'},
        ),
        migrations.AlterModelOptions(
            name='subsidiary',
            options={'verbose_name': 'Pobo\u010dka firmy', 'verbose_name_plural': 'Pobo\u010dky firem'},
        ),
        migrations.AlterModelOptions(
            name='team',
            options={'ordering': ('name',), 'verbose_name': 'T\xfdm', 'verbose_name_plural': 'T\xfdmy'},
        ),
        migrations.AlterModelOptions(
            name='transaction',
            options={'verbose_name': 'Transakce', 'verbose_name_plural': 'Transakce'},
        ),
        migrations.AlterModelOptions(
            name='trip',
            options={'ordering': ('date',), 'verbose_name': 'Cesta', 'verbose_name_plural': 'Cesty'},
        ),
        migrations.AlterModelOptions(
            name='tshirtsize',
            options={'ordering': ['order'], 'verbose_name': 'Velikost tri\u010dka', 'verbose_name_plural': 'Velikosti tri\u010dka'},
        ),
        migrations.AlterModelOptions(
            name='useractiontransaction',
            options={'verbose_name': 'U\u017eivatelsk\xe1 akce', 'verbose_name_plural': 'U\u017eivatelsk\xe9 akce'},
        ),
        migrations.AlterModelOptions(
            name='userattendance',
            options={'verbose_name': '\xda\u010dastn\xedk kampan\u011b', 'verbose_name_plural': '\xda\u010dastn\xedci kampan\u011b'},
        ),
        migrations.AlterModelOptions(
            name='userattendancetobatch',
            options={'verbose_name': 'U\u017eivatel na d\xe1vku objedn\xe1vek', 'verbose_name_plural': 'U\u017eivatel\xe9 na d\xe1vku objedn\xe1vek'},
        ),
        migrations.AlterModelOptions(
            name='userprofile',
            options={'ordering': ['user__last_name', 'user__first_name'], 'verbose_name': 'U\u017eivatelsk\xfd profil', 'verbose_name_plural': 'U\u017eivatelsk\xe9 profily'},
        ),
        migrations.AlterField(
            model_name='answer',
            name='choices',
            field=models.ManyToManyField(to='dpnk.Choice', blank=True),
        ),
        migrations.AlterField(
            model_name='answer',
            name='comment',
            field=models.TextField(max_length=600, null=True, verbose_name='Koment\xe1\u0159', blank=True),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='admission_fee',
            field=models.FloatField(default=0, verbose_name='V\u010dasn\xe9 startovn\xe9'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='admission_fee_company',
            field=models.FloatField(default=0, verbose_name='V\u010dasn\xe9 startovn\xe9 pro firmy'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='benefitial_admission_fee',
            field=models.FloatField(default=0, verbose_name='Benefi\u010dn\xed startovn\xe9'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='email_footer',
            field=models.TextField(default=b'', max_length=5000, null=True, verbose_name='Pati\u010dka u\u017eivatelsk\xfdch email\u016f', blank=True),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='free_entry_cases_html',
            field=models.TextField(null=True, verbose_name='P\u0159\xedpady, kdy je startovn\xe9 zdarma', blank=True),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='invoice_sequence_number_first',
            field=models.PositiveIntegerField(default=0, verbose_name='Prvn\xed \u010d\xedslo \u0159ady pro faktury'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='invoice_sequence_number_last',
            field=models.PositiveIntegerField(default=999999999, verbose_name='Posledn\xed \u010d\xedslo \u0159ady pro faktury'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='late_admission_fee',
            field=models.FloatField(default=0, verbose_name='Pozdn\xed startovn\xe9'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='late_admission_fee_company',
            field=models.FloatField(default=0, verbose_name='Pozdn\xed startovn\xe9 pro firmy'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='mailing_list_enabled',
            field=models.BooleanField(default=False, verbose_name='Povolit mailing list'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='mailing_list_id',
            field=models.CharField(default=b'', max_length=60, verbose_name='ID mailing listu', blank=True),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='minimum_percentage',
            field=models.PositiveIntegerField(default=66, verbose_name='Minim\xe1ln\xed procento pro kvalifikaci do pravidelnostn\xed sout\u011b\u017ee'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='minimum_rides_base',
            field=models.PositiveIntegerField(default=25, help_text='Minim\xe1ln\xed po\u010det j\xedzd, kter\xe9 je nutn\xe9 si zapsat, aby bylo mo\u017en\xe9 dos\xe1hnout 100% j\xedzd', verbose_name='Minim\xe1ln\xed z\xe1klad po\u010dtu j\xedzd'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='name',
            field=models.CharField(unique=True, max_length=60, verbose_name='Jm\xe9no kampan\u011b'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='package_depth',
            field=models.PositiveIntegerField(default=35, null=True, verbose_name='Hloubka bal\xedku', blank=True),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='package_height',
            field=models.PositiveIntegerField(default=1, null=True, verbose_name='V\xfd\u0161ka bal\xedku', blank=True),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='package_weight',
            field=models.FloatField(default=0.25, null=True, verbose_name='V\xe1ha bal\xedku', blank=True, validators=[django.core.validators.MaxValueValidator(1000), django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='package_width',
            field=models.PositiveIntegerField(default=26, null=True, verbose_name='\u0160\xed\u0159ka bal\xedku', blank=True),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='previous_campaign',
            field=models.ForeignKey(verbose_name='P\u0159edchoz\xed kampa\u0148', blank=True, to='dpnk.Campaign', null=True),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='tracking_number_first',
            field=models.PositiveIntegerField(default=0, verbose_name='Prvn\xed \u010d\xedslo \u0159ady pro doru\u010dov\xe1n\xed bal\xed\u010dk\u016f'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='tracking_number_last',
            field=models.PositiveIntegerField(default=999999999, verbose_name='Posledn\xed \u010d\xedslo \u0159ady pro doru\u010dov\xe1n\xed bal\xed\u010dk\u016f'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='trip_plus_distance',
            field=models.PositiveIntegerField(default=5, help_text='Po\u010det kilometr\u016f, o kter\xe9 je mo\u017en\xe9 prodlou\u017eit si jednu j\xedzdu', null=True, verbose_name='Maxim\xe1ln\xed nav\xfd\u0161en\xed vzd\xe1lenosti', blank=True),
        ),
        migrations.AlterField(
            model_name='choice',
            name='choice_type',
            field=models.ForeignKey(related_name='choices', verbose_name='Typ volby', to='dpnk.ChoiceType'),
        ),
        migrations.AlterField(
            model_name='choice',
            name='points',
            field=models.IntegerField(default=None, null=True, verbose_name='Body', blank=True),
        ),
        migrations.AlterField(
            model_name='choice',
            name='text',
            field=models.CharField(max_length=250, verbose_name='Nab\xeddka', db_index=True),
        ),
        migrations.AlterField(
            model_name='choicetype',
            name='name',
            field=models.CharField(max_length=40, unique=True, null=True, verbose_name='Jm\xe9no'),
        ),
        migrations.AlterField(
            model_name='choicetype',
            name='universal',
            field=models.BooleanField(default=False, verbose_name='Typ volby je pou\u017eiteln\xfd pro v\xedc ot\xe1zek'),
        ),
        migrations.AlterField(
            model_name='city',
            name='cyklistesobe_slug',
            field=models.CharField(max_length=40, null=True, verbose_name='Jm\xe9no skupiny na webu Cyklist\xe9 sob\u011b'),
        ),
        migrations.AlterField(
            model_name='city',
            name='location',
            field=django.contrib.gis.db.models.fields.PointField(srid=4326, null=True, verbose_name='poloha m\u011bsta'),
        ),
        migrations.AlterField(
            model_name='city',
            name='name',
            field=models.CharField(unique=True, max_length=40, verbose_name='Jm\xe9no'),
        ),
        migrations.AlterField(
            model_name='company',
            name='active',
            field=models.BooleanField(default=True, verbose_name='Aktivn\xed'),
        ),
        migrations.AlterField(
            model_name='company',
            name='address_city',
            field=models.CharField(default=b'', help_text='Nap\u0159. Jablonec n. N. nebo Praha 3-\u017di\u017ekov', max_length=50, verbose_name='M\u011bsto'),
        ),
        migrations.AlterField(
            model_name='company',
            name='address_district',
            field=models.CharField(default=b'', max_length=50, null=True, verbose_name='M\u011bstsk\xe1 \u010d\xe1st', blank=True),
        ),
        migrations.AlterField(
            model_name='company',
            name='address_psc',
            field=models.IntegerField(default=None, help_text='Nap\u0159.: 130 00', null=True, verbose_name='PS\u010c', validators=[django.core.validators.MaxValueValidator(99999), django.core.validators.MinValueValidator(10000)]),
        ),
        migrations.AlterField(
            model_name='company',
            name='address_recipient',
            field=models.CharField(default=b'', max_length=50, blank=True, help_text='Nap\u0159. od\u0161t\u011bpn\xfd z\xe1vod Brno, oblastn\xed pobo\u010dka Liberec, P\u0159\xedrodov\u011bdeck\xe1 fakulta atp.', null=True, verbose_name='N\xe1zev spole\u010dnosti (pobo\u010dky, z\xe1vodu, kancel\xe1\u0159e, fakulty) na adrese'),
        ),
        migrations.AlterField(
            model_name='company',
            name='address_street',
            field=models.CharField(default=b'', help_text='Nap\u0159. \u0160e\u0159\xedkov\xe1 nebo N\xe1m. W. Churchilla', max_length=50, verbose_name='Ulice'),
        ),
        migrations.AlterField(
            model_name='company',
            name='address_street_number',
            field=models.CharField(default=b'', help_text='Nap\u0159. 2965/12 nebo 156', max_length=10, verbose_name='\u010c\xedslo domu'),
        ),
        migrations.AlterField(
            model_name='company',
            name='dic',
            field=models.CharField(default=b'', max_length=10, null=True, verbose_name='DI\u010c', blank=True),
        ),
        migrations.AlterField(
            model_name='company',
            name='ico',
            field=models.PositiveIntegerField(default=None, null=True, verbose_name='I\u010cO'),
        ),
        migrations.AlterField(
            model_name='company',
            name='name',
            field=models.CharField(help_text='Nap\u0159. V\xfdrobna, a.s., P\u0159\xedsp\u011bvkov\xe1, p.o., Nevl\xe1dka, o.s., Univerzita Karlova', unique=True, max_length=60, verbose_name='N\xe1zev spole\u010dnosti'),
        ),
        migrations.AlterField(
            model_name='companyadmin',
            name='administrated_company',
            field=models.ForeignKey(related_name='company_admin', verbose_name='Administrovan\xe1 spole\u010dnost', to='dpnk.Company', null=True),
        ),
        migrations.AlterField(
            model_name='companyadmin',
            name='can_confirm_payments',
            field=models.BooleanField(default=False, verbose_name='M\u016f\u017ee potvrzovat platby'),
        ),
        migrations.AlterField(
            model_name='companyadmin',
            name='company_admin_approved',
            field=models.CharField(default=b'undecided', max_length=16, verbose_name='Spr\xe1vcovstv\xed organizace schv\xe1leno', choices=[(b'approved', 'Odsouhlasen\xfd'), (b'undecided', 'Nerozhodnuto'), (b'denied', 'Zam\xedtnut\xfd')]),
        ),
        migrations.AlterField(
            model_name='companyadmin',
            name='motivation_company_admin',
            field=models.TextField(default=b'', max_length=5000, blank=True, help_text='Napi\u0161te n\xe1m pros\xedm, jakou zast\xe1v\xe1te u Va\u0161eho zam\u011bstnavatele pozici', null=True, verbose_name='Zam\u011bstnaneck\xe1 pozice'),
        ),
        migrations.AlterField(
            model_name='companyadmin',
            name='note',
            field=models.TextField(max_length=500, null=True, verbose_name='Intern\xed pozn\xe1mka', blank=True),
        ),
        migrations.AlterField(
            model_name='companyadmin',
            name='user',
            field=models.ForeignKey(related_name='company_admin', verbose_name='User', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='competition',
            name='campaign',
            field=models.ForeignKey(verbose_name='Kampa\u0148', to='dpnk.Campaign'),
        ),
        migrations.AlterField(
            model_name='competition',
            name='city',
            field=models.ManyToManyField(help_text='Sout\u011b\u017e bude prob\xedhat ve vybran\xfdch m\u011bstech. Pokud z\u016fstane pr\xe1zdn\xe9, sout\u011b\u017e prob\xedh\xe1 ve v\u0161ech m\u011bstech.', to='dpnk.City', verbose_name='Sout\u011b\u017e pouze pro m\u011bsta', blank=True),
        ),
        migrations.AlterField(
            model_name='competition',
            name='company',
            field=models.ForeignKey(verbose_name='Sout\u011b\u017e pouze pro firmu', blank=True, to='dpnk.Company', null=True),
        ),
        migrations.AlterField(
            model_name='competition',
            name='company_competitors',
            field=models.ManyToManyField(related_name='competitions', to='dpnk.Company', blank=True),
        ),
        migrations.AlterField(
            model_name='competition',
            name='competitor_type',
            field=models.CharField(help_text='Ur\u010duje, zdali bude sout\u011b\u017e t\xfdmov\xe1, nebo pro jednotlivce. Ostatn\xed volby vyb\xedrejte jen pokud v\xedte, k \u010demu slou\u017e\xed.', max_length=16, verbose_name='Typ sout\u011b\u017e\xedc\xedho', choices=[(b'single_user', 'Jednotliv\xed sout\u011b\u017e\xedc\xed'), (b'liberos', 'Liberos'), (b'team', 'T\xfdmy'), (b'company', 'Sout\u011b\u017e firem')]),
        ),
        migrations.AlterField(
            model_name='competition',
            name='date_from',
            field=models.DateField(default=None, help_text='Od tohoto data se po\u010d\xedtaj\xed j\xedzdy', null=True, verbose_name='Datum za\u010d\xe1tku sout\u011b\u017ee', blank=True),
        ),
        migrations.AlterField(
            model_name='competition',
            name='date_to',
            field=models.DateField(default=None, help_text='Po tomto datu nebude mo\u017en\xe9 sout\u011b\u017eit (vypl\u0148ovat dotazn\xedk)', null=True, verbose_name='Datum konce sout\u011b\u017ee', blank=True),
        ),
        migrations.AlterField(
            model_name='competition',
            name='entry_after_beginning_days',
            field=models.IntegerField(default=7, help_text='Po\u010det dn\xed po za\u010d\xe1tku sout\u011b\u017ee, kdy je je\u0161t\u011b mo\u017en\xe9 se p\u0159ihl\xe1sit', verbose_name='Prodlou\u017een\xe9 p\u0159ihl\xe1\u0161ky'),
        ),
        migrations.AlterField(
            model_name='competition',
            name='is_public',
            field=models.BooleanField(default=True, verbose_name='Sout\u011b\u017e je ve\u0159ejn\xe1'),
        ),
        migrations.AlterField(
            model_name='competition',
            name='name',
            field=models.CharField(max_length=160, verbose_name='Jm\xe9no sout\u011b\u017ee'),
        ),
        migrations.AlterField(
            model_name='competition',
            name='public_answers',
            field=models.BooleanField(default=False, verbose_name='Zve\u0159ej\u0148ovat sout\u011b\u017en\xed odpov\u011bdi'),
        ),
        migrations.AlterField(
            model_name='competition',
            name='rules',
            field=models.TextField(default=None, null=True, verbose_name='Pravidla sout\u011b\u017ee', blank=True),
        ),
        migrations.AlterField(
            model_name='competition',
            name='sex',
            field=models.CharField(default=None, choices=[(b'unknown', '-------'), (b'male', 'Mu\u017e'), (b'female', '\u017dena')], max_length=50, blank=True, help_text='Pokud chcete odd\u011blit v\xfdsledky pro mu\u017ee a \u017eeny, je pot\u0159eba vypsat dv\u011b sout\u011b\u017ee - jednu pro mu\u017ee a druhou pro \u017eeny. Jinak nechte pr\xe1zdn\xe9.', null=True, verbose_name='Sout\u011b\u017e pouze pro pohlav\xed'),
        ),
        migrations.AlterField(
            model_name='competition',
            name='team_competitors',
            field=models.ManyToManyField(related_name='competitions', to='dpnk.Team', blank=True),
        ),
        migrations.AlterField(
            model_name='competition',
            name='type',
            field=models.CharField(help_text='Ur\u010duje, zdali bude sout\u011b\u017e v\xfdkonnostn\xed (na ujetou vzd\xe1lenost), nebo na pravidelnost. Volba "Dotazn\xedk" slou\u017e\xed pro kreativn\xed sout\u011b\u017ee, cyklozam\u011bstnavatele roku a dal\u0161\xed dotazn\xedky; je nutn\xe9 definovat ot\xe1zky.', max_length=16, verbose_name='Typ', choices=[(b'length', 'Ujet\xe1 vzd\xe1lenost'), (b'frequency', 'Pravidelnost j\xedzd na kole'), (b'questionnaire', 'Dotazn\xedk')]),
        ),
        migrations.AlterField(
            model_name='competition',
            name='user_attendance_competitors',
            field=models.ManyToManyField(related_name='competitions', to='dpnk.UserAttendance', blank=True),
        ),
        migrations.AlterField(
            model_name='competition',
            name='without_admission',
            field=models.BooleanField(default=True, help_text='Dotazn\xedk je obvykle na p\u0159ihl\xe1\u0161ky, v\xfdkonnost tak\xe9 a pravidelnost bez nich.', verbose_name='Sout\u011b\u017e bez p\u0159ihl\xe1\u0161ek (pro v\u0161echny)'),
        ),
        migrations.AlterField(
            model_name='competitionresult',
            name='result',
            field=models.FloatField(default=None, null=True, verbose_name='V\xfdsledek', db_index=True, blank=True),
        ),
        migrations.AlterField(
            model_name='deliverybatch',
            name='campaign',
            field=models.ForeignKey(verbose_name='Kampa\u0148', to='dpnk.Campaign'),
        ),
        migrations.AlterField(
            model_name='deliverybatch',
            name='created',
            field=models.DateTimeField(default=datetime.datetime.now, verbose_name='Datum vytvo\u0159en\xed'),
        ),
        migrations.AlterField(
            model_name='deliverybatch',
            name='customer_sheets',
            field=models.FileField(upload_to='customer_sheets', null=True, verbose_name='Z\xe1kaznick\xe9 listy', blank=True),
        ),
        migrations.AlterField(
            model_name='deliverybatch',
            name='tnt_order',
            field=models.FileField(upload_to='tnt_order', null=True, verbose_name='Objedn\xe1vka pro TNT', blank=True),
        ),
        migrations.AlterField(
            model_name='gpxfile',
            name='direction',
            field=models.CharField(max_length=50, verbose_name='Sm\u011br cesty', choices=[(b'trip_to', 'Tam'), (b'trip_from', 'Zp\u011bt')]),
        ),
        migrations.AlterField(
            model_name='gpxfile',
            name='track',
            field=django.contrib.gis.db.models.fields.MultiLineStringField(srid=4326, geography=True, null=True, verbose_name='trasa', blank=True),
        ),
        migrations.AlterField(
            model_name='gpxfile',
            name='trip_date',
            field=models.DateField(verbose_name='Datum vykon\xe1n\xed cesty'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='campaign',
            field=models.ForeignKey(verbose_name='Kampa\u0148', to='dpnk.Campaign'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='company',
            field=models.ForeignKey(verbose_name='Spole\u010dnost', to='dpnk.Company'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='company_pais_benefitial_fee',
            field=models.BooleanField(default=False, verbose_name='Moje firma si p\u0159eje podpo\u0159it Auto*Mat a zaplatit benefi\u010dn\xed startovn\xe9 (450 K\u010d za osobu).'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='created',
            field=models.DateTimeField(default=datetime.datetime.now, verbose_name='Datum vytvo\u0159en\xed'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='exposure_date',
            field=models.DateField(default=datetime.date.today, null=True, verbose_name='Den vystaven\xed da\u0148ov\xe9ho dokladu'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='invoice_pdf',
            field=models.FileField(upload_to='invoices', null=True, verbose_name='PDF faktury', blank=True),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='order_number',
            field=models.BigIntegerField(null=True, verbose_name='\u010c\xedslo objedn\xe1vky (nepovinn\xe9)', blank=True),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='paid_date',
            field=models.DateField(default=None, null=True, verbose_name='Datum zaplacen\xed', blank=True),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='sequence_number',
            field=models.PositiveIntegerField(verbose_name='Po\u0159adov\xe9 \u010d\xedslo faktury'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='taxable_date',
            field=models.DateField(default=datetime.date.today, null=True, verbose_name='Den uskute\u010dn\u011bn\xed zdaniteln\xe9ho pln\u011bn\xed'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='total_amount',
            field=models.FloatField(default=0, verbose_name='Celkov\xe1 \u010d\xe1stka'),
        ),
        migrations.AlterField(
            model_name='packagetransaction',
            name='delivery_batch',
            field=models.ForeignKey(verbose_name='D\xe1vka objedn\xe1vek', to='dpnk.DeliveryBatch'),
        ),
        migrations.AlterField(
            model_name='packagetransaction',
            name='t_shirt_size',
            field=models.ForeignKey(verbose_name='Velikost tri\u010dka', to='dpnk.TShirtSize', null=True),
        ),
        migrations.AlterField(
            model_name='packagetransaction',
            name='tracking_number',
            field=models.PositiveIntegerField(unique=True, verbose_name='Tracking number TNT'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='amount',
            field=models.PositiveIntegerField(verbose_name='\u010c\xe1stka'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='error',
            field=models.PositiveIntegerField(null=True, verbose_name='Chyba', blank=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='pay_type',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Typ platby', choices=[(b'mp', 'mPenize - mBank'), (b'kb', 'MojePlatba'), (b'rf', 'ePlatby pro eKonto'), (b'pg', 'GE Money Bank'), (b'pv', 'Sberbank (Volksbank)'), (b'pf', 'Fio banka'), (b'cs', 'PLATBA 24 \u2013 \u010cesk\xe1 spo\u0159itelna'), (b'era', 'Era - Po\u0161tovn\xed spo\u0159itelna'), (b'cb', '\u010cSOB'), (b'c', 'Kreditn\xed karta p\u0159es GPE'), (b'bt', 'bankovn\xed p\u0159evod'), (b'pt', 'p\u0159evod p\u0159es po\u0161tu'), (b'sc', 'superCASH'), (b'psc', 'PaySec'), (b'mo', 'Mobito'), (b't', 'testovac\xed platba'), (b'fa', 'faktura mimo PayU'), (b'fc', 'firma plat\xed fakturou'), (b'am', '\u010dlen Klubu p\u0159\xe1tel Auto*Matu'), (b'amw', 'kandid\xe1t na \u010dlenstv\xed v Klubu p\u0159\xe1tel Auto*Matu'), (b'fe', 'neplat\xed startovn\xe9')]),
        ),
        migrations.AlterField(
            model_name='phase',
            name='campaign',
            field=models.ForeignKey(verbose_name='Kampa\u0148', to='dpnk.Campaign'),
        ),
        migrations.AlterField(
            model_name='phase',
            name='date_from',
            field=models.DateField(default=None, null=True, verbose_name='Datum za\u010d\xe1tku f\xe1ze', blank=True),
        ),
        migrations.AlterField(
            model_name='phase',
            name='date_to',
            field=models.DateField(default=None, null=True, verbose_name='Datum konce f\xe1ze', blank=True),
        ),
        migrations.AlterField(
            model_name='phase',
            name='type',
            field=models.CharField(default=b'registration', max_length=16, verbose_name='Typ f\xe1ze', choices=[(b'registration', 'registra\u010dn\xed'), (b'late_admission', 'pozdn\xed startovn\xe9'), (b'compet_entry', 'vstup do sout\u011b\u017ee (zastaral\xe9)'), (b'payment', 'placen\xed startovn\xe9ho'), (b'competition', 'sout\u011b\u017en\xed'), (b'results', 'v\xfdsledkov\xe1'), (b'admissions', 'p\u0159ihla\u0161ovac\xed do sout\u011b\u017e\xed'), (b'invoices', 'vytv\xe1\u0159en\xed faktur')]),
        ),
        migrations.AlterField(
            model_name='question',
            name='choice_type',
            field=models.ForeignKey(default=None, blank=True, to='dpnk.ChoiceType', null=True, verbose_name='Typ volby'),
        ),
        migrations.AlterField(
            model_name='question',
            name='competition',
            field=models.ForeignKey(verbose_name='Sout\u011b\u017e', to='dpnk.Competition'),
        ),
        migrations.AlterField(
            model_name='question',
            name='date',
            field=models.DateField(null=True, verbose_name='Den', blank=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='name',
            field=models.CharField(max_length=60, null=True, verbose_name='Jm\xe9no', blank=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='order',
            field=models.IntegerField(null=True, verbose_name='Po\u0159ad\xed', blank=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='text',
            field=models.TextField(null=True, verbose_name='Ot\xe1zka', blank=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='type',
            field=models.CharField(default=b'text', max_length=16, verbose_name='Typ', choices=[(b'text', 'Text'), (b'choice', 'V\xfdb\u011br odpov\u011bdi'), (b'multiple-choice', 'V\xfdb\u011br z v\xedce odpov\u011bd\xed')]),
        ),
        migrations.AlterField(
            model_name='question',
            name='with_attachment',
            field=models.BooleanField(default=False, verbose_name='Povolit p\u0159\xedlohu'),
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='active',
            field=models.BooleanField(default=True, verbose_name='Aktivn\xed'),
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='address_city',
            field=models.CharField(default=b'', help_text='Nap\u0159. Jablonec n. N. nebo Praha 3-\u017di\u017ekov', max_length=50, verbose_name='M\u011bsto'),
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='address_district',
            field=models.CharField(default=b'', max_length=50, null=True, verbose_name='M\u011bstsk\xe1 \u010d\xe1st', blank=True),
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='address_psc',
            field=models.IntegerField(default=None, help_text='Nap\u0159.: 130 00', null=True, verbose_name='PS\u010c', validators=[django.core.validators.MaxValueValidator(99999), django.core.validators.MinValueValidator(10000)]),
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='address_recipient',
            field=models.CharField(default=b'', max_length=50, blank=True, help_text='Nap\u0159. od\u0161t\u011bpn\xfd z\xe1vod Brno, oblastn\xed pobo\u010dka Liberec, P\u0159\xedrodov\u011bdeck\xe1 fakulta atp.', null=True, verbose_name='N\xe1zev spole\u010dnosti (pobo\u010dky, z\xe1vodu, kancel\xe1\u0159e, fakulty) na adrese'),
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='address_street',
            field=models.CharField(default=b'', help_text='Nap\u0159. \u0160e\u0159\xedkov\xe1 nebo N\xe1m. W. Churchilla', max_length=50, verbose_name='Ulice'),
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='address_street_number',
            field=models.CharField(default=b'', help_text='Nap\u0159. 2965/12 nebo 156', max_length=10, verbose_name='\u010c\xedslo domu'),
        ),
        migrations.AlterField(
            model_name='subsidiary',
            name='city',
            field=models.ForeignKey(verbose_name='Sout\u011b\u017en\xed m\u011bsto', to='dpnk.City', help_text="Rozhoduje o tom, kde budete sout\u011b\u017eit - vizte <a href='http://www.dopracenakole.net/pravidla' target='_blank'>pravidla sout\u011b\u017ee</a>"),
        ),
        migrations.AlterField(
            model_name='team',
            name='campaign',
            field=models.ForeignKey(verbose_name='Kampa\u0148', to='dpnk.Campaign'),
        ),
        migrations.AlterField(
            model_name='team',
            name='invitation_token',
            field=models.CharField(default=b'', unique=True, max_length=100, verbose_name='Token pro pozv\xe1nky', validators=[dpnk.models.validate_length]),
        ),
        migrations.AlterField(
            model_name='team',
            name='member_count',
            field=models.IntegerField(default=0, verbose_name='Po\u010det pr\xe1voplatn\xfdch \u010dlen\u016f t\xfdmu', db_index=True),
        ),
        migrations.AlterField(
            model_name='team',
            name='name',
            field=models.CharField(max_length=50, verbose_name='N\xe1zev t\xfdmu'),
        ),
        migrations.AlterField(
            model_name='team',
            name='subsidiary',
            field=models.ForeignKey(related_name='teams', verbose_name='Pobo\u010dka', to='dpnk.Subsidiary'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='created',
            field=models.DateTimeField(default=datetime.datetime.now, verbose_name='Vytvo\u0159en\xed'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='description',
            field=models.TextField(default=b'', null=True, verbose_name='Popis', blank=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='realized',
            field=models.DateTimeField(null=True, verbose_name='Realizace', blank=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='status',
            field=models.PositiveIntegerField(default=0, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='trip',
            name='date',
            field=models.DateField(default=datetime.datetime.now, verbose_name='Datum cesty'),
        ),
        migrations.AlterField(
            model_name='trip',
            name='distance_from',
            field=models.FloatField(default=None, null=True, verbose_name='Ujet\xe1 vzd\xe1lenost z pr\xe1ce', blank=True, validators=[django.core.validators.MaxValueValidator(1000), django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='trip',
            name='distance_to',
            field=models.FloatField(default=None, null=True, verbose_name='Ujet\xe1 vzd\xe1lenost do pr\xe1ce', blank=True, validators=[django.core.validators.MaxValueValidator(1000), django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='trip',
            name='is_working_ride_from',
            field=models.BooleanField(default=False, verbose_name='pracovn\xed cesta z pr\xe1ce'),
        ),
        migrations.AlterField(
            model_name='trip',
            name='is_working_ride_to',
            field=models.BooleanField(default=False, verbose_name='pracovn\xed cesta do pr\xe1ce'),
        ),
        migrations.AlterField(
            model_name='trip',
            name='trip_from',
            field=models.NullBooleanField(default=None, verbose_name='Cesta z pr\xe1ce'),
        ),
        migrations.AlterField(
            model_name='trip',
            name='trip_to',
            field=models.NullBooleanField(default=None, verbose_name='Cesta do pr\xe1ce'),
        ),
        migrations.AlterField(
            model_name='tshirtsize',
            name='available',
            field=models.BooleanField(default=True, help_text='Zobrazuje se v nab\xeddce trik', verbose_name='Je dostupn\xe9?'),
        ),
        migrations.AlterField(
            model_name='tshirtsize',
            name='campaign',
            field=models.ForeignKey(verbose_name='Kampa\u0148', to='dpnk.Campaign'),
        ),
        migrations.AlterField(
            model_name='tshirtsize',
            name='name',
            field=models.CharField(max_length=40, verbose_name='Velikost tri\u010dka'),
        ),
        migrations.AlterField(
            model_name='tshirtsize',
            name='ship',
            field=models.BooleanField(default=True, verbose_name='Pos\xedl\xe1 se?'),
        ),
        migrations.AlterField(
            model_name='tshirtsize',
            name='t_shirt_preview',
            field=models.FileField(upload_to='t_shirt_preview', null=True, verbose_name='N\xe1hled trika', blank=True),
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='approved_for_team',
            field=models.CharField(default=b'undecided', max_length=16, verbose_name='Souhlas t\xfdmu', choices=[(b'approved', 'Odsouhlasen\xfd'), (b'undecided', 'Nerozhodnuto'), (b'denied', 'Zam\xedtnut\xfd')]),
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='campaign',
            field=models.ForeignKey(verbose_name='Kampa\u0148', to='dpnk.Campaign'),
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Datum vytvo\u0159en\xed', null=True),
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='distance',
            field=models.FloatField(default=None, help_text='Pr\u016fm\u011brn\xe1 ujet\xe1 vzd\xe1lenost z domova do pr\xe1ce (v km v jednom sm\u011bru)', null=True, verbose_name='Vzd\xe1lenost', blank=True),
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='dont_want_insert_track',
            field=models.BooleanField(default=False, verbose_name='Nep\u0159eji si zad\xe1vat svoji trasu.'),
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='t_shirt_size',
            field=models.ForeignKey(verbose_name='Velikost tri\u010dka', to='dpnk.TShirtSize', null=True),
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='team',
            field=models.ForeignKey(related_name='users', default=None, blank=True, to='dpnk.Team', null=True, verbose_name='T\xfdm'),
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='track',
            field=django.contrib.gis.db.models.fields.LineStringField(srid=4326, blank=True, help_text='\n<ul>\n   <li><strong>Zad\xe1v\xe1n\xed trasy zah\xe1j\xedte kliknut\xedm na tla\u010d\xedtko "Nakreslit trasu".</strong></li>\n   <li>Zm\u011bnu trasy provedete po p\u0159epnut\xed do re\u017eimu \xfaprav kliknut\xedm na trasu.</li>\n   <li>Trasu sta\u010d\xed zadat tak, \u017ee bude z\u0159ejm\xe9, kter\xfdmi ulicemi vede.</li>\n   <li>Zad\xe1n\xed p\u0159esn\u011bj\u0161\xedho pr\u016fb\u011bhu n\xe1m v\u0161ak m\u016f\u017ee pomoci l\xe9pe zjistit jak se lid\xe9 na kole pohybuj\xed.</li>\n   <li>Trasu bude mo\u017en\xe9 zm\u011bnit nebo up\u0159esnit i pozd\u011bji v pr\u016fb\u011bhu sout\u011b\u017ee.</li>\n   <li>Polohu za\u010d\xe1tku a konce trasy sta\u010d\xed zad\xe1vat s p\u0159esnost\xed 100m.</li>\n</ul>\nTrasa slou\u017e\xed k v\xfdpo\u010dtu vzd\xe1lenosti a pom\u016f\u017ee n\xe1m l\xe9pe ur\u010dit pot\u0159eby lid\xed pohybu\xedc\xedch se ve m\u011bst\u011b na kole. Va\u0161e cesta se zobraz\xed va\u0161im t\xfdmov\xfdm koleg\u016fm.\n<br/>Trasy v\u0161ech \xfa\u010dastn\xedk\u016f budou v anonymizovan\xe9 podob\u011b zobrazen\xe9 na \xfavodn\xed str\xe1nce.\n', null=True, verbose_name='trasa', geography=True),
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Datum posledn\xed zm\u011bny', null=True),
        ),
        migrations.AlterField(
            model_name='userattendance',
            name='userprofile',
            field=models.ForeignKey(verbose_name='U\u017eivatelsk\xfd profil', to='dpnk.UserProfile'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='administrated_cities',
            field=models.ManyToManyField(related_name='city_admins', to='dpnk.City', blank=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='language',
            field=models.CharField(default=b'cs', help_text='Jazyk, ve kter\xe9m v\xe1m budou doch\xe1zet emaily z registra\u010dn\xedho syst\xe9mu', max_length=16, verbose_name='Jazyk email\u016f', choices=[(b'cs', '\u010ce\u0161tina'), (b'en', 'Angli\u010dtna')]),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='mailing_hash',
            field=models.BigIntegerField(default=None, null=True, verbose_name='Hash posledn\xed synchronizace s mailingem', blank=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='mailing_id',
            field=models.CharField(default=None, max_length=128, blank=True, null=True, verbose_name='ID u\u017eivatele v mailing listu', db_index=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='nickname',
            field=models.CharField(help_text='Zobraz\xed se ve v\u0161ech ve\u0159ejn\xfdch v\xfdpisech m\xedsto va\u0161eho jm\xe9na. Zad\xe1vejte takov\xe9 jm\xe9no, podle kter\xe9ho v\xe1s va\u0161i kolegov\xe9 poznaj\xed', max_length=60, null=True, verbose_name='Zobrazen\xe9 jm\xe9no', blank=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='note',
            field=models.TextField(null=True, verbose_name='Intern\xed pozn\xe1mka', blank=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='sex',
            field=models.CharField(default=b'unknown', help_text='Slou\u017e\xed k za\u0159azen\xed do v\xfdkonnostn\xedch kategori\xed', max_length=50, verbose_name='Pohlav\xed', choices=[(b'unknown', '-------'), (b'male', 'Mu\u017e'), (b'female', '\u017dena')]),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='telephone',
            field=models.CharField(max_length=30, verbose_name='Telefon'),
        ),
    ]
