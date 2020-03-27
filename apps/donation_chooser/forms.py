from django import forms
from django.utils.html import format_html, mark_safe
from django.utils.translation import ugettext_lazy as _

from dpnk.forms import CampaignMixin, SubmitMixin

from .models import CharitativeOrganization, UserChoice


class CharitativeOrganizationChooserForm(CampaignMixin, SubmitMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['charitative_organization'].empty_label = None
        self.fields['charitative_organization'].label = _("Vyberte charitativní orgazizaci kterou podpoříte svými cestami")
        self.fields['charitative_organization'].choices = [
            (
                c.id,
                format_html(
                    "<img class='donation-icon' src='{}'/>"
                    "<div class='donation-heading'>{}</div>"
                    "<p class='donation-description'>"
                    "<img class='donation-image' src='{}'/>"
                    "{}"
                    "</p>",
                    c.icon.url,
                    c.name,
                    c.image.url,
                    mark_safe(c.description),
                ),
            ) for c in CharitativeOrganization.objects.filter(campaign=self.campaign)
        ]

    class Meta:
        model = UserChoice
        fields = (
            'charitative_organization',
        )
        widgets = {
            'charitative_organization': forms.RadioSelect,
        }
