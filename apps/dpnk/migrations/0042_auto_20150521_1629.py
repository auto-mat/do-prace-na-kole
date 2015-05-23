# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def change_bool_to_charfield(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Question = apps.get_model("dpnk", "Question")
    for question in Question.objects.all():
        if question.with_comment == True:
            question.comment_type = 'text'
        else:
            question.comment_type = None
        question.save()

class Migration(migrations.Migration):

    dependencies = [
        ('dpnk', '0041_auto_20150521_1629'),
    ]

    operations = [
        migrations.RunPython(change_bool_to_charfield),
    ]
