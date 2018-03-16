from django.utils.translation import ugettext_lazy as _

from selectable.base import ModelLookup
from selectable.registry import registry

from .models import Company


class CompanyLookup(ModelLookup):
    model = Company
    search_fields = (
        'name__unaccent__icontains',
        'name__unaccent__trigram_similar',
        'ico',
        'address_street__unaccent__icontains',
    )
    filters = {'active': True}

    def get_item_label(self, company):
        if company.ico:
            return _("%s (ičo: %s)") % (company.name, company.ico)
        else:
            return company.name


registry.register(CompanyLookup)
