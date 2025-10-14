import datetime
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict

from rest_framework import viewsets, permissions, serializers, status
from rest_framework.exceptions import APIException
from rest_framework.views import APIView
from rest_framework.response import Response
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
from t_shirt_delivery.models import (
    BoxRequest,
)
from .models.company import CompanyInCampaign
from .rest import (
    UserAttendanceSerializer,
    AddressSerializer,
    EmptyStrField,
    NullIntField,
    router,
    RequestSpecificField,
    SubsidiaryInCampaignField,
)
from .middleware import get_or_create_userattendance


class UserAttendanceMixin:
    def ua(self):
        ua = self.request.user_attendance
        if not ua:
            ua = get_or_create_userattendance(self.request, self.request.subdomain)
        return ua


class CompanyAdminMixin(UserAttendanceMixin):
    def ca(self):

        if not hasattr(self, "_company_admin") or self._company_admin is None:
            try:
                self._company_admin = CompanyAdmin.objects.get(
                    userprofile=self.ua().userprofile.pk,
                    campaign__slug=self.request.subdomain,
                    company_admin_approved="approved",
                )
            except CompanyAdmin.DoesNotExist:
                raise CompanyAdminDoesNotExist
        return self._company_admin


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


class FeeApprovalSet(viewsets.ReadOnlyModelViewSet, CompanyAdminMixin):
    def get_queryset(self):

        company_admin = self.ca()

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


class ApprovePaymentsView(APIView, CompanyAdminMixin):
    def post(self, request):
        serializer = ApprovePaymentsDeserializer(data=request.data)
        if serializer.is_valid():
            ids = serializer.validated_data["ids"]

            company_admin = self.ca()

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


class GetAttendanceView(APIView, CompanyAdminMixin):
    def get(self, request):

        company_admin = self.ca()

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


class SubsidiaryView(viewsets.ReadOnlyModelViewSet, CompanyAdminMixin):
    def get_queryset(self):

        company_admin = self.ca()

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


class TeamView(viewsets.ModelViewSet, CompanyAdminMixin):
    def get_queryset(self):

        company_admin = self.ca()

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


class MemberView(viewsets.ModelViewSet, CompanyAdminMixin):
    def get_queryset(self):

        company_admin = self.ca()

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


class BoxRequestView(APIView, CompanyAdminMixin):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """List subsidiaries with active box requests"""
        company_admin = self.ca()

        subsidiary_ids = list(
            Subsidiary.objects.filter(
                box_requests__company_admin=company_admin
            ).values_list("id", flat=True)
        )

        return Response({"subsidiary_ids": subsidiary_ids})

    @transaction.atomic
    def post(self, request):
        """Bulk create box requests for subsidiaries"""
        company_admin = self.ca()

        created_ids = []
        for sub_id in request.data["subsidiary_ids"]:
            subsidiary = get_object_or_404(
                Subsidiary, id=sub_id, company=company_admin.administrated_company
            )

            _, created = BoxRequest.objects.get_or_create(
                company_admin=company_admin, subsidiary=subsidiary
            )
            if created:
                created_ids.append(sub_id)

        return Response(
            {
                "message": f"Created {len(created_ids)} box requests",
                "added_subsidiary_ids": created_ids,
            },
            status=status.HTTP_201_CREATED,
        )


class BoxRequestRemoveView(APIView, CompanyAdminMixin):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        """Bulk delete box requests by subsidiary IDs"""
        company_admin = self.ca()

        # Get actual deleted subsidiary IDs from the box requests
        deleted_subsidiaries = list(
            BoxRequest.objects.filter(
                company_admin=company_admin,
                subsidiary_id__in=request.data["subsidiary_ids"],
            ).values_list("subsidiary_id", flat=True)
        )

        deleted_count, _ = BoxRequest.objects.filter(
            subsidiary_id__in=deleted_subsidiaries
        ).delete()

        return Response(
            {
                "message": f"Deleted {deleted_count} box requests",
                "deleted_subsidiary_ids": deleted_subsidiaries,
            },
            status=status.HTTP_200_OK,
        )


