

from django.contrib import admin

from .models import CharitativeOrganization, CharitativeOrganizationForm, UserChoice


@admin.register(CharitativeOrganization)
class CharitativeOrganizdationAdmin(admin.ModelAdmin):
    list_display = ('name', 'campaign')
    list_filter = ('campaign',)
    form = CharitativeOrganizationForm


@admin.register(UserChoice)
class UserChoiceAdmin(admin.ModelAdmin):
    list_display = ('user_attendance', 'charitative_organization')
