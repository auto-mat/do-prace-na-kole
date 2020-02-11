

from django import forms
from django.db import models

from dpnk.models.trip import Trip, distance_all_modes

from redactor.widgets import RedactorEditor


class CharitativeOrganization(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    campaign = models.ForeignKey('dpnk.Campaign', on_delete=models.CASCADE, null=False, blank=False)

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
