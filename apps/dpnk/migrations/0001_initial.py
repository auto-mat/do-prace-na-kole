# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import dpnk.models
import django.db.models.deletion
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comment', models.TextField(max_length=600, null=True, verbose_name='Comment', blank=True)),
                ('points_given', models.IntegerField(default=None, null=True, blank=True)),
                ('attachment', models.FileField(max_length=600, upload_to=b'questionaire/', blank=True)),
            ],
            options={
                'ordering': ('user_attendance__team__subsidiary__city', 'pk'),
                'verbose_name': 'Answer',
                'verbose_name_plural': 'Answers',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=60, verbose_name='Name of campaign')),
                ('slug', models.SlugField(default=b'', unique=True, verbose_name='Dom\xe9na v URL')),
                ('email_footer', models.TextField(default=b'', max_length=5000, null=True, verbose_name='Users e-mail footer', blank=True)),
                ('mailing_list_id', models.CharField(default=b'', max_length=60, verbose_name='ID mailing list', blank=True)),
                ('mailing_list_enabled', models.BooleanField(default=False, verbose_name='Permit mailing list')),
                ('trip_plus_distance', models.PositiveIntegerField(default=5, help_text='How much can competitor increase his/her ride against ordinar distance (in km)', null=True, verbose_name='Maximal distance increase', blank=True)),
                ('tracking_number_first', models.PositiveIntegerField(default=0, verbose_name='First digit of the start kit delivery')),
                ('tracking_number_last', models.PositiveIntegerField(default=999999999, verbose_name='Last digit of the start kit delivery')),
                ('invoice_sequence_number_first', models.PositiveIntegerField(default=0, verbose_name='First sequence number for invoices')),
                ('invoice_sequence_number_last', models.PositiveIntegerField(default=999999999, verbose_name='Last sequence number for invoices')),
            ],
            options={
                'verbose_name': 'campaign',
                'verbose_name_plural': 'campaigns',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=250, verbose_name='Choice', db_index=True)),
                ('points', models.IntegerField(default=None, null=True, verbose_name='Points', blank=True)),
            ],
            options={
                'verbose_name': 'Choice to questionnaire questions',
                'verbose_name_plural': 'Choices to questionnaire questions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ChoiceType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=40, unique=True, null=True, verbose_name='Name')),
                ('universal', models.BooleanField(default=False, verbose_name='Choice type can be used for more questions')),
            ],
            options={
                'verbose_name': 'Choice type',
                'verbose_name_plural': 'Choice type',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=40, verbose_name='Name')),
                ('slug', models.SlugField(unique=True, verbose_name='Subdom\xe9na v URL')),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'Town',
                'verbose_name_plural': 'Towns',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CityInCampaign',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('admission_fee', models.PositiveIntegerField(default=180, verbose_name='Starting fee')),
                ('admission_fee_company', models.FloatField(default=179.34, verbose_name='Company starting fee')),
                ('campaign', models.ForeignKey(to='dpnk.Campaign', on_delete=models.CASCADE)),
                ('city', models.ForeignKey(to='dpnk.City', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('campaign', 'city__name'),
                'verbose_name': 'Town in the campaign',
                'verbose_name_plural': 'Towns in the campaign',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='For example V\xfdrobna, a.s., P\u0159\xedsp\u011bvkov\xe1, p.o., Nevl\xe1dka, o.s., Univerzita Karlova', unique=True, max_length=60, verbose_name='Company name')),
                ('address_street', models.CharField(default=b'', help_text='For example \u0160e\u0159\xedkov\xe1 nebo N\xe1m. W. Churchilla', max_length=50, verbose_name='Street')),
                ('address_street_number', models.CharField(default=b'', help_text='For example. 2965/12 or 156', max_length=10, verbose_name='House number')),
                ('address_recipient', models.CharField(default=b'', max_length=50, blank=True, help_text='For example Brno, Liberec, Science faculty', null=True, verbose_name='Company name (subsidiary, office, faculty) on the address')),
                ('address_district', models.CharField(default=b'', max_length=50, null=True, verbose_name='City part', blank=True)),
                ('address_psc', models.IntegerField(default=0, help_text='For example 130 00', verbose_name='ZIP code (PS\u010c)', validators=[django.core.validators.MaxValueValidator(99999), django.core.validators.MinValueValidator(10000)])),
                ('address_city', models.CharField(default=b'', help_text='For example Jablonec n.N. or Praha 3-\u017di\u017ekov', max_length=50, verbose_name='Town')),
                ('ico', models.PositiveIntegerField(default=None, null=True, verbose_name='Company registration number (I\u010cO)')),
                ('dic', models.CharField(default=b'', max_length=10, null=True, verbose_name='VAT ID', blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'Company',
                'verbose_name_plural': 'Companies',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CompanyAdmin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('company_admin_approved', models.CharField(default=b'undecided', max_length=16, verbose_name='Company administration approved', choices=[(b'approved', 'Confirmed'), (b'undecided', 'Unconfirmed'), (b'denied', 'Denied')])),
                ('motivation_company_admin', models.TextField(default=b'', max_length=5000, blank=True, help_text='Please, write us, which position you occupy in your company', null=True, verbose_name='Occupied position')),
                ('note', models.TextField(max_length=500, null=True, verbose_name='Internal note', blank=True)),
                ('can_confirm_payments', models.BooleanField(default=False, verbose_name='Can confirm payments')),
                ('administrated_company', models.ForeignKey(related_name=b'company_admin', verbose_name='Administrated company', to='dpnk.Company', null=True, on_delete=models.CASCADE)),
                ('campaign', models.ForeignKey(to='dpnk.Campaign', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(related_name=b'company_admin', verbose_name='U\u017eivatel', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Company administrator',
                'verbose_name_plural': 'Company administrators',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Competition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=160, verbose_name='Competition name')),
                ('slug', models.SlugField(default=b'', unique=True, verbose_name='Dom\xe9na v URL')),
                ('url', models.URLField(default=b'', null=True, verbose_name='Odkaz na str\xe1nku sout\u011b\u017ee', blank=True)),
                ('date_from', models.DateField(default=None, help_text='The rides are counting from this date', verbose_name='Competition beginning date')),
                ('date_to', models.DateField(default=None, help_text='After this date the competition will be closed (or fill questionnaire)', verbose_name='Competition end date')),
                ('type', models.CharField(max_length=16, verbose_name='Type', choices=[(b'length', 'Distance ridden'), (b'frequency', 'Bike rides regularity'), (b'questionnaire', 'Questionnaire')])),
                ('competitor_type', models.CharField(max_length=16, verbose_name='Competitor type', choices=[(b'single_user', 'Individual competitors'), (b'liberos', 'Liberos'), (b'team', 'Teams'), (b'company', 'Company competition')])),
                ('sex', models.CharField(default=None, choices=[(b'male', 'Mu\u017e'), (b'female', '\u017dena'), (b'unknown', 'Nezn\xe1m\xe9')], max_length=50, blank=True, null=True, verbose_name='Sout\u011b\u017e pouze pro pohlav\xed')),
                ('without_admission', models.BooleanField(default=True, help_text='Questionnaire is usually with admission, frequency and regullarity without admission.', verbose_name='Competition is without admission')),
                ('public_answers', models.BooleanField(default=False, verbose_name='Zve\u0159ej\u0148ovat sout\u011b\u017en\xed odpov\u011bdi')),
                ('is_public', models.BooleanField(default=True, verbose_name='Competition is public')),
                ('entry_after_beginning_days', models.IntegerField(default=7, help_text='Days from begining, when it is still possible to admit the competition.', verbose_name='Prolonged admissions')),
                ('rules', models.TextField(default=None, null=True, verbose_name='Competition rules', blank=True)),
                ('campaign', models.ForeignKey(verbose_name='Campaign', to='dpnk.Campaign', on_delete=models.CASCADE)),
                ('city', models.ForeignKey(verbose_name='Competition is only for cities', blank=True, to='dpnk.City', null=True, on_delete=models.CASCADE)),
                ('company', models.ForeignKey(verbose_name='Competition is only for companies', blank=True, to='dpnk.Company', null=True, on_delete=models.CASCADE)),
                ('company_competitors', models.ManyToManyField(related_name=b'competitions', null=True, to='dpnk.Company', blank=True)),
            ],
            options={
                'ordering': ('-campaign', 'type', 'name'),
                'verbose_name': 'Competition',
                'verbose_name_plural': 'Competitions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CompetitionResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('result', models.FloatField(default=None, null=True, verbose_name='Result', db_index=True, blank=True)),
                ('company', models.ForeignKey(related_name=b'company_results', default=None, blank=True, to='dpnk.Company', null=True, on_delete=models.CASCADE)),
                ('competition', models.ForeignKey(related_name=b'results', to='dpnk.Competition', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Competition result',
                'verbose_name_plural': 'Competition results',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DeliveryBatch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, verbose_name='Created')),
                ('customer_sheets', models.FileField(upload_to=b'customer_sheets', null=True, verbose_name='Customer sheets', blank=True)),
                ('tnt_order', models.FileField(upload_to=b'tnt_order', null=True, verbose_name='TNT order', blank=True)),
                ('author', models.ForeignKey(related_name=b'deliverybatch_create', verbose_name='author', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)),
                ('campaign', models.ForeignKey(verbose_name='Campaign', to='dpnk.Campaign', on_delete=models.SET_NULL)),
                ('updated_by', models.ForeignKey(related_name=b'deliverybatch_update', verbose_name='last updated by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)),
            ],
            options={
                'verbose_name': 'Delivery batch',
                'verbose_name_plural': 'Delivery batches',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, verbose_name='Created')),
                ('exposure_date', models.DateField(default=datetime.date.today, null=True, verbose_name='Invoice exposure date')),
                ('taxable_date', models.DateField(default=datetime.date.today, null=True, verbose_name='Taxable date')),
                ('paid_date', models.DateField(default=None, null=True, verbose_name='Payment date', blank=True)),
                ('invoice_pdf', models.FileField(upload_to=b'invoices', null=True, verbose_name='PDF invoice', blank=True)),
                ('sequence_number', models.PositiveIntegerField(unique=True, verbose_name='Invoice sequence number')),
                ('order_number', models.BigIntegerField(null=True, verbose_name='Order number', blank=True)),
                ('author', models.ForeignKey(related_name=b'invoice_create', verbose_name='author', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('campaign', models.ForeignKey(verbose_name='Campaign', to='dpnk.Campaign', on_delete=models.CASCADE)),
                ('company', models.ForeignKey(verbose_name='Company', to='dpnk.Company', on_delete=models.CASCADE)),
                ('updated_by', models.ForeignKey(related_name=b'invoice_update', verbose_name='last updated by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Invoice',
                'verbose_name_plural': 'Invoices',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Phase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(default=b'registration', max_length=16, verbose_name='Phase type', choices=[(b'registration', 'registration'), (b'compet_entry', 'main competition entry'), (b'competition', 'competition'), (b'results', 'results'), (b'admissions', 'apply for competitions')])),
                ('date_from', models.DateField(default=None, null=True, verbose_name='Phase beginning date', blank=True)),
                ('date_to', models.DateField(default=None, null=True, verbose_name='Phase end date', blank=True)),
                ('campaign', models.ForeignKey(verbose_name='Campaign', to='dpnk.Campaign', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'champaign phase',
                'verbose_name_plural': 'champaign phase',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=60, null=True, verbose_name='Name', blank=True)),
                ('text', models.TextField(null=True, verbose_name='Question', blank=True)),
                ('date', models.DateField(null=True, verbose_name='Day', blank=True)),
                ('type', models.CharField(default=b'text', max_length=16, verbose_name='Type', choices=[(b'text', 'Text'), (b'choice', 'Choice'), (b'multiple-choice', 'Multiple choice ')])),
                ('with_comment', models.BooleanField(default=True, verbose_name='Allow comment')),
                ('with_attachment', models.BooleanField(default=False, verbose_name='Allow attachment')),
                ('order', models.IntegerField(null=True, verbose_name='Order', blank=True)),
                ('choice_type', models.ForeignKey(default=None, blank=True, to='dpnk.ChoiceType', null=True, verbose_name='Choice type', on_delete=models.CASCADE)),
                ('competition', models.ForeignKey(verbose_name='Competition', to='dpnk.Competition', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('order',),
                'verbose_name': 'Survey question',
                'verbose_name_plural': 'Survey questions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Subsidiary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('address_street', models.CharField(default=b'', help_text='For example \u0160e\u0159\xedkov\xe1 nebo N\xe1m. W. Churchilla', max_length=50, verbose_name='Street')),
                ('address_street_number', models.CharField(default=b'', help_text='For example. 2965/12 or 156', max_length=10, verbose_name='House number')),
                ('address_recipient', models.CharField(default=b'', max_length=50, blank=True, help_text='For example Brno, Liberec, Science faculty', null=True, verbose_name='Company name (subsidiary, office, faculty) on the address')),
                ('address_district', models.CharField(default=b'', max_length=50, null=True, verbose_name='City part', blank=True)),
                ('address_psc', models.IntegerField(default=0, help_text='For example 130 00', verbose_name='ZIP code (PS\u010c)', validators=[django.core.validators.MaxValueValidator(99999), django.core.validators.MinValueValidator(10000)])),
                ('address_city', models.CharField(default=b'', help_text='For example Jablonec n.N. or Praha 3-\u017di\u017ekov', max_length=50, verbose_name='Town')),
                ('city', models.ForeignKey(verbose_name='Competing town', to='dpnk.City', help_text="Rozhoduje o tom, kde budete sout\u011b\u017eit - vizte <a href='/~petr/dpnk-wp//pravidla' target='_blank'>pravidla sout\u011b\u017ee</a>", on_delete=models.CASCADE)),
                ('company', models.ForeignKey(related_name=b'subsidiaries', to='dpnk.Company', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Subdivision',
                'verbose_name_plural': 'Subdivisions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, verbose_name='Team name')),
                ('invitation_token', models.CharField(default=b'', unique=True, max_length=100, verbose_name='Invitation token')),
                ('member_count', models.IntegerField(default=0, verbose_name='Number of authorized team members', db_index=True)),
                ('campaign', models.ForeignKey(verbose_name='Campaign', to='dpnk.Campaign', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'Team',
                'verbose_name_plural': 'Teams',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.PositiveIntegerField(default=0, max_length=50, verbose_name='Status')),
                ('created', models.DateTimeField(default=datetime.datetime.now, verbose_name='Created')),
                ('description', models.TextField(default=b'', null=True, verbose_name='Description', blank=True)),
                ('realized', models.DateTimeField(null=True, verbose_name='Realized', blank=True)),
            ],
            options={
                'verbose_name': 'Transaction',
                'verbose_name_plural': 'Transaction',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('transaction_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='dpnk.Transaction', on_delete=models.CASCADE)),
                ('order_id', models.CharField(default=b'', max_length=50, null=True, verbose_name=b'Order ID', blank=True)),
                ('session_id', models.CharField(default=b'', max_length=50, null=True, verbose_name=b'Session ID', blank=True)),
                ('trans_id', models.CharField(max_length=50, null=True, verbose_name=b'Transaction ID', blank=True)),
                ('amount', models.PositiveIntegerField(verbose_name='Amount')),
                ('pay_type', models.CharField(blank=True, max_length=50, null=True, verbose_name='Payment type', choices=[(b'mp', 'mPenize - mBank'), (b'kb', 'MojePlatba'), (b'rf', 'ePlatby pro eKonto'), (b'pg', 'GE Money Bank'), (b'pv', 'Sberbank (Volksbank)'), (b'pf', 'Fio banka'), (b'cs', 'PLATBA 24 \u2013 \u010cesk\xe1 spo\u0159itelna'), (b'era', 'Era - Po\u0161tovn\xed spo\u0159itelna'), (b'cb', '\u010cSOB'), (b'c', 'Credit card via GPE'), (b'bt', 'bank transfer'), (b'pt', 'transfer by post office'), (b'sc', 'superCASH'), (b'psc', 'PaySec'), (b'mo', 'Mobito'), (b't', 'testing payment'), (b'fa', 'invoice outside PayU'), (b'fc', 'company pays by invoice'), (b'am', 'Auto*Mat Friends Club member')])),
                ('error', models.PositiveIntegerField(null=True, verbose_name='Error', blank=True)),
                ('invoice', models.ForeignKey(related_name=b'payment_set', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='dpnk.Invoice', null=True)),
            ],
            options={
                'verbose_name': 'Payment transaction',
                'verbose_name_plural': 'Payment transaction',
            },
            bases=('dpnk.transaction',),
        ),
        migrations.CreateModel(
            name='PackageTransaction',
            fields=[
                ('transaction_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='dpnk.Transaction', on_delete=models.CASCADE)),
                ('tracking_number', models.PositiveIntegerField(unique=True, verbose_name='TNT tracking number')),
                ('delivery_batch', models.ForeignKey(verbose_name='Delivery batch', to='dpnk.DeliveryBatch', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Package transaction',
                'verbose_name_plural': 'Package transaction',
            },
            bases=('dpnk.transaction',),
        ),
        migrations.CreateModel(
            name='CommonTransaction',
            fields=[
                ('transaction_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='dpnk.Transaction', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Common transaction',
                'verbose_name_plural': 'Common transactions',
            },
            bases=('dpnk.transaction',),
        ),
        migrations.CreateModel(
            name='Trip',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(default=datetime.datetime.now, verbose_name='Trip date')),
                ('trip_to', models.BooleanField(default=False, verbose_name='Trip to work')),
                ('trip_from', models.BooleanField(default=False, verbose_name='Trip from work')),
                ('distance_to', models.IntegerField(default=None, null=True, verbose_name='Distance ridden to work', blank=True, validators=[django.core.validators.MaxValueValidator(1000), django.core.validators.MinValueValidator(0)])),
                ('distance_from', models.IntegerField(default=None, null=True, verbose_name='Distance ridden from work', blank=True, validators=[django.core.validators.MaxValueValidator(1000), django.core.validators.MinValueValidator(0)])),
            ],
            options={
                'ordering': ('date',),
                'verbose_name': 'Trip',
                'verbose_name_plural': 'Trips',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TShirtSize',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=40, verbose_name='T-shirt size')),
                ('order', models.PositiveIntegerField(default=0)),
                ('ship', models.BooleanField(default=True, verbose_name='Ships?')),
                ('available', models.BooleanField(default=True, help_text='Is shown in the t-shirt sizes', verbose_name='Is available?')),
                ('t_shirt_preview', models.FileField(upload_to=b't_shirt_preview', null=True, verbose_name='T-shirt preview', blank=True)),
                ('campaign', models.ForeignKey(verbose_name='Campaign', to='dpnk.Campaign', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['order'],
                'verbose_name': 'T-shirt size',
                'verbose_name_plural': 'T-shirt size',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserActionTransaction',
            fields=[
                ('transaction_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='dpnk.Transaction', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'User action',
                'verbose_name_plural': 'User actions',
            },
            bases=('dpnk.transaction',),
        ),
        migrations.CreateModel(
            name='UserAttendance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('distance', models.PositiveIntegerField(default=None, help_text='Average distance from home to work (in km in one direction)', null=True, verbose_name='Distance', blank=True)),
                ('approved_for_team', models.CharField(default=b'undecided', max_length=16, verbose_name='Team approval', choices=[(b'approved', 'Confirmed'), (b'undecided', 'Unconfirmed'), (b'denied', 'Denied')])),
                ('campaign', models.ForeignKey(verbose_name='Campaign', to='dpnk.Campaign', on_delete=models.CASCADE)),
                ('t_shirt_size', models.ForeignKey(verbose_name='T-shirt size', to='dpnk.TShirtSize', null=True, on_delete=models.CASCADE)),
                ('team', models.ForeignKey(related_name=b'users', default=None, blank=True, to='dpnk.Team', null=True, verbose_name='Team', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Campaign attendance',
                'verbose_name_plural': 'Campaign attendances',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('telephone', models.CharField(max_length=30, verbose_name='Telephone')),
                ('language', models.CharField(default=b'cs', max_length=16, verbose_name='Language', choices=[(b'cs', 'Czech'), (b'en', 'English')])),
                ('mailing_id', models.CharField(default=None, max_length=128, blank=True, null=True, verbose_name='Mailing list ID', db_index=True)),
                ('mailing_hash', models.BigIntegerField(default=None, null=True, verbose_name='Hash of last synchronization with mailing list', blank=True)),
                ('sex', models.CharField(default=b'unknown', max_length=50, verbose_name='Pohlav\xed', choices=[(b'male', 'Mu\u017e'), (b'female', '\u017dena'), (b'unknown', 'Nezn\xe1m\xe9')])),
                ('note', models.TextField(null=True, verbose_name='Internal note', blank=True)),
                ('administrated_cities', models.ManyToManyField(related_name=b'city_admins', null=True, to='dpnk.CityInCampaign', blank=True)),
                ('user', models.OneToOneField(related_name=b'userprofile', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['user__last_name', 'user__first_name'],
                'verbose_name': 'User profile',
                'verbose_name_plural': 'U\u017eivatelsk\xe9 profily',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='userattendance',
            name='userprofile',
            field=models.ForeignKey(verbose_name='User profile', to='dpnk.UserProfile', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='userattendance',
            unique_together=set([('userprofile', 'campaign')]),
        ),
        migrations.AlterUniqueTogether(
            name='tshirtsize',
            unique_together=set([('name', 'campaign')]),
        ),
        migrations.AddField(
            model_name='trip',
            name='user_attendance',
            field=models.ForeignKey(related_name=b'user_trips', default=None, blank=True, to='dpnk.UserAttendance', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='trip',
            unique_together=set([('user_attendance', 'date')]),
        ),
        migrations.AddField(
            model_name='transaction',
            name='author',
            field=models.ForeignKey(related_name=b'transaction_create', verbose_name='author', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='transaction',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name=b'polymorphic_dpnk.transaction_set', editable=False, to='contenttypes.ContentType', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='transaction',
            name='updated_by',
            field=models.ForeignKey(related_name=b'transaction_update', verbose_name='last updated by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='transaction',
            name='user_attendance',
            field=models.ForeignKey(related_name=b'transactions', default=None, to='dpnk.UserAttendance', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='team',
            name='coordinator_campaign',
            field=models.OneToOneField(related_name=b'coordinated_team', null=True, verbose_name='Team coordinator', to='dpnk.UserAttendance', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='team',
            name='subsidiary',
            field=models.ForeignKey(related_name=b'teams', verbose_name='Subdivision', to='dpnk.Subsidiary', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='team',
            unique_together=set([('name', 'campaign')]),
        ),
        migrations.AlterUniqueTogether(
            name='phase',
            unique_together=set([('type', 'campaign')]),
        ),
        migrations.AddField(
            model_name='packagetransaction',
            name='t_shirt_size',
            field=models.ForeignKey(verbose_name='T-shirt size', to='dpnk.TShirtSize', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='competitionresult',
            name='team',
            field=models.ForeignKey(related_name=b'competitions_results', default=None, blank=True, to='dpnk.Team', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='competitionresult',
            name='user_attendance',
            field=models.ForeignKey(related_name=b'competitions_results', default=None, blank=True, to='dpnk.UserAttendance', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='competitionresult',
            unique_together=set([('team', 'competition'), ('user_attendance', 'competition')]),
        ),
        migrations.AddField(
            model_name='competition',
            name='team_competitors',
            field=models.ManyToManyField(related_name=b'competitions', null=True, to='dpnk.Team', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='competition',
            name='user_attendance_competitors',
            field=models.ManyToManyField(related_name=b'competitions', null=True, to='dpnk.UserAttendance', blank=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='companyadmin',
            unique_together=set([('user', 'campaign'), ('administrated_company', 'campaign')]),
        ),
        migrations.AlterUniqueTogether(
            name='cityincampaign',
            unique_together=set([('city', 'campaign')]),
        ),
        migrations.AddField(
            model_name='choicetype',
            name='competition',
            field=models.ForeignKey(to='dpnk.Competition', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='choicetype',
            unique_together=set([('competition', 'name')]),
        ),
        migrations.AddField(
            model_name='choice',
            name='choice_type',
            field=models.ForeignKey(related_name=b'choices', verbose_name='Choice type', to='dpnk.ChoiceType', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='choice',
            unique_together=set([('choice_type', 'text')]),
        ),
        migrations.AddField(
            model_name='answer',
            name='choices',
            field=models.ManyToManyField(to='dpnk.Choice', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(to='dpnk.Question', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='answer',
            name='user_attendance',
            field=models.ForeignKey(blank=True, to='dpnk.UserAttendance', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='answer',
            unique_together=set([('user_attendance', 'question')]),
        ),
        migrations.CreateModel(
            name='SubsidiaryInCampaign',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('dpnk.subsidiary',),
        ),
        migrations.CreateModel(
            name='TeamInCampaign',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('dpnk.team',),
        ),
        migrations.CreateModel(
            name='TeamName',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('dpnk.team',),
        ),
        migrations.CreateModel(
            name='UserAttendanceRelated',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('dpnk.userattendance',),
        ),
    ]
