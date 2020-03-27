from rest_framework import routers, serializers, viewsets

from .models import CharitativeOrganization


class CharitativeOrganizationSerializer(serializers.ModelSerializer):
    ridden_distance = serializers.ReadOnlyField(source='get_ridden_distance')

    class Meta:
        model = CharitativeOrganization
        fields = (
            'name',
            'description',
            'ridden_distance',
            'image',
            'icon',
        )


class CharitativeOrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CharitativeOrganization.objects.all()
    serializer_class = CharitativeOrganizationSerializer


organization_router = routers.DefaultRouter()
organization_router.register(r'charitative_organization', CharitativeOrganizationViewSet, basename="charitative_organization")
