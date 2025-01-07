from rest_framework import routers, serializers, viewsets

from .models import CharitativeOrganization

import drf_serpy as serpy


# dup
class OptionalImageField(serpy.ImageField):
    def to_value(self, value):
        # if value is None:
        if not value:
            return None
        return super().to_value(value)


class CharitativeOrganizationSerializer(serpy.Serializer):
    ridden_distance = serpy.Field(attr="get_ridden_distance", call=True)
    name = serpy.StrField()
    description = serpy.StrField()
    image = OptionalImageField()
    icon = OptionalImageField()


class CharitativeOrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CharitativeOrganization.objects.all()
    serializer_class = CharitativeOrganizationSerializer


organization_router = routers.DefaultRouter()
organization_router.register(
    r"charitative_organization",
    CharitativeOrganizationViewSet,
    basename="charitative_organization",
)
