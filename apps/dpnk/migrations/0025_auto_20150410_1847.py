# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0024_auto_20150402_1350'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='answer',
            options={'ordering': ('user_attendance__team__subsidiary__city', 'pk'), 'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'Answer', 'verbose_name_plural': 'Answers'},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'campaign', 'verbose_name_plural': 'campaigns'},
        ),
        migrations.AlterModelOptions(
            name='choice',
            options={'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'Choice to questionnaire questions', 'verbose_name_plural': 'Choices to questionnaire questions'},
        ),
        migrations.AlterModelOptions(
            name='choicetype',
            options={'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'Choice type', 'verbose_name_plural': 'Choice type'},
        ),
        migrations.AlterModelOptions(
            name='city',
            options={'ordering': ('name',), 'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'Town', 'verbose_name_plural': 'Towns'},
        ),
        migrations.AlterModelOptions(
            name='cityincampaign',
            options={'ordering': ('campaign', 'city__name'), 'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'Town in the campaign', 'verbose_name_plural': 'Towns in the campaign'},
        ),
        migrations.AlterModelOptions(
            name='company',
            options={'ordering': ('name',), 'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'Company', 'verbose_name_plural': 'Companies'},
        ),
        migrations.AlterModelOptions(
            name='companyadmin',
            options={'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'Company coordinator', 'verbose_name_plural': 'Company coordinators'},
        ),
        migrations.AlterModelOptions(
            name='competition',
            options={'ordering': ('-campaign', 'type', 'name'), 'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'Competition', 'verbose_name_plural': 'Competitions'},
        ),
        migrations.AlterModelOptions(
            name='competitionresult',
            options={'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'Competition result', 'verbose_name_plural': 'Competition results'},
        ),
        migrations.AlterModelOptions(
            name='deliverybatch',
            options={'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'Delivery batch', 'verbose_name_plural': 'Delivery batches'},
        ),
        migrations.AlterModelOptions(
            name='invoice',
            options={'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'Invoice', 'verbose_name_plural': 'Invoices'},
        ),
        migrations.AlterModelOptions(
            name='phase',
            options={'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'champaign phase', 'verbose_name_plural': 'champaign phase'},
        ),
        migrations.AlterModelOptions(
            name='question',
            options={'ordering': ('order',), 'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'Survey question', 'verbose_name_plural': 'Survey questions'},
        ),
        migrations.AlterModelOptions(
            name='subsidiary',
            options={'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'Subdivision', 'verbose_name_plural': 'Subdivisions'},
        ),
        migrations.AlterModelOptions(
            name='team',
            options={'ordering': ('name',), 'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'Team', 'verbose_name_plural': 'Teams'},
        ),
        migrations.AlterModelOptions(
            name='trip',
            options={'ordering': ('date',), 'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'Trip', 'verbose_name_plural': 'Trips'},
        ),
        migrations.AlterModelOptions(
            name='tshirtsize',
            options={'ordering': ['order'], 'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'T-shirt size', 'verbose_name_plural': 'T-shirt size'},
        ),
        migrations.AlterModelOptions(
            name='userattendance',
            options={'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'Campaign attendee', 'verbose_name_plural': 'Campaign attendees'},
        ),
        migrations.AlterModelOptions(
            name='userprofile',
            options={'ordering': ['user__last_name', 'user__first_name'], 'default_permissions': ('view', 'add', 'change', 'delete'), 'verbose_name': 'User profile', 'verbose_name_plural': 'User profiles'},
        ),
    ]