class OrganizationAdminOrganizationUserAttendanceSerializer(serpy.Serializer):
    id = serpy.IntField()
    name = serpy.StrField(call=True)
    nickname = RequestSpecificField(lambda ua, req: ua.userprofile.nickname)
    date_of_challenge_registration = serpy.Field(attr="created")
    email = RequestSpecificField(lambda ua, req: ua.userprofile.user.email)
    telephone = RequestSpecificField(lambda ua, req: ua.userprofile.telephone)
    sex = RequestSpecificField(lambda ua, req: ua.userprofile.sex)
    avatar_url = serpy.Field(call=True)
    approved_for_team = serpy.StrField()
    payment_status = serpy.StrField()
    payment_type = serpy.StrField(call=True)
    payment_category = serpy.StrField(call=True)
    payment_amount = serpy.StrField(call=True)
    discount_coupon = EmptyStrField()
    user_profile_id = RequestSpecificField(lambda ua, req: ua.userprofile.id)


class OrganizationAdminOrganizationTeamsSerializer(serpy.Serializer):
    members_without_paid_entry_fee_by_org_coord = RequestSpecificField(
        lambda team, req: [
            OrganizationAdminOrganizationUserAttendanceSerializer(
                member,
                context={"request": req},
            ).data
            for member in team.members.filter(
                userprofile__user__is_active=True,
                representative_payment__pay_type="fc",
                discount_coupon__isnull=True,
            )
            .exclude(
                payment_status="done",
            )
            .select_related(
                "userprofile__user",
                "team__subsidiary__city",
            )
            .order_by(
                "team__subsidiary__city",
                "userprofile__user__last_name",
                "userprofile__user__first_name",
            )
        ]
    )
    members_with_paid_entry_fee_by_org_coord = RequestSpecificField(
        lambda team, req: [
            OrganizationAdminOrganizationUserAttendanceSerializer(
                member,
                context={"request": req},
            ).data
            for member in team.members.filter(
                userprofile__user__is_active=True,
                representative_payment__pay_type="fc",
                discount_coupon__isnull=True,
                payment_status="done",
            )
            .select_related(
                "userprofile__user",
                "team__subsidiary__city",
            )
            .order_by(
                "team__subsidiary__city",
                "userprofile__user__last_name",
                "userprofile__user__first_name",
            )
        ]
    )
    other_members = RequestSpecificField(
        lambda team, req: [
            OrganizationAdminOrganizationUserAttendanceSerializer(
                member,
                context={"request": req},
            ).data
            for member in team.members.filter(
                userprofile__user__is_active=True,
            )
            .exclude(
                Q(payment_status="done") | Q(payment_status="waiting"),
                representative_payment__pay_type="fc",
                discount_coupon__isnull=True,
            )
            .select_related(
                "userprofile__user",
                "team__subsidiary__city",
            )
            .order_by(
                "team__subsidiary__city",
                "userprofile__user__last_name",
                "userprofile__user__first_name",
            )
        ]
    )

    name = serpy.StrField(required=False)
    id = serpy.IntField()
    icon_url = serpy.Field(call=True)


class OrganizationAdminOrganizationSubsidiariesSerializer(serpy.Serializer):
    teams = SubsidiaryInCampaignField(
        lambda sic, req: [
            OrganizationAdminOrganizationTeamsSerializer(
                team, context={"request": req}
            ).data
            for team in sic.teams
        ]
    )
    id = serpy.IntField()
    street = serpy.StrField(attr="address.street")
    street_number = serpy.IntField(attr="address.street_number")
    city = serpy.StrField()
    icon_url = serpy.Field(call=True)


class OrganizationAdminOrganizationSerializer(serpy.Serializer):
    name = serpy.StrField()
    psc = NullIntField(attr="address.psc")
    street = EmptyStrField(attr="address.street")
    street_number = EmptyStrField(attr="address.street_number")
    recipient = EmptyStrField(attr="address.recipient")
    city = EmptyStrField(attr="address.city")
    ico = NullIntField()
    dic = EmptyStrField()
    active = serpy.BoolField()
    subsidiaries = RequestSpecificField(
        lambda organization, req: [
            OrganizationAdminOrganizationSubsidiariesSerializer(
                sub, context={"request": req}
            ).data
            for sub in organization.subsidiaries.filter(
                teams__campaign__slug=req.subdomain, active=True
            ).distinct()
        ]
    )


class OrganizationAdminOrganizationSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return Company.objects.filter(
            id__in=CompanyAdmin.objects.filter(
                userprofile=self.request.user.userprofile,
                company_admin_approved="approved",
                campaign__slug=self.request.subdomain,
            ).values_list("administrated_company__id", flat=True)
        )

    serializer_class = OrganizationAdminOrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]


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
router.register(
    "organization-coordinator-organization-structure",
    OrganizationAdminOrganizationSet,
    basename="organization-coordinator-organization-structure",
)
