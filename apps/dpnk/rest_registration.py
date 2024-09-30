from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth.models import User


class CustomRegisterSerializer(RegisterSerializer):
    username = None  # Remove the username field

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
