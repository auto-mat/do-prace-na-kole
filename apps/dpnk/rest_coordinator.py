import datetime
from collections import namedtuple

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict

from rest_framework import (
    mixins,
    permissions,
    serializers,
    status,
    viewsets,
)
from rest_framework.exceptions import APIException
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action

import drf_serpy as serpy

from .models import (
    UserAttendance,
    CompanyAdmin,
    Invoice,
    Payment,
    PayUOrderedProduct,
    Status,
    Company,
    Subsidiary,
    Team,
    Campaign,
)
from t_shirt_delivery.models import (
    BoxRequest,
    PackageTransaction,
    SubsidiaryBox,
)
from .models.company import CompanyInCampaign
from .rest import (
    CompaniesDeserializer,
    UserAttendanceSerializer,
    AddressSerializer,
    EmptyStrField,
    NullIntField,
    router,
    RequestSpecificField,
    SubsidiaryInCampaignField,
    UserAttendancePaymentWithRewardSerializer,
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

    ids = serializers.DictField(
        child=serializers.IntegerField(),
        required=True,
    )


class ApprovePaymentsView(APIView, CompanyAdminMixin):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ApprovePaymentsDeserializer(data=request.data)
        if serializer.is_valid():
            ids = serializer.validated_data["ids"]

            company_admin = self.ca()

            users = UserAttendance.objects.filter(
                id__in=list(map(int, ids.keys())),
                team__subsidiary__company=company_admin.administrated_company,
                campaign=company_admin.campaign,
                userprofile__user__is_active=True,
                representative_payment__pay_type="fc",
            ).exclude(
                payment_status="done",
            )

            approved_count = 0
            payments = []
            payu_ordered_products = []
            for user in users:
                payment = user.representative_payment
                payment.status = Status.COMPANY_ACCEPTS
                amount = ids[str(user.id)]
                if payment.amount != amount:
                    payment.amount = amount
                    entry_fee = payment.payu_ordered_product.get(
                        name__icontains="entry fee"
                    )
                    entry_fee.unit_price = amount
                    payu_ordered_products.append(entry_fee)
                else:
                    payment.amount = user.company_admission_fee()
                payment.description = (
                    payment.description
                    + "\nFA %s odsouhlasil dne %s"
                    % (self.request.user.username, datetime.datetime.now())
                )
                payment.save()
                # payments.append(payment)
                approved_count += 1

            # Payment.objects.bulk_update(
            #     payments,
            #     ["status", "amount", "description"],
            # )
            PayUOrderedProduct.objects.bulk_update(
                payu_ordered_products,
                ["unit_price"],
            )
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


class SubsidiaryAddressDeserializer(CompaniesDeserializer):
    class Meta:
        model = Subsidiary
        fields = (
            "address_street",
            "address_street_number",
            "address_psc",
            "address_city",
            "address_recipient",
            "box_addressee_name",
            "box_addressee_telephone",
            "box_addressee_email",
        )


class SubsidiaryView(
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
    CompanyAdminMixin,
):
    def get_queryset(self):

        company_admin = self.ca()

        queryset = Subsidiary.objects.filter(
            company=company_admin.administrated_company,
        )
        return queryset

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return SubsidiarySerializer
        else:
            return SubsidiaryAddressDeserializer

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


class OrganizationAdminOrganizationUserAttendanceSerializer(
    UserAttendancePaymentWithRewardSerializer
):
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
    diploma = EmptyStrField(
        attr="get_diploma_pdf_url",
        call=True,
        required=False,
    )
    t_shirt_size = EmptyStrField()
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
    diploma = EmptyStrField(
        attr="get_diploma_pdf_url",
        call=True,
        required=False,
    )


class OrganizationAdminPackageTransactionSerializer(serpy.Serializer):
    t_shirt_size = EmptyStrField()
    name = serpy.StrField(attr="user_attendance.name", call=True)


class OrganizationAdminOrganizationTeamPackageSerializer(serpy.Serializer):
    dispatched = serpy.BoolField()
    package_transactions = RequestSpecificField(
        lambda team_package, req: [
            OrganizationAdminPackageTransactionSerializer(
                package_transaction, context={"request": req}
            ).data
            for package_transaction in PackageTransaction.objects.filter(
                team_package=team_package, user_attendance__campaign=req.campaign
            )
        ]
    )


class OrganizationAdminOrganizationSubsidiaryBoxSerializer(serpy.Serializer):
    dispatched = serpy.BoolField()
    carrier_identification = EmptyStrField()
    tracking_link = EmptyStrField(call=True)
    modified = serpy.StrField()
    team_packages = RequestSpecificField(
        lambda subsidiary_box, req: [
            OrganizationAdminOrganizationTeamPackageSerializer(
                team_package, context={"request": req}
            ).data
            for team_package in subsidiary_box.teampackage_set.all()
        ]
    )


class OrganizationAdminOrganizationSubsidiariesSerializer(serpy.Serializer):
    teams = SubsidiaryInCampaignField(
        lambda sic, req: [
            OrganizationAdminOrganizationTeamsSerializer(
                team, context={"request": req}
            ).data
            for team in sic.teams
        ]
    )
    boxes = SubsidiaryInCampaignField(
        lambda sic, req: [
            OrganizationAdminOrganizationSubsidiaryBoxSerializer(
                subsidiary_box, context={"request": req}
            ).data
            for subsidiary_box in SubsidiaryBox.objects.filter(
                subsidiary=sic.subsidiary,
                delivery_batch__campaign=req.campaign,
            )
        ]
    )
    id = serpy.IntField()
    name = serpy.StrField(call=True)
    address = AddressSerializer()
    icon_url = serpy.Field(call=True)


class OrganizationAdminOrganizationSerializer(serpy.Serializer):
    name = serpy.StrField()
    address = AddressSerializer()
    ico = NullIntField()
    dic = EmptyStrField()
    active = serpy.BoolField()
    has_filled_contact_information = serpy.BoolField(
        attr="has_filled_contact_information",
        call=True,
    )
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
                can_confirm_payments=True,
                administrated_company__active=True,
            ).values_list("administrated_company__id", flat=True)
        )

    serializer_class = OrganizationAdminOrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]


