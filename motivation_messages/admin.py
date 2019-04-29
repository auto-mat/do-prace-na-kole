from django.contrib import admin
from django.utils.html import mark_safe

from import_export.admin import ImportExportMixin

from . import models


@admin.register(models.MotivationMessage)
class MotivationMessageAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'message_html',
        'note',
        'enabled',
        'priority',
        'frequency_min',
        'frequency_max',
        'day_from',
        'day_to',
        'date_from',
        'date_to',
        'team_rank_from',
        'team_rank_to',
        'team_backwards_rank_from',
        'team_backwards_rank_to',
    )
    list_editable = (
        'enabled',
        'priority',
        'frequency_min',
        'frequency_max',
        'day_from',
        'day_to',
        'date_from',
        'date_to',
        'team_rank_from',
        'team_rank_to',
        'team_backwards_rank_from',
        'team_backwards_rank_to',
    )
    readonly_fields = (
        'author',
        'updated_by',
    )

    def message_html(self, obj):
        return mark_safe(obj.message)
