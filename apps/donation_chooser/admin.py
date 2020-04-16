
from adminsortable2.admin import SortableAdminMixin

from django.contrib import admin

from .models import CharitativeOrganization, CharitativeOrganizationForm, UserChoice


@admin.register(CharitativeOrganization)
class CharitativeOrganizdationAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'campaign')
    list_filter = ('campaign',)
    form = CharitativeOrganizationForm
    save_as = True


@admin.register(UserChoice)
class UserChoiceAdmin(admin.ModelAdmin):
    list_display = ('user_attendance', 'charitative_organization')
