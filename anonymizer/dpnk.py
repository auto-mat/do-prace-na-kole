from datetime import datetime

from dj_anonymizer import anonym_field
from dj_anonymizer.register_models import (
    AnonymBase,
    register_anonym,
)

from django.contrib.auth.models import User

from faker import Factory


# using faker lib for generating nice names
fake = Factory.create()


# create anonymizer class
class UserAnonym(AnonymBase):
    last_name = anonym_field.function(fake.last_name)
    first_name = anonym_field.function(fake.first_name)
    email = anonym_field.string(
        "timothy.hobbs+testuser{seq}@auto-mat.cz",
        seq_callback=datetime.now,
    )
    username = anonym_field.string("user_name{seq}")

    class Meta:
        # anonymize all users except the first one
        queryset = User.objects.exclude(id=1)
        # list of fields which will not be changed
        exclude_fields = [
            "groups", "user_permissions", "is_active",
            "is_superuser", "last_login", "date_joined",
            "is_staff", "password",
        ]


register_anonym([
    (User, UserAnonym),
])
