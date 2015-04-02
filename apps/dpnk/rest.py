from rest_framework import routers, serializers, viewsets, filters
from models import GpxFile, UserAttendance


class GpxFileSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        user = self.context['request'].user
        subdomain = self.context['request'].subdomain
        user_attendance = UserAttendance.objects.get(userprofile__user=user, campaign__slug=subdomain)
        validated_data['user_attendance'] = user_attendance
        return super(GpxFileSerializer, self).create(validated_data)

    class Meta:
        model = GpxFile
        fields = ('trip_date', 'direction', 'file')


class GpxFileSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return GpxFile.objects.filter(user_attendance__userprofile__user=self.request.user)
    serializer_class = GpxFileSerializer

router = routers.DefaultRouter()
router.register(r'gpx', GpxFileSet, base_name="gpxfile")
