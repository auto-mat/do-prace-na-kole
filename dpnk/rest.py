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

from rest_framework import permissions, routers, serializers, viewsets
from rest_framework.reverse import reverse

from .middleware import get_or_create_userattendance
from .models import City, CommuteMode, Company, Competition, CompetitionResult, Subsidiary, Team, Trip, UserAttendance


class InactiveDayGPX(serializers.ValidationError):
    status_code = 410
    default_code = 'invalid_date'
    default_detail = {'date': "Trip for this day cannot be created/updated. This day is not active for edition"}


class GPXParsingFail(serializers.ValidationError):
    status_code = 400
    default_detail = {"file": "Can't parse GPX file"}


class CompetitionDoesNotExist(serializers.ValidationError):
    status_code = 405
    default_detail = {'competition': "Competition with this slug not found"}


class DistanceMetersSerializer(serializers.IntegerField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        return value / 1000

    def to_representation(self, data):
        value = round(data * 1000)
        return super().to_representation(value)


class TripSerializer(serializers.ModelSerializer):
    distanceMeters = DistanceMetersSerializer(
        required=False,
        min_value=0,
        max_value=1000 * 1000,
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
        required=True,
        source='source_application',
        help_text='Any string identifiing the source application of the track',
    )
    trip_date = serializers.DateField(
        required=False,
        source='date',
        help_text='Date of the trip e.g. "1970-01-23"',
    )
    file = serializers.FileField(
        required=False,
        source='gpx_file',
        help_text='GPX file with the track',
    )

    def is_valid(self, *args, **kwargs):
        request = self.context['request']
        self.user_attendance = request.user_attendance
        if not self.user_attendance:
            self.user_attendance = get_or_create_userattendance(request, request.subdomain)
        return super().is_valid(*args, **kwargs)

    def validate(self, data):
        validated_data = super().validate(data)
        if 'date' in validated_data and not self.user_attendance.campaign.day_active(validated_data['date']):
            raise InactiveDayGPX
        return validated_data

    def create(self, validated_data):
        try:
            instance, _ = Trip.objects.update_or_create(
                user_attendance=self.user_attendance,
                date=validated_data['date'],
                direction=validated_data['direction'],
                defaults=validated_data,
            )
            instance.from_application = True
            instance.save()
        except ValidationError:
            raise GPXParsingFail
        return instance

    class Meta:
        model = Trip
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
            'direction': {'help_text': 'Direction of the trip "trip_to" for trip to work, "trip_from" for trip from work'},
        }


class TripDetailSerializer(TripSerializer):
    class Meta(TripSerializer.Meta):
        extra_kwargs = {}


class TripUpdateSerializer(TripSerializer):
    class Meta(TripSerializer.Meta):
        fields = (
            'id',
            'file',
            'track',
            'commuteMode',
            'durationSeconds',
            'distanceMeters',
            'sourceApplication',
        )


class TripSet(viewsets.ModelViewSet):
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
        return Trip.objects.filter(
            user_attendance__userprofile__user=self.request.user,
            user_attendance__campaign=self.request.campaign,
        )

    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return TripUpdateSerializer
        return TripDetailSerializer if self.action == 'retrieve' else TripSerializer

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
router.register(r'gpx', TripSet, base_name="gpxfile")
# This is disabled, because Abra doesn't cooperate anymore
# router.register(r'competition', CompetitionSet, base_name="competition")
# router.register(r'team', TeamSet, base_name="team")
# router.register(r'subsidiary', SubsidiarySet, base_name="subsidiary")
# router.register(r'company', CompanySet, base_name="company")
# router.register(r'userattendance', UserAttendanceSet, base_name="userattendance")
# router.register(r'result/(?P<competition_slug>.+)', CompetitionResultSet, base_name="result")
