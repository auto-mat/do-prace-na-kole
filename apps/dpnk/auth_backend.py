from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class EmailModelBackend(ModelBackend):
    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            return None

        if user.check_password(password):
            return user
