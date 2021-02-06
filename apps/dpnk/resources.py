import types

from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _

from import_export import fields, resources
from import_export.fields import Field

from . import models


class CompanyResource(resources.ModelResource):
    class Meta:
        model = models.Company
        fields = [
            "id",
            "name",
            "ico",
            "dic",
        ]
        export_order = fields


def get_paid_user_attendances_for_company(company, campaign, extra_filter=None):
    queryset = models.UserAttendance.objects.filter(
        campaign=campaign, team__subsidiary__company=company,
    )
    if extra_filter:
        queryset = extra_filter(queryset)
    return [ua for ua in queryset if ua.has_paid()]


def total_paid_participants_factory(campaign):
    def tpp(_, company):
        return str(len(get_paid_user_attendances_for_company(company, campaign)),)

    return tpp


def employer_paid_by_bill_factory(campaign):
    def epbb(_, company):
        return str(
            len(
                get_paid_user_attendances_for_company(
                    company,
                    campaign,
                    lambda qs: qs.filter(representative_payment__pay_type="fc"),
                ),
            ),
        )

    return epbb


def create_company_history_resource():
    campaigns = models.Campaign.objects.all()
    extra_fields = {}
    extra_field_types = {
        "total_paid_participants": total_paid_participants_factory,
        "employer_paid_by_bill": employer_paid_by_bill_factory,
    }
    for ft in extra_field_types:
        for campaign in campaigns:
            extra_fields.update(
                {
                    "{campaign}_{field_type}".format(
                        campaign=campaign.slug, field_type=ft
                    ): (campaign, ft)
                    for campaign in campaigns
                }
            )

    class CompanyHistoryResource(resources.ModelResource):
        class Meta:
            model = models.Company
            fields = ["id", "name", "ico", "dic",] + list(extra_fields.keys())
            export_order = fields

        for field in extra_fields.keys():
            vars()[field] = fields.Field(readonly=True)

    for field_name, (campaign, field_type) in extra_fields.items():
        setattr(
            CompanyHistoryResource,
            "dehydrate_" + field_name,
            extra_field_types[field_type](campaign),
        )

    return CompanyHistoryResource


def create_subsidiary_resource(campaign_slugs):
    campaign_fields = ["user_count_%s" % sl for sl in campaign_slugs]

    class SubsidiaryResource(resources.ModelResource):
        class Meta:
            model = models.Subsidiary
            fields = [
                "id",
                "name",
                "address_street",
                "address_street_number",
                "address_recipient",
                "address_city",
                "address_psc",
                "company__name",
                "city__name",
                "user_count",
                "team_count",
            ] + campaign_fields
            export_order = fields

        name = fields.Field(readonly=True, attribute="name")
        team_count = fields.Field(readonly=True, attribute="team_count")
        user_count = fields.Field(readonly=True)

        def dehydrate_user_count(self, obj):
            return obj.teams.distinct().aggregate(Sum("member_count"))[
                "member_count__sum"
            ]

        for slug in campaign_slugs:
            vars()["user_count_%s" % slug] = fields.Field(readonly=True)

    for slug in campaign_slugs:

        def func(slug, obj):
            return (
                obj.teams.filter(campaign__slug=slug)
                .distinct()
                .aggregate(Sum("member_count"))["member_count__sum"]
            )

        setattr(
            SubsidiaryResource,
            "dehydrate_user_count_%s" % slug,
            types.MethodType(func, slug),
        )

    return SubsidiaryResource


def create_userprofile_resource(campaign_slugs):  # noqa: C901
    campaign_fields = ["user_attended_%s" % sl for sl in campaign_slugs]

    class UserProileResource(resources.ModelResource):
        class Meta:
            model = models.UserProfile
            fields = [
                "id",
                "user",
                "name",
                "email",
                "sex",
                "telephone",
                "language",
                "occupation",
                "occupation_name",
                "age_group",
                "mailing_id",
                "note",
                "ecc_password",
                "ecc_email",
            ] + campaign_fields
            export_order = fields

        name = fields.Field(readonly=True, attribute="name")
        email = fields.Field(readonly=True, attribute="user__email")
        occupation_name = fields.Field(readonly=True, attribute="occupation__name")

        for slug in campaign_slugs:
            vars()["user_attended_%s" % slug] = fields.Field(readonly=True)

    for slug in campaign_slugs:

        def func(slug, obj):
            user_profile = obj.userattendance_set.filter(campaign__slug=slug)
            if user_profile.exists():
                return user_profile.get().payment_status

        setattr(
            UserProileResource,
            "dehydrate_user_attended_%s" % slug,
            types.MethodType(func, slug),
        )

    return UserProileResource


class UserAttendanceResource(resources.ModelResource):
    class Meta:
        model = models.UserAttendance
        fields = [
            "id",
            "campaign",
            "campaign__slug",
            "distance",
            "frequency",
            "trip_length_total",
            "team",
            "team__name",
            "approved_for_team",
            "t_shirt_size",
            "t_shirt_size__name",
            "team__subsidiary__city__name",
            "userprofile",
            "userprofile__language",
            "userprofile__telephone",
            "userprofile__user__id",
            "userprofile__user__first_name",
            "userprofile__user__last_name",
            "userprofile__user__username",
            "userprofile__user__email",
            "userprofile__occupation",
            "userprofile__age_group",
            "subsidiary_name",
            "team__subsidiary__company__name",
            "company_admin_emails",
            "created",
            "payment_date",
            "payment_status",
            "payment_type",
            "payment_amount",
        ]
        export_order = fields

    subsidiary_name = fields.Field(readonly=True, attribute="team__subsidiary__name")
    payment_date = fields.Field(readonly=True, attribute="payment_complete_date")
    payment_status = fields.Field(readonly=True, attribute="payment_status")
    payment_type = fields.Field(
        readonly=True, attribute="representative_payment__pay_type"
    )
    payment_amount = fields.Field(
        readonly=True, attribute="representative_payment__amount"
    )
    company_admin_emails = fields.Field(readonly=True, attribute="company_admin_emails")


