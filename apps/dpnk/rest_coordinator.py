from rest_framework import routers, viewsets, permissions, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
import drf_serpy as serpy

from .models import (
    UserAttendance,
    CompanyAdmin,
    Payment,
    Status,
    Company,
    Subsidiary,
    Team,
    Campaign,
)

from .models.company import CompanyInCampaign
from .rest import (
    UserAttendanceSerializer,
    AddressSerializer,
    EmptyStrField,
    RequestSpecificField,
)
from .middleware import get_or_create_userattendance
import datetime
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import APIException
from django.forms.models import model_to_dict


class UserAttendanceMixin:
    def ua(self):
        ua = self.request.user_attendance
        if not ua:
            ua = get_or_create_userattendance(self.request, self.request.subdomain)
        return ua


class FeeApprovalSerializer(serpy.Serializer):
    id = serpy.IntField()
    company_admission_fee = serpy.IntField(call=True)
    first_name = serpy.StrField(attr="userprofile.user.first_name")
    last_name = serpy.StrField(attr="userprofile.user.last_name")
    nickname = serpy.StrField(attr="userprofile.nickname")
    email = serpy.StrField(attr="userprofile.user.email")
    city = serpy.StrField(attr="team.subsidiary.city")
    created = serpy.StrField()


class CompanyAdminDoesNotExist(serializers.ValidationError):
    status_code = 403
    default_detail = {"company_admin": "User is not company admin"}


class TeamNotEmpty(APIException):
    status_code = 400
    default_detail = "Cannot delete a team with active members."
    default_code = "team_not_empty"


class FeeApprovalSet(viewsets.ReadOnlyModelViewSet, UserAttendanceMixin):
    def get_queryset(self):

        try:
            company_admin = CompanyAdmin.objects.get(
                userprofile=self.ua().userprofile.pk,
                campaign__slug=self.request.subdomain,
                company_admin_approved="approved",
            )
        except CompanyAdmin.DoesNotExist:
            raise CompanyAdminDoesNotExist

        queryset = (
            UserAttendance.objects.filter(
                team__subsidiary__company=company_admin.administrated_company,
                campaign=company_admin.campaign,
                userprofile__user__is_active=True,
                representative_payment__pay_type="fc",
            )
            .exclude(
                payment_status="done",
            )
            .select_related(
                "userprofile__user",
                "campaign",
                "team__subsidiary__city",
                "t_shirt_size",
                "representative_payment",
            )
            .order_by(
                "team__subsidiary__city",
                "userprofile__user__last_name",
                "userprofile__user__first_name",
            )
        )
        return queryset

    serializer_class = FeeApprovalSerializer
    permission_classes = [permissions.IsAuthenticated]


class ApprovePaymentsDeserializer(serializers.Serializer):

    ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
    )


