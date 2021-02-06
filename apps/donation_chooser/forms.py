from django import forms
from django.utils.html import format_html, mark_safe

from dpnk.forms import CampaignMixin, SubmitMixin

from .models import CharitativeOrganization, UserChoice


class CharitativeOrganizationChooserForm(CampaignMixin, SubmitMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["charitative_organization"].empty_label = None
        self.fields["charitative_organization"].label = ""
        self.fields["charitative_organization"].choices = [
            (
                c.id,
                format_html(
                    "<div class='donation-heading'>"
                    "<img class='donation-icon' src='{}'/>"
                    "<h4 class='donation-name'>"
                    "{}"
                    "</h4>"
                    "</div>"
                    "<p class='donation-description'>"
                    "<img class='donation-image' src='{}'/>"
                    "{}"
                    "</p>",
                    c.icon.url if c.icon else "",
                    c.name,
                    c.image.url if c.image else "",
                    mark_safe(c.description),
                ),
            )
            for c in CharitativeOrganization.objects.filter(campaign=self.campaign)
        ]

    class Meta:
        model = UserChoice
        fields = (
            # black
            "charitative_organization",
        )
        widgets = {
            "charitative_organization": forms.RadioSelect,
        }
