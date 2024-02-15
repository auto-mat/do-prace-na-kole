from django.conf import settings
from django.contrib import admin

from . import models
from . import tasks


def sync(modeladmin, request, queryset):
    for stravaaccount in queryset:
        tasks.sync(stravaaccount.id, manual_sync=False)


def clear_errors(modeladmin, request, queryset):
    for stravaaccount in queryset:
        stravaaccount.errors = ""
        stravaaccount.save()


@admin.register(models.StravaAccount)
class StravaAccountAdmin(admin.ModelAdmin):
    raw_id_fields = ("user",)

    search_fields = (
        f"user__username__{settings.ADMIN_SEARCH_FIELD_LOOKUP}",
        f"user__first_name__{settings.ADMIN_SEARCH_FIELD_LOOKUP}",
        f"strava_username__{settings.ADMIN_SEARCH_FIELD_LOOKUP}",
        f"first_name__{settings.ADMIN_SEARCH_FIELD_LOOKUP}",
        f"last_name__{settings.ADMIN_SEARCH_FIELD_LOOKUP}",
    )

    list_display = (
        "user",
        "strava_username",
        "first_name",
        "last_name",
        "last_sync_time",
        "user_sync_count",
        "access_token",
        "get_failed",
    )

    def get_failed(self, obj):
        if obj.errors:
            return "❌Failed"
        else:
            return "Synced"

    actions = [
        sync,
    ]

    list_filter = ("errors",)
