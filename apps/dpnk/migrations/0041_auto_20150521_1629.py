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
        ('dpnk', '0040_auto_20150515_1729'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='comment_type',
            field=models.CharField(default=None, max_length=16, null=True, verbose_name='Typ koment\xe1\u0159e', choices=[(None, 'Nic'), (b'text', 'Text'), (b'link', 'Odkaz'), (b'one-liner', 'Jeden \u0159\xe1dek textu')]),
            preserve_default=True,
        ),
        migrations.RunPython(change_bool_to_charfield),
        migrations.RemoveField(
            model_name='question',
            name='with_comment',
        ),
    ]
