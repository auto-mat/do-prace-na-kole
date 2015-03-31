# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def null_session_id(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Payment  = apps.get_model("dpnk", "Payment")
    for payment in Payment.objects.all():
        if payment.session_id == "":
            payment.session_id = None
            payment.save()

class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0021_auto_20150330_1530'),
    ]

    operations = [
        migrations.RunPython(null_session_id),
    ]