class OrganizationAdminPaymentSerializer(serpy.Serializer):
    id = serpy.IntField()
    amount = serpy.IntField()
    userprofile_id = RequestSpecificField(
        lambda payment, req: payment.payment_user_attendance.userprofile.id
    )
    payment_status = serpy.IntField()
    pay_type = serpy.StrField()
    pay_category = serpy.StrField()


class OrganizationAdminInvoiceSerializer(serpy.Serializer):
    id = serpy.IntField()
    order_number = EmptyStrField()
    total_amount = NullIntField()
    fakturoid_invoice_url = EmptyStrField()
    exposure_date = EmptyStrField()
    paid_date = EmptyStrField()
    company_pais_benefitial_fee = serpy.BoolField()
    client_note = EmptyStrField()
    payments = RequestSpecificField(
        lambda invoice, req: [
            OrganizationAdminPaymentSerializer(payment, context={"request": req}).data
            for payment in invoice.payment_set.all()
        ]
    )


class OrganizationAdminInvoicesSerializer(serpy.Serializer):
    payments_to_invoice = RequestSpecificField(
        lambda organization, req: [
            OrganizationAdminPaymentSerializer(payment, context={"request": req}).data
            for payment in Payment.objects.filter(
                pay_type="fc",
                status=Status.COMPANY_ACCEPTS,
                user_attendance__team__subsidiary__company=organization,
                user_attendance__campaign__slug=req.subdomain,
            )
        ]
    )
    invoices = RequestSpecificField(
        lambda organization, req: [
            OrganizationAdminInvoiceSerializer(
                payment.invoice, context={"request": req}
            ).data
            for payment in Payment.objects.filter(
                Q(status=Status.INVOICE_MADE) | Q(status=Status.INVOICE_PAID),
                pay_type="fc",
                user_attendance__team__subsidiary__company=organization,
                user_attendance__campaign__slug=req.subdomain,
                invoice__isnull=False,
            ).distinct("invoice_id")
        ]
    )


class OrganizationAdminInvoiceSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return Company.objects.filter(
            id__in=CompanyAdmin.objects.filter(
                userprofile=self.request.user.userprofile,
                company_admin_approved="approved",
                campaign__slug=self.request.subdomain,
                can_confirm_payments=True,
                administrated_company__active=True,
            ).values_list("administrated_company__id", flat=True)
        )

    serializer_class = OrganizationAdminInvoicesSerializer
    permission_classes = [permissions.IsAuthenticated]


class CompanyAddressDeserializer(serializers.Serializer):
    psc = serializers.CharField(required=False)
    street = serializers.CharField(required=False)
    street_number = serializers.CharField(required=False)
    recipient = serializers.CharField(required=False)
    city = serializers.CharField(required=False)


