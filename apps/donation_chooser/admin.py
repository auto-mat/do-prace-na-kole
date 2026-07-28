from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import CharitativeOrganization, CharitativeOrganizationForm, UserChoice


@admin.register(CharitativeOrganization)
class CharitativeOrganizdationAdmin(SortableAdminMixin, admin.ModelAdmin):
    title = _("Charitativní organizace")
    list_display = ("name", "campaign")
    list_filter = ("campaign",)
    form = CharitativeOrganizationForm
    save_as = True


@admin.register(UserChoice)
class UserChoiceAdmin(admin.ModelAdmin):
    title = _("Uživatelská volba")
    list_display = ("user_attendance", "charitative_organization")
