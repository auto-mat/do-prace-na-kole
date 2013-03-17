# downloaded from  http://djangosnippets.org/snippets/2887/
from django.contrib import admin
from django.db import models

def getter_for_related_field(name, admin_order_field=None, short_description=None):
    """
        Create a function that can be attached to a ModelAdmin to use as a list_display field, e.g:
        client__name = getter_for_related_field('client__name', short_description='Client')
    """
    related_names = name.split('__')
    def getter(self, obj):
        for related_name in related_names:
            obj = getattr(obj, related_name)
        return obj
    getter.admin_order_field = admin_order_field or name
    getter.short_description = short_description or related_names[-1].title().replace('_',' ')
    return getter

class RelatedFieldAdminMetaclass(admin.ModelAdmin.__metaclass__):
    """
        Metaclass used by RelatedFieldAdmin to handle fetching of related field values.
        We have to do this as a metaclass because Django checks that list_display fields are supported by the class.
    """
    def __getattr__(self, name):
        if '__' in name:
            getter = getter_for_related_field(name)
            setattr(self, name, getter) # cache so we don't have to do this again
            return getter
        raise AttributeError # let missing attribute be handled normally

class RelatedFieldAdmin(admin.ModelAdmin):
    """
        Version of ModelAdmin that can use related fields in list_display, e.g.:
        list_display = ('address__city', 'address__country__country_code')
    """
    __metaclass__ = RelatedFieldAdminMetaclass
    def queryset(self, request):
        qs = super(RelatedFieldAdmin, self).queryset(request)

        # include all related fields in queryset
        select_related = [field.rsplit('__',1)[0] for field in self.list_display if '__' in field]

        # Include all foreign key fields in queryset.
        # This is based on ChangeList.get_query_set().
        # We have to duplicate it here because select_related() only works once.
        # Can't just use list_select_related because we might have multiple__depth__fields it won't follow.
        model = qs.model
        for field_name in self.list_display:
            try:
                field = model._meta.get_field(field_name)
            except models.FieldDoesNotExist:
                continue
            if isinstance(field.rel, models.ManyToOneRel):
                select_related.append(field_name)

        return qs.select_related(*select_related)
