from ajax_select import register, LookupChannel
from .models import Company


@register('companies')
class TagsLookup(LookupChannel):
    model = Company

    def check_auth(self, request):
        return True

    def get_query(self, q, request):
        query = Company.objects.filter(active=True, name__unaccent__icontains=q)
        if len(q) < 3:
            return query[:10]
        return query

    def format_item_display(self, item):
        return u"<span class='tag'>%s</span>" % item.name
