from rest_framework import routers, serializers, viewsets, filters
from rest_framework.exceptions import APIException
from models import GpxFile, UserAttendance
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError


class DuplicateGPX(APIException):
    status_code = 409
    default_detail ="GPX for this day and trip already uploaded"


class GPXParsingFail(APIException):
    status_code = 400
    default_detail ="Can't parse GPX file"


class GpxFileSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        user = self.context['request'].user
        subdomain = self.context['request'].subdomain
        user_attendance = UserAttendance.objects.get(userprofile__user=user, campaign__slug=subdomain)
        validated_data['user_attendance'] = user_attendance
        try:
            instance = GpxFile(**validated_data)
            instance.clean()
            instance.track = instance.track_clean
            instance.save()
        except IntegrityError:
            raise DuplicateGPX
        except ValidationError:
            raise GPXParsingFail
        return instance

    class Meta:
        model = GpxFile
        fields = ('trip_date', 'direction', 'file')
        read_only_fields = ('track',)


class GpxFileSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return GpxFile.objects.filter(user_attendance__userprofile__user=self.request.user)
    serializer_class = GpxFileSerializer

router = routers.DefaultRouter()
router.register(r'gpx', GpxFileSet, base_name="gpxfile")
