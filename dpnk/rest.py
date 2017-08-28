# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2015 o.s. Auto*Mat
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from rest_framework import permissions, routers, serializers, viewsets
from rest_framework.exceptions import APIException
from rest_framework.reverse import reverse

from .models import City, CommuteMode, Company, Competition, CompetitionResult, GpxFile, Subsidiary, Team, Trip, UserAttendance


class DuplicateGPX(APIException):
    status_code = 409
    default_detail = "GPX for this day and trip already uploaded"


class GPXParsingFail(APIException):
    status_code = 400
    default_detail = "Can't parse GPX file"


class CompetitionDoesNotExist(APIException):
    status_code = 405
    default_detail = "Competition with this slug not found"


class GpxFileSerializer(serializers.ModelSerializer):
    distanceMeters = serializers.IntegerField(
        required=False,
        min_value=0,
        source='distance',
        help_text='Distance in meters. If not set, distance will be calculated from the track',
    )
    durationSeconds = serializers.IntegerField(
        required=False,
        min_value=0,
        source='duration',
        help_text='Duration of track in seconds',
    )
    commuteMode = serializers.SlugRelatedField(
        many=False,
        required=False,
        slug_field='slug',
        source='commute_mode',
        queryset=CommuteMode.objects.all(),
        help_text='Transport mode of the trip',
    )
    sourceApplication = serializers.CharField(
        required=False,
        source='source_application',
        help_text='Any string identifiing the source application of the track',
    )

    def create(self, validated_data):
        validated_data['user_attendance'] = self.context['request'].user_attendance
        try:
            instance = GpxFile(**validated_data)
            instance.clean()
            if hasattr(instance, 'track_clean'):
                instance.track = instance.track_clean
            instance.from_application = True
            instance.save()
        except IntegrityError:
            raise DuplicateGPX
        except ValidationError:
            raise GPXParsingFail
        return instance

    class Meta:
        model = GpxFile
        fields = (
            'id',
            'trip_date',
            'direction',
            'file',
            'track',
            'commuteMode',
            'durationSeconds',
            'distanceMeters',
            'sourceApplication',
        )
        extra_kwargs = {
            'track': {
                'write_only': True,
                'help_text': 'Track in GeoJSON MultiLineString format',
            },
            'file': {'help_text': 'GPX file with the track'},
            'trip_date': {'help_text': 'Date of the trip e.g. "1970-01-23"'},
            'direction': {'help_text': 'Direction of the trip "trip_to" for trip to work, "trip_from" for trip from work'},
        }


class GpxFileDetailSerializer(GpxFileSerializer):
    class Meta(GpxFileSerializer.Meta):
        extra_kwargs = {}


class GpxFileSet(viewsets.ModelViewSet):
    """
    Documentation: https://www.dopracenakole.cz/rest-docs/

    get:
    Return a list of all tracks for logged user.

    get on /rest/gpx/{id}:
    Return track detail including a track geometry.

    post:
    Create a new track instance. Track can be sent ether by GPX file (file parameter) or in GeoJSON format (track parameter).
    """

    def get_queryset(self):
        return GpxFile.objects.filter(user_attendance__userprofile__user=self.request.user)

    def get_serializer_class(self):
        return GpxFileDetailSerializer if self.action == 'retrieve' else GpxFileSerializer

    permission_classes = [permissions.IsAuthenticated]


class CompetitionSerializer(serializers.HyperlinkedModelSerializer):
    results = serializers.SerializerMethodField()

    class Meta:
        model = Competition
        fields = ('id', 'name', 'slug', 'competitor_type', 'competition_type', 'url', 'results')

    def get_results(self, obj):
        return reverse("result-list", kwargs={"competition_slug": obj.slug}, request=self.context['request'])


class CompetitionSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return Competition.objects.filter(campaign__slug=self.request.subdomain)
    serializer_class = CompetitionSerializer
    permission_classes = [permissions.AllowAny]


class TripSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Trip
        fields = ('id', 'date', 'direction', 'commute_mode', 'distance')


class TripSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return Trip.objects.filter(user_attendance__campaign__slug=self.request.subdomain)
    serializer_class = TripSerializer
    permission_classes = [permissions.AllowAny]


class CitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = City
        fields = ('id', 'name',)


class CompanySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Company
        fields = ('id', 'name',)


class CompanySet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return Company.objects.filter(subsidiaries__teams__campaign__slug=self.request.subdomain, active=True).distinct()
    serializer_class = CompanySerializer
    permission_classes = [permissions.AllowAny]


class SubsidiarySerializer(serializers.HyperlinkedModelSerializer):
    city = CitySerializer(read_only=True)

    class Meta:
        model = Subsidiary
        fields = ('id', 'address_street', 'company', 'city')


class SubsidiarySet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return Subsidiary.objects.filter(teams__campaign__slug=self.request.subdomain, active=True).distinct()
    serializer_class = SubsidiarySerializer
    permission_classes = [permissions.AllowAny]


class UserAttendanceSerializer(serializers.HyperlinkedModelSerializer):
    user_trips = TripSerializer(many=True, read_only=True)

    class Meta:
        model = UserAttendance
        fields = ('id', 'name', 'team', 'user_trips', 'frequency', 'trip_length_total')


class UserAttendanceSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return UserAttendance.objects.filter(campaign__slug=self.request.subdomain).select_related('userprofile__user')
    serializer_class = UserAttendanceSerializer
    permission_classes = [permissions.AllowAny]


class TeamSerializer(serializers.HyperlinkedModelSerializer):
    members = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='userattendance-detail',
    )

    class Meta:
        model = Team
        fields = ('id', 'name', 'subsidiary', 'members', 'get_frequency', 'get_length')


class TeamSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return Team.objects.filter(campaign__slug=self.request.subdomain)
    serializer_class = TeamSerializer
    permission_classes = [permissions.AllowAny]


class CompetitionResultSerializer(serializers.HyperlinkedModelSerializer):
    user_attendance = serializers.CharField(read_only=True)
    company = serializers.CharField(read_only=True)

    class Meta:
        model = CompetitionResult
        fields = ('id', 'user_attendance', 'team', 'company', 'competition', 'result')


class CompetitionResultSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        competition_slug = self.kwargs['competition_slug']
        try:
            competition = Competition.objects.get(slug=competition_slug)
        except Competition.DoesNotExist:
            raise CompetitionDoesNotExist
        return competition.get_results().select_related('team')
    serializer_class = CompetitionResultSerializer
    permission_classes = [permissions.AllowAny]


router = routers.DefaultRouter()
router.register(r'gpx', GpxFileSet, base_name="gpxfile")
# This is disabled, because Abra doesn't cooperate anymore
# router.register(r'competition', CompetitionSet, base_name="competition")
# router.register(r'team', TeamSet, base_name="team")
# router.register(r'subsidiary', SubsidiarySet, base_name="subsidiary")
# router.register(r'company', CompanySet, base_name="company")
# router.register(r'userattendance', UserAttendanceSet, base_name="userattendance")
# router.register(r'result/(?P<competition_slug>.+)', CompetitionResultSet, base_name="result")