class MakeInvoiceDeserializer(serializers.ModelSerializer):
    payment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
    )
    company_address = CompanyAddressDeserializer(required=False)

    class Meta:
        model = Invoice
        fields = [
            "order_number",
            "client_note",
            "company_pais_benefitial_fee",
            "payment_ids",
            "company_ico",
            "company_dic",
            "telephone",
            "email",
            "country",
            "company_name",
            "anonymize",
            "company_address",
        ]
        extra_kwargs = {
            "order_number": {"required": False},
            "client_note": {"required": False},
            "company_pais_benefitial_fee": {"required": False},
            "company_ico": {"required": False},
            "company_dic": {"required": False},
            "telephone": {"required": False},
            "email": {"required": False},
            "country": {"required": False},
            "company_name": {"required": False},
            "anonymize": {"required": False},
        }


class MakeInvoiceVew(APIView, CompanyAdminMixin):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MakeInvoiceDeserializer(data=request.data)
        if serializer.is_valid():
            order_number = serializer.validated_data.get("order_number")
            client_note = serializer.validated_data.get("client_note")
            company_pais_benefitial_fee = serializer.validated_data.get(
                "company_pais_benefitial_fee"
            )
            payment_ids = serializer.validated_data.get("payment_ids")
            company_ico = serializer.validated_data.get("company_ico")
            company_dic = serializer.validated_data.get("company_dic")
            telephone = serializer.validated_data.get("telephone")
            email = serializer.validated_data.get("email")
            country = serializer.validated_data.get("country")
            company_name = serializer.validated_data.get("company_name")
            anonymize = serializer.validated_data.get("anonymize")
            company_address = serializer.validated_data.get("company_address")

            company_admin = self.ca()
            queryset = {
                "campaign": company_admin.campaign,
                "company": company_admin.administrated_company,
            }

            if company_address:
                CompanyAddress = namedtuple(
                    "CompanyAddress",
                    [
                        "psc",
                        "street",
                        "street_number",
                        "recipient",
                        "city",
                    ],
                    defaults=[
                        None,
                        None,
                        None,
                        None,
                        None,
                    ],
                )
                CompAddr = CompanyAddress()

            if order_number:
                queryset["order_number"] = order_number
            if client_note:
                queryset["client_note"] = client_note
            if company_pais_benefitial_fee:
                queryset["company_pais_benefitial_fee"] = company_pais_benefitial_fee
            if company_ico:
                queryset["company_ico"] = company_ico
            if company_dic:
                queryset["company_dic"] = company_dic
            if telephone:
                queryset["telephone"] = telephone
            if email:
                queryset["email"] = email
            if country:
                queryset["country"] = country
            if company_name:
                queryset["company_name"] = company_name
            if anonymize:
                queryset["anonymize"] = anonymize

            # Custom organization address
            if company_address:
                psc = company_address.get("psc")
                if psc:
                    CompAddr = CompAddr._replace(psc=psc)
                street = company_address.get("street")
                if street:
                    CompAddr = CompAddr._replace(street=street)
                street_number = company_address.get("street_number")
                if street_number:
                    CompAddr = CompAddr._replace(street_number=street_number)
                city = company_address.get("city")
                if city:
                    CompAddr = CompAddr._replace(city=city)
                recipient = company_address.get("recipient")
                if recipient:
                    CompAddr = CompAddr._replace(recipient=recipient)

                queryset["company_address"] = CompAddr._asdict()

            invoice = Invoice(**queryset)
            invoice.save(payment_ids=payment_ids)

            return Response(
                {
                    "invoice_id": invoice.id,
                    "payment_ids": payment_ids,
                },
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


router.register(r"coordinator/fee-approval", FeeApprovalSet, basename="fee-approval")
# router.register(r"approve-payments", ApprovePaymentsView, basename="approve-payments")
# router.register(r"get-attendance", GetAttendanceView, basename="get-attendance")
router.register(
    r"coordinator/subsidiary", SubsidiaryView, basename="subsidiary-coordinator"
)
router.register(
    r"coordinator/subsidiary/(?P<subsidiary_id>\d+)/team",
    TeamView,
    basename="subsidiary-team",
)
router.register(
    r"coordinator/subsidiary/(?P<subsidiary_id>\d+)/team/(?P<team_id>\d+)/member",
    MemberView,
    basename="subsidiary-team-member",
)
router.register(
    "coordinator/organization-structure",
    OrganizationAdminOrganizationSet,
    basename="organization-coordinator-organization-structure",
)
router.register(
    "coordinator/invoices",
    OrganizationAdminInvoiceSet,
    basename="organization-coordinator-invoices",
)
