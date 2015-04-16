# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def change_cic_to_c(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    UserProfile  = apps.get_model("dpnk", "UserProfile")
    for userprofile in UserProfile.objects.all():
        for cic in userprofile.administrated_cities.all():
            userprofile.administrated_cities_tmp.add(cic.city)
        userprofile.save()

class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0025_auto_20150410_2158'),
    ]

    operations = [
        migrations.RunPython(change_cic_to_c),
    ]
