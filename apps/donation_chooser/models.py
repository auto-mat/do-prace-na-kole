

from django import forms
from django.db import models
from django.utils.html import escape, format_html

from dpnk.models.trip import Trip, distance_all_modes

from redactor.widgets import RedactorEditor


def get_charitative_results_column(user_profile):
    try:
        charitative_organization = user_profile.charitative_choice.charitative_organization
    except AttributeError:
        charitative_organization = None
    if charitative_organization:
        column_html = ""
        if charitative_organization.icon:
            column_html += format_html(
                "<img class='donation-results-logo' src='{}'>",
                escape(charitative_organization.icon.url),
            )
        column_html += format_html(
            "<div class='donation-results-name'>{}</div>",
            escape(charitative_organization.name),
        )
        return column_html


class CharitativeOrganization(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    campaign = models.ForeignKey('dpnk.Campaign', on_delete=models.CASCADE, null=False, blank=False)
    image = models.ImageField(upload_to='charitative_organization/image', null=True, blank=True)
    icon = models.ImageField(upload_to='charitative_organization/image', null=True, blank=True)

    def get_ridden_distance(self):
        return distance_all_modes(
            Trip.objects.filter(
                user_attendance__charitative_choice__charitative_organization=self,
            ),
            self.campaign,
        )

    def __str__(self):
        return self.name


class CharitativeOrganizationForm(forms.ModelForm):
    class Meta:
        model = CharitativeOrganization
        exclude = ()
        widgets = {
            'description': RedactorEditor(),
        }


class UserChoice(models.Model):
    user_attendance = models.OneToOneField(
        'dpnk.UserAttendance',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='charitative_choice',
    )
    charitative_organization = models.ForeignKey(
        'CharitativeOrganization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
