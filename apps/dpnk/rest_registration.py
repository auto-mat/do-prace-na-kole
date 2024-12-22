from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth.models import User
from rest_framework import serializers
from django.db import transaction
from dj_rest_auth.registration.views import RegisterView

from .models import (
    UserProfile,
    CompanyAdmin,
    Campaign,
    UserAttendance,
)

import copy


class BasicRegisterSerializer(RegisterSerializer):
    username = None  # Remove the username field

    def save(self, request):
        user = super().save(request)
        username = user.email.split("@")[0]  # Calculate username from email
        user_number = User.objects.count()

        user.username = f"{username}@{user_number}"

        user.save()
        return user


class RegisterCoordinatorSerializer(BasicRegisterSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user_fields = UserSerializer().fields
        user_profile_fields = UserProfileSerializer().fields
        company_admin_fields = CompanyAdminSerializer().fields
        user_attendance_fields = UserAttendanceSerializer().fields

        for field_name, field in user_fields.items():
            self.fields[field_name] = copy.deepcopy(field)

        for field_name, field in user_profile_fields.items():
            self.fields[field_name] = copy.deepcopy(field)

        for field_name, field in company_admin_fields.items():
            self.fields[field_name] = copy.deepcopy(field)

        for field_name, field in user_attendance_fields.items():
            self.fields[field_name] = copy.deepcopy(field)

    @transaction.atomic
    def save(self, request):

        user = super().save(request)
        user.first_name = self.validated_data.get("first_name", "")
        user.last_name = self.validated_data.get("last_name", "")
        user.save()

        campaign = Campaign.objects.get(slug=request.subdomain)

        userprofile = UserProfile(
            user=user,
            telephone=self.validated_data.get("telephone", ""),
            newsletter=self.validated_data.get("newsletter"),
        )
        userprofile.save()

        company_admin = CompanyAdmin(
            userprofile=userprofile,
            administrated_company=self.validated_data.get("administrated_company"),
            motivation_company_admin=self.validated_data.get(
                "motivation_company_admin"
            ),
            will_pay_opt_in=self.validated_data.get("will_pay_opt_in"),
            campaign=campaign,
        )
        company_admin.save()

        userattendance = UserAttendance(
            campaign=campaign,
            userprofile=userprofile,
            personal_data_opt_in=self.validated_data.get("personal_data_opt_in"),
            payment_status="None",
        )
        userattendance.save()

        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "firstName",
            "lastName",
        )
        extra_kwargs = {
            "firstName": {"source": "first_name"},
            "lastName": {"source": "last_name"},
        }


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            "phone",
            "newsletter",
        )
        extra_kwargs = {
            "phone": {"source": "telephone"},
        }


class CompanyAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyAdmin
        fields = (
            "organizationId",
            "jobTitle",
            "responsibility",
        )
        extra_kwargs = {
            "organizationId": {"source": "administrated_company"},
            "jobTitle": {"source": "motivation_company_admin"},
            "responsibility": {"source": "will_pay_opt_in"},
        }


class UserAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAttendance
        fields = ("terms",)
        extra_kwargs = {
            "terms": {"source": "personal_data_opt_in"},
        }


class BasicRegisterView(RegisterView):
    serializer_class = BasicRegisterSerializer


class RegisterCoordinatorView(RegisterView):
    serializer_class = RegisterCoordinatorSerializer
