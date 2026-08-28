from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers


class CustomRegisterSerializer(RegisterSerializer):
    username = None  # Remove the username field

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                _("Uživatel s touto e-mail adresou %(email)s je již registrován.")
                % {"email": value}
            )
        return value

    def save(self, request):
        user = super().save(request)
        username = user.email.split("@")[0]  # Calculate username from email
        user_number = User.objects.count()

        user.username = f"{username}@{user_number}"

        user.save()
        return user


from dj_rest_auth.registration.views import RegisterView


class CustomRegisterView(RegisterView):
    serializer_class = CustomRegisterSerializer
