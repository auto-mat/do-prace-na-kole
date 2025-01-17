from rest_framework import routers, viewsets, permissions
import drf_serpy as serpy

from .models import (
    UserAttendance,
    CompanyAdmin,
)

from .middleware import get_or_create_userattendance


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


class FeeApprovalSet(viewsets.ReadOnlyModelViewSet, UserAttendanceMixin):
    def get_queryset(self):
        company_admin = CompanyAdmin.objects.get(
            userprofile=self.ua().userprofile.pk,
            campaign__slug=self.request.subdomain,
            company_admin_approved="approved",
        )
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


router = routers.DefaultRouter()
router.register(r"fee-approval", FeeApprovalSet, basename="fee-approval")
