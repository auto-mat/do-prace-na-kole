from django.contrib import admin
from django.db.models import Q
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _
from dpnk.models import CampaignType
from import_export.admin import ImportExportMixin

from . import models


class CampaignTypeFilter(admin.SimpleListFilter):
    title = _("Campaign type")
    parameter_name = "campaign_type"

    def lookups(self, request, model_admin):
        return [(c.id, c.name) for c in CampaignType.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                Q(campaign_types=self.value()) | Q(campaign_types__isnull=True)
            )


class MyMessagesFilter(admin.SimpleListFilter):
    title = _("Filter my messages")
    parameter_name = "my_messages"

    def lookups(self, request, model_admin):
        return [
            ("my", "My messages"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "my":
            return models.MotivationMessage._get_all_messages(request.user_attendance)


@admin.register(models.MotivationMessage)
class MotivationMessageAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "message_html",
        "note",
        "enabled",
        "get_campaign_types",
        "priority",
        "frequency_min",
        "frequency_max",
        "day_from",
        "day_to",
        "date_from",
        "date_to",
        "team_rank_from",
        "team_rank_to",
        "team_backwards_rank_from",
        "team_backwards_rank_to",
    )
    list_filter = (
        "enabled",
        CampaignTypeFilter,
        MyMessagesFilter,
    )
    list_editable = (
        "enabled",
        "priority",
        "frequency_min",
        "frequency_max",
        "day_from",
        "day_to",
        "date_from",
        "date_to",
        "team_rank_from",
        "team_rank_to",
        "team_backwards_rank_from",
        "team_backwards_rank_to",
    )
    readonly_fields = (
        "author",
        "updated_by",
    )
    save_as = True

    def get_campaign_types(self, obj):
        return ", ".join(c.name for c in obj.campaign_types.all())

    def message_html(self, obj):
        return mark_safe(obj.message)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                "campaign_types",
            )
        )
