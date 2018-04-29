from django.contrib import admin

from . import models


# Register your models here.
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
