from selectable.base import ModelLookup
from selectable.registry import registry

from .models import Company


class CompanyLookup(ModelLookup):
    model = Company
    search_fields = ('name__unaccent__icontains',)
    filters = {'active': True}


registry.register(CompanyLookup)
