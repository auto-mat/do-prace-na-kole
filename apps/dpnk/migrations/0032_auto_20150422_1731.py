# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def change_cic_to_c(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Competition  = apps.get_model("dpnk", "Competition")
    for competition in Competition.objects.all():
        if competition.city:
            competition.cities.add(competition.city)
            competition.save()

class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0031_auto_20150422_1730'),
    ]

    operations = [
        migrations.RunPython(change_cic_to_c),
    ]