class AnswerResource(resources.ModelResource):
    class Meta:
        model = models.Answer
        fields = [
            "id",
            "user_attendance__userprofile__user__first_name",
            "user_attendance__userprofile__user__last_name",
            "user_attendance__userprofile__user__email",
            "user_attendance__userprofile__user__id",
            "user_attendance__userprofile__telephone",
            "user_attendance__userprofile__id",
            "user_attendance__team__name",
            "user_attendance__team__subsidiary__address_street",
            "user_attendance__team__subsidiary__address_street_number",
            "user_attendance__team__subsidiary__address_recipient",
            "user_attendance__team__subsidiary__address_psc",
            "user_attendance__team__subsidiary__address_city",
            "user_attendance__team__subsidiary__company__name",
            "user_attendance__team__subsidiary__city__name",
            "user_attendance__id",
            "points_given",
            "question",
            "question__name",
            "question__text",
            "choices",
            "str_choices",
            "comment",
        ]
        export_order = fields

    str_choices = fields.Field(readonly=True, attribute="str_choices")


class TripResource(resources.ModelResource):
    class Meta:
        model = models.Trip
        fields = [
            "id",
            "user_attendance__userprofile__user__id",
            "user_attendance__userprofile__user__first_name",
            "user_attendance__userprofile__user__last_name",
            "user_attendance__userprofile__user__email",
            "user_attendance",
            "source_application",
            "source_id",
            "date",
            "direction",
            "commute_mode",
            "commute_mode__slug",
            "distance",
            "duration",
            "from_application",
        ]
        export_order = fields


class CompanyAdminResource(resources.ModelResource):
    class Meta:
        model = models.CompanyAdmin
        fields = [
            "userprofile__user",
            "userprofile__user__email",
            "userprofile",
            "userprofile__user__first_name",
            "userprofile__user__last_name",
            "userprofile__telephone",
            "company_admin_approved",
            "can_confirm_payments",
            "will_pay_opt_in",
            "note",
            "sitetree_postfix",
            "motivation_company_admin",
            "campaign",
            "administrated_company__name",
            "administrated_company__id",
        ]


class InvoiceResource(resources.ModelResource):
    campaign_name = Field(column_name=_("campaign_name"))

    class Meta:
        model = models.Invoice
        fields = [
            "company__name",
            "created",
            "exposure_date",
            "taxable_date",
            "payback_date",
            "paid_date",
            "total_amount",
            "payments_count",
            "campaign_name",
            "sequence_number",
            "order_number",
            "company__ico",
            "company__dic",
            "company_pais_benefitial_fee",
            "company__address_street",
            "company__address_street_number",
            "company__address_recipient",
            "company__address_psc",
            "company__address_city",
            "company_admin_telephones",
            "company_admin_emails",
        ]
        export_order = fields

    payments_count = fields.Field(readonly=True, attribute="payments_count")
    company_admin_emails = fields.Field(readonly=True, attribute="company_admin_emails")
    company_admin_telephones = fields.Field(
        readonly=True, attribute="company_admin_telephones"
    )

    def dehydrate_campaign_name(self, result):
        return result.campaign.display_name()


class CompetitionResultResource(resources.ModelResource):
    public_name = Field(column_name=_("Přezdívka"))
    first_name = Field(column_name=_("Jméno"))
    last_name = Field(column_name=_("Příjmení"))
    competition__name = Field(column_name=_("Soutěž"), attribute="competition__name")
    team = Field(column_name=_("Tým"))
    company = Field(column_name=_("Organizace"))
    subsidiary = Field(column_name=_("Pobočka"))
    sequence_range = Field(column_name=_("Pořadí"))

    class Meta:
        model = models.CompetitionResult
        fields = [
            "public_name",
            "first_name",
            "last_name",
            "competition__name",
            "team",
            "subsidiary",
            "company",
            "result",
            "result_divident",
            "result_divisor",
            "sequence_range",
        ]
        export_order = ("competition", "result", "company")
        export_order = fields

    def __init__(self, include_personal_info=False):
        self.include_personal_info = include_personal_info
        super().__init__()

    def dehydrate_public_name(self, result):
        if result.user_attendance:
            return result.user_attendance.name()

    def dehydrate_first_name(self, result):
        if self.include_personal_info and result.user_attendance:
            return result.user_attendance.first_name()

    def dehydrate_last_name(self, result):
        if self.include_personal_info and result.user_attendance:
            return result.user_attendance.last_name()

    def dehydrate_team(self, result):
        return result.get_team().name

    def dehydrate_subsidiary(self, result):
        if self.include_personal_info:
            return result.get_team().subsidiary.name()

    def dehydrate_company(self, result):
        return result.get_team().subsidiary.company.name

    def dehydrate_sequence_range(self, result):
        return str(result.get_sequence_range())

    def get_export_headers(self):
        headers = []
        for field in self.get_fields():
            model_fields = self.Meta.model._meta.get_fields()
            header = next(
                (x.verbose_name for x in model_fields if x.name == field.column_name),
                field.column_name,
            )
            headers.append(str(header))
        return headers


class AdminCompetitionResultResource(CompetitionResultResource):
    def __init__(self):
        return super().__init__(include_personal_info=True)
