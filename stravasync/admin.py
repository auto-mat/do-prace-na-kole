from django.contrib import admin

from . import models
from . import tasks


def sync(modeladmin, request, queryset):
    for stravaaccount in queryset:
        tasks.sync(stravaaccount.id, manual_sync=False)


@admin.register(models.StravaAccount)
class StravaAccountAdmin(admin.ModelAdmin):
    raw_id_fields = (
        'user',
    )

    list_display = (
        'user',
        'strava_username',
        'first_name',
        'last_name',
        'last_sync_time',
        'user_sync_count',
        'access_token',
    )

    actions = [sync, ]
