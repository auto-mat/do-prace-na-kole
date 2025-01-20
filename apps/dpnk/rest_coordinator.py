from rest_framework import routers, viewsets, permissions, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import drf_serpy as serpy

from .models import (
    UserAttendance,
    CompanyAdmin,
    Payment,
    Status,
)

from .middleware import get_or_create_userattendance
import datetime


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
    def post(self, request, *args, **kwargs):
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


router = routers.DefaultRouter()
router.register(r"fee-approval", FeeApprovalSet, basename="fee-approval")
# router.register(r"approve-payments", ApprovePaymentsView, basename="approve-payments")