class ApprovePaymentsView(APIView, UserAttendanceMixin):
    def post(self, request):
        serializer = ApprovePaymentsDeserializer(data=request.data)
        if serializer.is_valid():
            ids = serializer.validated_data["ids"]

            try:
                company_admin = CompanyAdmin.objects.get(
                    userprofile=self.ua().userprofile.pk,
                    campaign__slug=self.request.subdomain,
                    company_admin_approved="approved",
                )
            except CompanyAdmin.DoesNotExist:
                raise CompanyAdminDoesNotExist

            users = UserAttendance.objects.filter(
                id__in=ids,
                team__subsidiary__company=company_admin.administrated_company,
                campaign=company_admin.campaign,
                userprofile__user__is_active=True,
                representative_payment__pay_type="fc",
            ).exclude(
                payment_status="done",
            )

            approved_count = 0
            for user in users:
                payment = user.representative_payment
                payment.status = Status.COMPANY_ACCEPTS
                payment.amount = user.company_admission_fee()
                payment.description = (
                    payment.description
                    + "\nFA %s odsouhlasil dne %s"
                    % (self.request.user.username, datetime.datetime.now())
                )
                payment.save()
                approved_count += 1

            return Response(
                {
                    "message": f"Approved {approved_count} payments successfully",
                    "approved_ids": [user.id for user in users],
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserAttendanceSerializer(serpy.Serializer):
    id = serpy.IntField()
    first_name = serpy.StrField(attr="userprofile.user.first_name")
    last_name = serpy.StrField(attr="userprofile.user.last_name")
    nickname = EmptyStrField(attr="userprofile.nickname")
    email = serpy.StrField(attr="userprofile.user.email")
    company_admission_fee = serpy.IntField(call=True)
    payment_status = serpy.StrField()
    # representative_payment = serpy.StrField(call=True)
    created = serpy.StrField()


class TeamSerializer(serpy.Serializer):
    id = serpy.IntField()
    name = serpy.StrField()
    users = UserAttendanceSerializer(many=True)


class SubsidiaryInCampaignSerializer(serpy.Serializer):
    id = serpy.IntField(attr="subsidiary.id")
    address = AddressSerializer(attr="subsidiary.address")
    city = serpy.StrField(attr="subsidiary.city")
    teams = TeamSerializer(many=True)


class GetAttendanceSerializer(serpy.Serializer):
    subsidiaries = SubsidiaryInCampaignSerializer(many=True)


class GetAttendanceView(APIView, UserAttendanceMixin):
    def get(self, request):

        try:
            company_admin = CompanyAdmin.objects.get(
                userprofile=self.ua().userprofile.pk,
                campaign__slug=self.request.subdomain,
                company_admin_approved="approved",
            )
        except CompanyAdmin.DoesNotExist:
            raise CompanyAdminDoesNotExist

        company = Company.objects.get(
            pk=company_admin.administrated_company_id,
        )
        """
        ).select_related(
            "userprofile__user",
            "team",
            "team__subsidiary",
        """

        cic = CompanyInCampaign(company, self.request.campaign)
        return Response(GetAttendanceSerializer(cic).data)

    permission_classes = [permissions.IsAuthenticated]


class TeamNameSerializer(serpy.Serializer):
    id = serpy.IntField()
    name = serpy.StrField()


class SubsidiarySerializer(serpy.Serializer):
    id = serpy.IntField()
    address = AddressSerializer()
    city = serpy.StrField()
    teams = RequestSpecificField(
        lambda subsidiary, req: [
            TeamNameSerializer(t).data
            for t in subsidiary.teams.filter(
                campaign__slug=req.subdomain,
            )
        ]
    )


class SubsidiaryTeamSerializer(serpy.Serializer):
    id = serpy.IntField()
    name = serpy.StrField()
    members = UserAttendanceSerializer(many=True)


class SubsidiaryView(viewsets.ReadOnlyModelViewSet, UserAttendanceMixin):
    def get_queryset(self):

        try:
            company_admin = CompanyAdmin.objects.get(
                userprofile=self.ua().userprofile.pk,
                campaign__slug=self.request.subdomain,
                company_admin_approved="approved",
            )
        except CompanyAdmin.DoesNotExist:
            raise CompanyAdminDoesNotExist

        queryset = Subsidiary.objects.filter(
            company=company_admin.administrated_company,
        )

        return queryset

    serializer_class = SubsidiarySerializer
    permission_classes = [permissions.IsAuthenticated]


class SubsidiaryTeamDeserializer(serializers.HyperlinkedModelSerializer):
    campaign_id = serializers.PrimaryKeyRelatedField(
        queryset=Campaign.objects.all(), source="campaign"
    )
    subsidiary_id = serializers.PrimaryKeyRelatedField(
        queryset=Subsidiary.objects.all(), source="subsidiary"
    )

    class Meta:
        model = Team
        fields = ("id", "name", "campaign_id", "subsidiary_id")

    def to_representation(self, value):
        data = super().to_representation(value)
        del data["campaign_id"]
        del data["subsidiary_id"]
        return data


class TeamView(viewsets.ModelViewSet, UserAttendanceMixin):
    def get_queryset(self):

        try:
            company_admin = CompanyAdmin.objects.get(
                userprofile=self.ua().userprofile.pk,
                campaign__slug=self.request.subdomain,
                company_admin_approved="approved",
            )
        except CompanyAdmin.DoesNotExist:
            raise CompanyAdminDoesNotExist

        queryset = Team.objects.filter(
            subsidiary__company=company_admin.administrated_company,
            subsidiary=self.kwargs["subsidiary_id"],
            campaign__slug=self.request.subdomain,
        )

        return queryset

    def destroy(self, request, *args, **kwargs):
        team = self.get_object()
        if team.all_members().exists():
            raise TeamNotEmpty
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return SubsidiaryTeamSerializer
        else:
            return SubsidiaryTeamDeserializer

    permission_classes = [permissions.IsAuthenticated]


class MemberSerializer(serpy.Serializer):
    id = serpy.IntField()
    name = serpy.StrField(call=True)
    approved_for_team = serpy.StrField()


class MemberDeserializer(serializers.HyperlinkedModelSerializer):
    campaign_id = serializers.PrimaryKeyRelatedField(
        queryset=Campaign.objects.all(), source="campaign"
    )
    team_id = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(), source="team"
    )

    class Meta:
        model = UserAttendance
        fields = ("id", "name", "team_id", "campaign_id", "approved_for_team")

    def validate(self, data):
        instance = self.instance or self.Meta.model(**data)
        if self.instance:
            old_instance = instance
            new_data = data

            if "team" in new_data:
                oldcompany = old_instance.team.subsidiary.company.id
                newcompany = new_data["team"].subsidiary.company.id
                if oldcompany != newcompany:
                    raise serializers.ValidationError(
                        "Cannot move members between companies"
                    )

            for key, value in data.items():
                setattr(instance, key, value)
        # Call full_clean() to trigger model validation
        instance.full_clean()

        return data


class MemberView(viewsets.ModelViewSet, UserAttendanceMixin):
    def get_queryset(self):

        try:
            company_admin = CompanyAdmin.objects.get(
                userprofile=self.ua().userprofile.pk,
                campaign__slug=self.request.subdomain,
                company_admin_approved="approved",
            )
        except CompanyAdmin.DoesNotExist:
            raise CompanyAdminDoesNotExist

        queryset = UserAttendance.objects.filter(
            team__subsidiary__company=company_admin.administrated_company,
            team__subsidiary=self.kwargs["subsidiary_id"],
            team=self.kwargs["team_id"],
            campaign__slug=self.request.subdomain,
        )

        return queryset

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return MemberSerializer
        else:
            return MemberDeserializer

    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        instance.team = None
        instance.save()


router = routers.DefaultRouter()
router.register(r"fee-approval", FeeApprovalSet, basename="fee-approval")
# router.register(r"approve-payments", ApprovePaymentsView, basename="approve-payments")
# router.register(r"get-attendance", GetAttendanceView, basename="get-attendance")
router.register(r"subsidiary", SubsidiaryView, basename="subsidiary-coordinator")
router.register(
    r"subsidiary/(?P<subsidiary_id>\d+)/team", TeamView, basename="subsidiary-team"
)
router.register(
    r"subsidiary/(?P<subsidiary_id>\d+)/team/(?P<team_id>\d+)/member",
    MemberView,
    basename="subsidiary-team-member",
)
