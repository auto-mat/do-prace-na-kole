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
import time

# TODO re-enable or fix denorm
# import denorm

from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import F, Window
from django.db.models.functions import DenseRank
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_page

from allauth.account.utils import has_verified_email
from donation_chooser.rest import organization_router

from drf_extra_fields.geo_fields import PointField

from memoize import mproperty
from notifications.models import Notification

import photologue

from rest_framework import mixins, permissions, routers, serializers, viewsets

from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.views import APIView

from .middleware import get_or_create_userattendance
from .models import (
    Address,
    Campaign,
    CampaignType,
    City,
    CityInCampaign,
    CommuteMode,
    Company,
    Competition,
    CompetitionResult,
    LandingPageIcon,
    Phase,
    Subsidiary,
    Team,
    Trip,
    UserAttendance,
)
from .models.company import Company, CompanyInCampaign
from .models.subsidiary import SubsidiaryInCampaign
from .util import get_all_logged_in_users

from photologue.models import Photo
from stravasync.models import StravaAccount

import drf_serpy as serpy

from django.contrib.gis.geos import GEOSGeometry
from django.utils.encoding import smart_str

import json
from rest_framework import status

organization_types = [org_type[0] for org_type in Company.ORGANIZATION_TYPE]


class OptionalImageField(serpy.ImageField):
    def to_value(self, value):
        if not value:
            return None
        return super().to_value(value)


class GeometryField(serpy.Field):
    def to_value(self, value):
        if value is None:
            return value

        if value.geojson:
            geojson = json.loads(value.geojson)
        else:
            geojson = {"type": value.geom_type, "coordinates": []}
        return geojson


class PointField(serpy.Field):
    def __init__(self, *args, **kwargs):
        self.str_points = kwargs.pop("str_points", False)
        self.srid = kwargs.pop("srid", None)
        self.format = kwargs.pop("format", "latlon")

        if self.format not in ["latlon", "coords"]:
            raise ValueError(f"Unsupported format: {self.format}")

        super(PointField, self).__init__(*args, **kwargs)

    def to_value(self, value):
        if value is None:
            return value

        if isinstance(value, GEOSGeometry):
            if self.format == "coords":
                value = {"coordinates": [value.x, value.y], "type": "Point"}

            elif self.format == "latlon":
                value = {"latitude": value.y, "longitude": value.x}
        if self.str_points:
            if self.format == "coords":
                # 'location': {'coordinates': [14.644775, 50.104139],'type': 'Point'}
                value = {
                    "coordinates": [value.pop("longitude"), value.pop("latitude")],
                    "type": "Point",
                }
            elif self.format == "latlon":
                value["longitude"] = smart_str(value.pop("longitude"))
                value["latitude"] = smart_str(value.pop("latitude"))

        return value


class HyperlinkedField(serpy.Field):
    getter_takes_serializer = True

    def __init__(self, view_name, **kwargs):
        self.view_name = view_name
        super().__init__(**kwargs)

    def as_getter(self, serializer_field_name, serializer_cls):
        if self.attr == "":
            getter = lambda instance: instance
        else:
            getter = serializer_cls.default_getter(self.attr or serializer_field_name)
        return lambda serializer, instance: self.to_value(
            (getter(instance), serializer.context)
        )

    def to_value(self, value):
        object, context = value

        # Fetch the request from the context
        request = context.get("request")

        return self.get_url(object, request)

    def get_url(self, object, request):
        if object is None:
            return None

        # Generate the relative URL
        relative_url = reverse(self.view_name, kwargs={"pk": object.id})

        # Generate the fully qualified URL
        return request.build_absolute_uri(relative_url)


class RequestSpecificField(serpy.Field):
    getter_takes_serializer = True

    def __init__(self, method, *args, **kwargs):
        self.method = method
        return super().__init__(*args, **kwargs)

    def as_getter(self, serializer_field_name, serializer_cls):
        return lambda serializer, instance: self.to_value(
            (instance, serializer.context)
        )

    def to_value(self, value):
        object, context = value
        return self.method(object, context["request"])


class UserAttendanceMixin:
    def ua(self):
        ua = self.request.user_attendance
        if not ua:
            ua = get_or_create_userattendance(self.request, self.request.subdomain)
        return ua


class InactiveDayGPX(serializers.ValidationError):
    status_code = 410
    default_code = "invalid_date"
    default_detail = {
        "date": "Trip for this day cannot be created/updated. This day is not active for edition"
    }


class GPXParsingFail(serializers.ValidationError):
    status_code = 400
    default_detail = {"file": "Can't parse GPX file"}


class TripAlreadyExists(serializers.ValidationError):
    status_code = 400
    default_detail = {
        "date": "Trip already exists",
        "direction": "Trip already exists.",
    }


class CompetitionDoesNotExist(serializers.ValidationError):
    status_code = 405
    default_detail = {"competition": "Competition with this slug not found"}


class DistanceMetersDeserializer(serializers.IntegerField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        return value / 1000

    def to_representation(self, data):
        value = round(data * 1000)
        return super().to_representation(value)


class DistanceMetersSerializer(serpy.IntField):
    def to_value(self, data):
        value = round(data * 1000)
        return super().to_value(value)


class MinimalTripDeserializer(serializers.ModelSerializer):
    distanceMeters = DistanceMetersDeserializer(
        required=False,
        min_value=0,
        max_value=1000 * 1000,
        source="distance",
        help_text="Distance in meters. If not set, distance will be calculated from the track",
    )
    durationSeconds = serializers.IntegerField(
        required=False,
        min_value=0,
        source="duration",
        help_text="Duration of track in seconds",
    )
    commuteMode = serializers.SlugRelatedField(
        many=False,
        required=False,
        slug_field="slug",
        source="commute_mode",
        queryset=CommuteMode.objects.all(),
        help_text="Transport mode of the trip",
    )
    sourceApplication = serializers.CharField(
        required=True,
        source="source_application",
        help_text="Any string identifiing the source application of the track",
    )
    trip_date = serializers.DateField(
        required=False,
        source="date",
        help_text='Date of the trip e.g. "1970-01-23"',
    )


class MinimalTripSerializer(serpy.Serializer):
    distanceMeters = DistanceMetersSerializer(
        required=False,
        # min_value=0,
        # max_value=1000 * 1000,
        attr="distance",
        # help_text="Distance in meters. If not set, distance will be calculated from the track",
    )
    durationSeconds = serpy.IntField(
        required=False,
        # min_value=0,
        attr="duration",
        # help_text="Duration of track in seconds",
    )
    commuteMode = serpy.StrField(
        # many=False,
        required=False,
        # slug_field="slug",
        attr="commute_mode.slug",
        # queryset=CommuteMode.objects.all(),
        # help_text="Transport mode of the trip",
    )
    sourceApplication = serpy.StrField(
        required=False,
        attr="source_application",
        # help_text="Any string identifiing the source application of the track",
    )
    trip_date = serpy.DateField(
        required=False,
        attr="date",
        # help_text='Date of the trip e.g. "1970-01-23"',
    )


class TripDeserializer(MinimalTripDeserializer):
    sourceId = serializers.CharField(
        required=False,
        source="source_id",
        help_text="Any string identifiing the id in the source application",
    )
    file = serializers.FileField(
        required=False,
        source="gpx_file",
        help_text="GPX file with the track",
    )
    description = serializers.CharField(
        required=False, help_text="Description of the trip as input by user"
    )

    def is_valid(self, *args, **kwargs):
        request = self.context["request"]
        self.user_attendance = request.user_attendance
        if not self.user_attendance:
            self.user_attendance = get_or_create_userattendance(
                request, request.subdomain
            )
        return super().is_valid(*args, **kwargs)

    def validate(self, data):
        validated_data = super().validate(data)
        if "date" in validated_data and not self.user_attendance.campaign.day_recent(
            validated_data["date"]
        ):
            raise InactiveDayGPX
        return validated_data

    def create(self, validated_data):
        try:
            Trip.objects.filter(
                user_attendance=self.user_attendance,
                date=validated_data["date"],
                direction=validated_data["direction"],
            ).delete()
            validated_data["user_attendance"] = self.user_attendance
            validated_data["from_application"] = True
            instance = Trip.objects.create(**validated_data)
        except ValidationError:
            raise GPXParsingFail
        except IntegrityError:
            raise TripAlreadyExists
        return instance

    class Meta:
        model = Trip
        fields = (
            "id",
            "trip_date",
            "direction",
            "file",
            "track",
            "commuteMode",
            "durationSeconds",
            "distanceMeters",
            "sourceApplication",
            "sourceId",
            "description",
        )
        extra_kwargs = {
            "track": {
                "write_only": True,
                "help_text": "Track in GeoJSON MultiLineString format",
            },
            "direction": {
                "help_text": 'Direction of the trip "trip_to" for trip to work, "trip_from" for trip from work'
            },
        }


class TripSerializer(MinimalTripSerializer):
    sourceId = serpy.StrField(
        required=False,
        attr="source_id",
        # help_text="Any string identifiing the id in the source application",
    )

    file = RequestSpecificField(
        lambda trip, req: req.build_absolute_uri(trip.gpx_file.file.url)
        if trip.gpx_file
        else None,
        required=False,
        # attr="gpx_file",
        # help_text="GPX file with the track",
    )

    description = serpy.StrField(
        required=False,
        # help_text="Description of the trip as input by user"
    )

    id = serpy.IntField()
    direction = serpy.StrField(required=False)
    track = GeometryField(required=False)


class ColleagueTripSeralizer(MinimalTripSerializer):
    user = RequestSpecificField(
        lambda trip, req: trip.user_attendance.name(),
    )
    team = RequestSpecificField(
        lambda trip, req: trip.user_attendance.team.name,
    )
    subsidiary = RequestSpecificField(
        lambda trip, req: str(trip.user_attendance.team.subsidiary),
    )
    has_track = RequestSpecificField(
        lambda trip, req: trip.track is not None,
    )

    id = serpy.IntField()
    direction = serpy.StrField(required=False)
    user_attendance = serpy.IntField(attr="user_attendance.id", required=False)


class TripUpdateDeserializer(TripDeserializer):
    class Meta(TripDeserializer.Meta):
        fields = (
            "id",
            "file",
            "track",
            "commuteMode",
            "durationSeconds",
            "distanceMeters",
            "sourceApplication",
            "sourceId",
        )

    def create(self, validated_data):
        try:
            instance, _ = Trip.objects.update_or_create(
                user_attendance=self.user_attendance,
                date=validated_data["date"],
                direction=validated_data["direction"],
                defaults=validated_data,
            )
            instance.from_application = True
            instance.save()
        except ValidationError:
            raise GPXParsingFail
        return instance


class TripSet(UserAttendanceMixin, viewsets.ModelViewSet):
    """
    Documentation: https://www.dopracenakole.cz/rest-docs/

    get:
    Return a list of all tracks for logged user.

    get on /rest/trip/{id}:
    Return track detail including a track geometry.

    post:
    Create a new track instance. Track can be sent ether by GPX file (file parameter) or in GeoJSON format (track parameter).
    """

    def get_queryset(self):
        return Trip.objects.filter(
            user_attendance=self.ua(),
        )

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return TripSerializer
        elif self.action in ["update", "partial_update"]:
            return TripUpdateDeserializer
        else:
            return TripDeserializer

    permission_classes = [permissions.IsAuthenticated]


class TripRangeSet(UserAttendanceMixin, viewsets.ModelViewSet):
    """
    Documentation: https://www.dopracenakole.cz/rest-docs/

    get:
    Return a list of all trips in date range for logged user.

    get on /rest/gpx/{id}:
    Return track detail including a track geometry.
    """

    def get_queryset(self):
        subsidiaries = RequestSpecificField(
            lambda company, req: [
                MinimalSubsidiarySerializer(sub, context={"request": req}).data
                for sub in company.subsidiaries.filter(
                    teams__campaign__slug=req.subdomain, active=True
                ).distinct()
            ]
        )
        qs = Trip.objects.filter(
            user_attendance=self.ua(),
        )
        start_date = self.request.query_params.get("start", None)
        end_date = self.request.query_params.get("end", None)
        if start_date and end_date:
            qs = qs.filter(
                date__range=[start_date, end_date],
            )
        return qs

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return TripSerializer
        elif self.action in ["update", "partial_update"]:
            return TripUpdateDeserializer
        else:
            return TripDeserializer

    permission_classes = [permissions.IsAuthenticated]


class ColleagueTripRangeSet(UserAttendanceMixin, viewsets.ReadOnlyModelViewSet):
    """
    Documentation: https://www.dopracenakole.cz/rest-docs/

    get:
    Return a list of all trips in date range for logged in user and their colleagues.

    get on /rest/colleague_trip/{id}:
    Return track detail including a track geometry.
    """

    def get_queryset(self):
        qs = (
            Trip.objects.filter(
                user_attendance__team__subsidiary__company=self.ua().team.subsidiary.company.pk,
                user_attendance__campaign=self.ua().campaign,
            )
            .select_related(
                "user_attendance",
                "user_attendance__team",
                "user_attendance__team__subsidiary",
            )
            .order_by("date")
        )
        start_date = self.request.query_params.get("start", None)
        end_date = self.request.query_params.get("end", None)
        if start_date and end_date:
            qs = qs.filter(
                date__range=[start_date, end_date],
            )
        return qs

    serializer_class = ColleagueTripSeralizer
    permission_classes = [permissions.IsAuthenticated]


class CompetitionSerializer(serpy.Serializer):
    results = serpy.MethodField()

    id = serpy.IntField()
    name = serpy.StrField()
    slug = serpy.StrField()
    competitor_type = serpy.StrField()
    competition_type = serpy.StrField()
    url = serpy.StrField(required=False)
    priority = serpy.IntField()

    def get_results(self, obj):
        return reverse(
            "result-list",
            kwargs={"competition_slug": obj.slug},
            request=self.context["request"],
        )


class CompetitionSet(UserAttendanceMixin, viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return self.ua().get_competitions()

    serializer_class = CompetitionSerializer
    permission_classes = [permissions.IsAuthenticated]


class CompanyInCampaignField(RequestSpecificField):
    def to_value(self, value):
        object, context = value
        try:
            cic = object.__company_in_campaign
        except AttributeError:
            object.__company_in_campaign = CompanyInCampaign(
                object, context["request"].campaign
            )
            cic = object.__company_in_campaign
        return self.method(cic, context["request"])


class CompanySerializer(serpy.Serializer):
    subsidiaries = RequestSpecificField(
        lambda company, req: [
            MinimalSubsidiarySerializer(sub, context={"request": req}).data
            for sub in company.subsidiaries.filter(
                teams__campaign__slug=req.subdomain, active=True
            ).distinct()
        ]
    )
    eco_trip_count = CompanyInCampaignField(
        lambda cic, req: cic.eco_trip_count,
    )
    frequency = CompanyInCampaignField(
        lambda cic, req: cic.frequency,
    )
    emissions = CompanyInCampaignField(
        lambda cic, req: cic.emissions,
    )
    distance = CompanyInCampaignField(
        lambda cic, req: cic.distance,
    )
    working_rides_base_count = CompanyInCampaignField(
        lambda cic, req: cic.working_rides_base_count,
    )

    id = serpy.IntField()
    name = serpy.StrField()
    icon = OptionalImageField()
    icon_url = serpy.Field(call=True)
    gallery = HyperlinkedField("gallery-detail")
    gallery_slug = serpy.Field(call=True)


class CompanySet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    def get_queryset(self):
        return Company.objects.filter(
            subsidiaries__teams__campaign__slug=self.request.subdomain, active=True
        ).distinct()

    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]


class MyCompanySet(UserAttendanceMixin, viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return Company.objects.filter(pk=self.ua().team.subsidiary.company.pk)

    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]


class SubsidiaryInCampaignField(RequestSpecificField):
    def to_value(self, value):
        object, context = value
        try:
            sic = object.__subsidiary_in_campaign
        except AttributeError:
            object.__subsidiary_in_campaign = SubsidiaryInCampaign(
                object, context["request"].campaign
            )
            sic = object.__subsidiary_in_campaign
        return self.method(sic, context["request"])


class BaseSubsidiarySerializer(serpy.Serializer):
    frequency = SubsidiaryInCampaignField(
        lambda sic, req: sic.frequency,
    )
    distance = SubsidiaryInCampaignField(
        lambda sic, req: sic.distance,
    )
    eco_trip_count = SubsidiaryInCampaignField(
        lambda sic, req: sic.eco_trip_count,
    )
    working_rides_base_count = SubsidiaryInCampaignField(
        lambda sic, req: sic.working_rides_base_count,
    )
    emissions = SubsidiaryInCampaignField(
        lambda sic, req: sic.emissions,
    )

    id = serpy.IntField()
    address_street = serpy.StrField()
    city = HyperlinkedField("city-detail")
    icon_url = serpy.Field(call=True)


class MinimalSubsidiarySerializer(BaseSubsidiarySerializer):
    rest_url = HyperlinkedField("subsidiary-detail", attr="")


class SubsidiarySerializer(BaseSubsidiarySerializer):
    teams = SubsidiaryInCampaignField(
        lambda sic, req: [
            MinimalTeamSerializer(team, context={"request": req}).data
            for team in sic.teams
        ]
    )
    id = serpy.IntField()
    address_street = serpy.StrField()
    company = HyperlinkedField("company-detail")
    city = HyperlinkedField("city-detail")
    icon = HyperlinkedField("photo-detail")
    icon_url = serpy.Field(call=True)
    gallery = HyperlinkedField("gallery-detail")
    gallery_slug = serpy.Field(call=True)


class SubsidiarySet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return Subsidiary.objects.filter(
            teams__campaign__slug=self.request.subdomain, active=True
        ).distinct()

    serializer_class = SubsidiarySerializer
    permission_classes = [permissions.IsAuthenticated]


class MySubsidiarySet(UserAttendanceMixin, viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return Subsidiary.objects.filter(pk=self.ua().team.subsidiary.pk)

    serializer_class = SubsidiarySerializer
    permission_classes = [permissions.IsAuthenticated]


class BaseUserAttendanceSerializer(serpy.Serializer):
    distance = serpy.FloatField(
        attr="trip_length_total",
        # help_text="Distance ecologically traveled in Km",
    )

    emissions = serpy.Field(
        attr="get_emissions",
        call=True,
        # help_text="Emission reduction estimate",
    )
    working_rides_base_count = serpy.IntField(
        attr="get_working_rides_base_count",
        call=True,
        # help_text="Max number of possible trips",
    )

    id = serpy.IntField()
    name = serpy.StrField(call=True)
    frequency = serpy.FloatField()
    avatar_url = serpy.Field(call=True)
    eco_trip_count = serpy.IntField(call=True)


class MinimalUserAttendanceSerializer(BaseUserAttendanceSerializer):
    rest_url = RequestSpecificField(
        lambda ua, req: HyperlinkedField("userattendance-detail").get_url(ua, req)
    )

    is_me = RequestSpecificField(
        lambda ua, req: True if ua.userprofile.user.pk == req.user.pk else False,
    )


class UserAttendanceSerializer(BaseUserAttendanceSerializer):
    remaining_rides_count = serpy.IntField(
        attr="get_remaining_rides_count",
        call=True
        # help_text="Remaining number of possible trips",
    )
    sesame_token = RequestSpecificField(
        lambda ua, req: ua.userprofile.get_sesame_token()
        if ua.userprofile.user.pk == req.user.pk
        else None,
    )
    is_coordinator = RequestSpecificField(
        lambda ua, req: ua.userprofile.administrated_cities.exists()
        if ua.userprofile.user.pk == req.user.pk
        else None,
    )
    registration_complete = RequestSpecificField(
        lambda ua, req: ua.entered_competition(),
    )
    gallery = RequestSpecificField(
        lambda ua, req: HyperlinkedField("gallery-detail",).get_url(
            ua.userprofile.get_gallery(),
            req,
        ),
    )
    unread_notification_count = RequestSpecificField(
        lambda ua, req: ua.notifications().filter(unread=True).count()
        if ua.userprofile.user.pk == req.user.pk
        else None,
    )

    points = serpy.IntField()
    points_display = serpy.StrField(call=True)
    team = HyperlinkedField("team-detail")


class AllUserAttendanceSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    def get_queryset(self):
        # denorm.flush()
        return UserAttendance.objects.all().select_related("userprofile__user")

    serializer_class = UserAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    # TODO TODO TODO invalidate or do correctly somehow
    @method_decorator(cache_page(600))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class MyUserAttendanceSet(UserAttendanceMixin, viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        # denorm.flush()
        return UserAttendance.objects.filter(
            id=self.ua().id,
        ).select_related("userprofile__user")

    serializer_class = UserAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]


class BaseTeamSerializer(serpy.Serializer):
    distance = serpy.FloatField(
        attr="get_length",
        call=True,
    )
    frequency = serpy.FloatField(
        attr="get_frequency",
        call=True,
        # help_text="Fequeny of travel in as a fraction (multiply by 100 to get percentage)",
        # read_only=True,
    )
    emissions = serpy.Field(
        attr="get_emissions",
        call=True,
    )
    eco_trip_count = serpy.IntField(
        attr="get_eco_trip_count",
        call=True,
    )
    working_rides_base_count = serpy.IntField(
        attr="get_working_trips_count",
        call=True,
    )

    name = serpy.StrField(required=False)
    id = serpy.IntField()
    icon_url = serpy.Field(call=True)


class MinimalTeamSerializer(BaseTeamSerializer):
    rest_url = HyperlinkedField("team-detail", attr="")


class TeamSerializer(BaseTeamSerializer):
    members = RequestSpecificField(
        lambda team, req: MinimalUserAttendanceSerializer(
            team.members, context={"request": req}, many=True
        ).data
    )

    icon = HyperlinkedField("photo-detail")
    subsidiary = HyperlinkedField("subsidiary-detail")
    campaign = HyperlinkedField("campaign-detail")
    gallery = HyperlinkedField("gallery-detail")
    gallery_slug = serpy.Field(call=True)

    """read_only_fields = (
            "id",
            "subsidiary",
            "members",
            "frequency",
            "distance",
            "eco_trip_count",
            "emissions",
            "campaign",
            "icon_url",
            "gallery",
            "gallery_slug",
    )"""


class TeamSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    def get_queryset(self):
        return Team.objects.filter(
            campaign__slug=self.request.subdomain,
        )

    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    # TODO TODO TODO invalidate or do correctly somehow
    @method_decorator(cache_page(600))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class MyTeamSet(
    UserAttendanceMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    def get_queryset(self):
        return Team.objects.filter(pk=self.ua().team.pk)

    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]


class CompetitionResultSerializer(serpy.Serializer):
    user_attendance = serpy.StrField(required=False)
    company = HyperlinkedField("company-detail")
    place = serpy.IntField()
    name = serpy.StrField(attr="__str__", call=True)
    icon_url = RequestSpecificField(lambda a, b: "")
    divident = serpy.IntField(attr="result_divident", required=False)
    divisor = serpy.IntField(attr="result_divisor", required=False)
    emissions = serpy.Field(attr="get_emissions", call=True)
    id = serpy.IntField()
    team = HyperlinkedField("team-detail")
    competition = HyperlinkedField("competition-detail")
    result = serpy.StrField(required=False)
    place = serpy.IntField()
    frequency = serpy.FloatField(required=False)
    distance = serpy.FloatField(required=False)


class CompetitionResultSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        competition_slug = self.kwargs["competition_slug"]
        try:
            competition = Competition.objects.get(slug=competition_slug)
        except Competition.DoesNotExist:
            raise CompetitionDoesNotExist
        return (
            competition.get_results()
            .select_related("team")
            .order_by("-result")
            .annotate(
                place=Window(
                    expression=DenseRank(),
                    order_by=[
                        F("result").desc(),
                    ],
                ),
            )
        )

    serializer_class = CompetitionResultSerializer
    permission_classes = [permissions.IsAuthenticated]


class CityInCampaignSerializer(serpy.Serializer):
    city__name = serpy.StrField(attr="city.name")
    city__location = PointField(attr="city.location", format="latlon", required=False)
    city__wp_url = serpy.StrField(attr="city.get_wp_url", call=True)

    id = serpy.IntField()
    competitor_count = serpy.IntField(call=True)


class CityInCampaignSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return CityInCampaign.objects.filter(campaign__slug=self.request.subdomain)

    serializer_class = CityInCampaignSerializer
    permission_classes = [permissions.AllowAny]


class CitySerializer(serpy.Serializer):
    competitor_count = RequestSpecificField(
        lambda city, req: CityInCampaign.objects.get(
            city=city, campaign=req.campaign
        ).competitor_count(),
    )
    trip_stats = RequestSpecificField(
        lambda city, req: CityInCampaign.objects.get(
            city=city, campaign=req.campaign
        ).distances(),
    )
    # frequency = RequestSpecificField(  TODO
    #     lambda city, req: CityInCampaign.objects.get(city=city, campaign=req.campaign).distances()
    # )
    emissions = RequestSpecificField(
        lambda city, req: CityInCampaign.objects.get(
            city=city, campaign=req.campaign
        ).emissions(),
    )
    distance = RequestSpecificField(
        lambda city, req: CityInCampaign.objects.get(
            city=city, campaign=req.campaign
        ).distance(),
    )
    eco_trip_count = RequestSpecificField(
        lambda city, req: CityInCampaign.objects.get(
            city=city, campaign=req.campaign
        ).eco_trip_count(),
    )
    description = RequestSpecificField(
        lambda city, req: CityInCampaign.objects.get(
            city=city, campaign=req.campaign
        ).description(language=req.query_params.get("lang", "cs")),
    )
    organizer = RequestSpecificField(
        lambda city, req: CityInCampaign.objects.get(
            city=city, campaign=req.campaign
        ).organizer,
    )

    organizer_url = RequestSpecificField(
        lambda city, req: CityInCampaign.objects.get(
            city=city, campaign=req.campaign
        ).organizer_url,
    )
    subsidiaries = RequestSpecificField(
        lambda city, req: [
            HyperlinkedField(  # noqa
                "subsidiary-detail",
            ).get_url(subsidiary, req)
            for subsidiary in Subsidiary.objects.filter(  # noqa  # noqa
                id__in=Team.objects.filter(
                    subsidiary__city=city,
                    campaign=req.campaign,
                ).values_list("subsidiary", flat=True),
            )
        ]
    )
    competitions = RequestSpecificField(
        lambda city, req: [
            CompetitionSerializer(competition, context={"request": req}).data
            for competition in Competition.objects.filter(  # noqa
                city__id=city.id, campaign=req.campaign, company=None, is_public=True
            )
        ]
    )
    wp_url = serpy.StrField(
        attr="get_wp_url",
        call=True,
    )

    id = serpy.IntField()
    name = serpy.StrField()
    location = PointField(format="coords")
    # 'frequency', TODO


class CitySet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        city_ids = CityInCampaign.objects.filter(
            campaign__slug=self.request.subdomain
        ).values_list("city", flat=True)
        return City.objects.filter(id__in=city_ids)

    serializer_class = CitySerializer
    permission_classes = [permissions.IsAuthenticated]


class MyCitySet(UserAttendanceMixin, viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        city_ids = CityInCampaign.objects.filter(
            campaign__slug=self.request.subdomain,
            city=self.ua().team.subsidiary.city,
        ).values_list("city", flat=True)
        return City.objects.filter(id__in=city_ids)

    serializer_class = CitySerializer
    permission_classes = [permissions.IsAuthenticated]


def get_data_export_url(city, campaign):
    try:
        return CityInCampaign.objects.get(city=city, campaign=campaign).data_export.url
    except ValueError:
        return None


class CoordinatedCitySerializer(CitySerializer):
    data_export_password = RequestSpecificField(
        lambda city, req: CityInCampaign.objects.get(
            city=city, campaign=req.campaign
        ).data_export_password,
    )

    data_export_url = RequestSpecificField(
        lambda city, req: get_data_export_url(city, req.campaign),
    )


class CoordinatedCitySet(UserAttendanceMixin, viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return City.objects.filter(
            id__in=self.ua().userprofile.administrated_cities.all()
        )

    serializer_class = CoordinatedCitySerializer
    permission_classes = [permissions.IsAuthenticated]


class CommuteModeSerializer(serpy.Serializer):
    id = serpy.IntField()
    slug = serpy.StrField()
    does_count = serpy.BoolField()
    eco = serpy.BoolField()
    distance_important = serpy.BoolField()
    duration_important = serpy.BoolField()
    minimum_distance = serpy.FloatField()
    minimum_duration = serpy.IntField()
    description_en = serpy.StrField(required=False)
    description_cs = serpy.StrField(required=False)
    icon = OptionalImageField()
    name_en = serpy.StrField(required=False)
    name_cs = serpy.StrField()
    points = serpy.IntField()
    # icon TODO


class CommuteModeSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return CommuteMode.objects.all()

    serializer_class = CommuteModeSerializer
    permission_classes = [permissions.IsAuthenticated]


class CampaignTypeSerializer(serpy.Serializer):
    id = serpy.IntField()
    slug = serpy.StrField()
    name = serpy.StrField()
    name_en = serpy.StrField(required=False)
    name_cs = serpy.StrField()
    web = serpy.StrField()
    campaigns = RequestSpecificField(
        lambda campaign_type, req: [
            HyperlinkedField(  # noqa
                "campaign-detail",
            ).get_url(campaign, req)
            for campaign in campaign_type.campaigns.all()
        ]
    )
    frontend_url = serpy.StrField()


class CampaignTypeDeserializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CampaignType
        fields = (
            "id",
            "slug",
            "name",
            "name_en",
            "name_cs",
            "web",
            "campaigns",
            "frontend_url",
        )


from rest_framework.permissions import BasePermission, SAFE_METHODS

# https://gist.github.com/andreagrandi/14e07afd293fafaea770f69cf66cac14
class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS and request.user.is_authenticated:
            return True
        else:
            return request.user.is_staff


class IsSuperuser(BasePermission):
    def has_permission(self, request, view):
        if (
            request.method in SAFE_METHODS
            and request.user.is_authenticated
            and request.user.is_superuser
        ):
            return True


class CampaignTypeSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return CampaignType.objects.all()

    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        return (
            CampaignTypeSerializer
            if self.action in ["retrieve", "list"]
            else CampaignTypeDeserializer
        )


class PhaseSerializer(serpy.Serializer):
    phase_type = serpy.StrField()
    date_from = serpy.DateField(required=False)
    date_to = serpy.DateField(required=False)


class CampaignSerializer(serpy.Serializer):
    phase_set = PhaseSerializer(many=True)
    id = serpy.IntField()
    slug = serpy.StrField()
    days_active = serpy.IntField()
    year = serpy.StrField()
    campaign_type = HyperlinkedField("campaigntype-detail")


class CampaignSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return Campaign.objects.all()

    serializer_class = CampaignSerializer
    permission_classes = [permissions.IsAuthenticated]


class ThisCampaignSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return Campaign.objects.filter(slug=self.request.subdomain)

    serializer_class = CampaignSerializer
    permission_classes = [permissions.IsAuthenticated]


class NotificationSerializer(serpy.Serializer):
    mark_as_read = RequestSpecificField(
        lambda notification, req: req.build_absolute_uri(
            reverse("notifications:mark_as_read", args=(notification.slug,))
        ),
    )
    mark_as_unread = RequestSpecificField(
        lambda notification, req: req.build_absolute_uri(
            reverse("notifications:mark_as_unread", args=(notification.slug,))
        ),
    )

    id = serpy.IntField()
    level = serpy.StrField()
    unread = serpy.BoolField()
    deleted = serpy.BoolField()
    verb = serpy.StrField()
    description = serpy.StrField(required=False)
    timestamp = serpy.DateTimeField(date_format="%Y-%m-%dT%H:%M:%S.%f")
    data = serpy.StrField(required=False)  # podezřelé


class NotificationSet(UserAttendanceMixin, viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return self.ua().notifications()

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]


class PhotoDeserializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = photologue.models.Photo
        fields = (
            "id",
            "caption",
            "image",
        )

    def create(self, validated_data, *args, **kwargs):
        request = self.context["request"]
        self.user_attendance = request.user_attendance
        if not self.user_attendance:
            self.user_attendance = get_or_create_userattendance(
                request, request.subdomain
            )
        validated_data["slug"] = "ua%s-%s" % (
            self.user_attendance.pk,
            round(time.time() * 1000),
        )
        validated_data["title"] = validated_data["slug"]
        photo = super().create(validated_data, *args, **kwargs)
        self.user_attendance.userprofile.get_gallery().photos.add(photo)
        self.user_attendance.team.get_gallery().photos.add(photo)
        self.user_attendance.team.subsidiary.get_gallery().photos.add(photo)
        self.user_attendance.team.subsidiary.company.get_gallery().photos.add(photo)
        return photo


class PhotoSet(UserAttendanceMixin, viewsets.ModelViewSet):
    def get_queryset(self):
        return self.ua().team.subsidiary.company.get_gallery().photos.all()

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return (
            PhotoSerializer
            if self.action in ["retrieve", "list"]
            else PhotoDeserializer
        )


class PhotoSerializer(serpy.Serializer):
    id = serpy.IntField()
    caption = serpy.StrField()
    image = serpy.ImageField()


class GallerySerializer(serpy.Serializer):
    title = serpy.StrField()
    slug = serpy.StrField()
    description = serpy.StrField()
    photos = RequestSpecificField(
        lambda gallery, req: [
            HyperlinkedField("photo-detail").get_url(photo, req)
            for photo in gallery.photos.all()
        ]
    )


class GallerySet(
    UserAttendanceMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    def get_queryset(self):
        return photologue.models.Gallery.objects.all()

    serializer_class = GallerySerializer
    permission_classes = [permissions.IsAuthenticated]


class StravaAccountSerializer(serpy.Serializer):
    strava_username = serpy.StrField()
    first_name = serpy.StrField()
    last_name = serpy.StrField()
    user_sync_count = serpy.IntField()
    errors = serpy.StrField()


class StravaAccountSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return StravaAccount.objects.filter(user=self.request.user)

    serializer_class = StravaAccountSerializer
    permission_classes = [permissions.IsAuthenticated]


class LandingPageIconSerializer(serpy.Serializer):
    file = RequestSpecificField(
        lambda obj, req: req.build_absolute_uri(obj.file.url) if obj.file else None
    )
    role = serpy.StrField()
    min_frequency = serpy.FloatField(required=False)
    max_frequency = serpy.FloatField(required=False)


class LandingPageIconSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return LandingPageIcon.objects.all()

    serializer_class = LandingPageIconSerializer
    permission_classes = [permissions.IsAuthenticated]


class GetPhotoURLAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        if (
            request.user.is_authenticated
            and request.user.groups.filter(name="metabase").exists()
        ):
            return True
        return False


class PhotoURLGet(APIView):
    """Get photo URL"""

    permission_classes = [GetPhotoURLAccess]

    def get(self, request, photo_url=None):
        photo = get_object_or_404(Photo, image=photo_url)
        return Response(photo.get_display_url())


class LoggedInUsersListSerializer(serpy.Serializer):
    username = serpy.StrField()


class LoggedInUsersListGet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsSuperuser]
    serializer_class = LoggedInUsersListSerializer

    def get_queryset(self):
        return get_all_logged_in_users()


class HasUserVerifiedEmailAddress(APIView):
    """Has user verified email address"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(
            {"has_user_verified_email_address": has_verified_email(request.user)}
        )


class CitiesSerializer(serpy.Serializer):
    id = serpy.IntField()
    name = serpy.StrField()


class CitiesSet(viewsets.ReadOnlyModelViewSet):
    # fetch all available cities (for campaign)
    def get_queryset(self):
        city_ids = CityInCampaign.objects.filter(
            campaign__slug=self.request.subdomain
        ).values_list("city", flat=True)
        return City.objects.filter(id__in=city_ids)

    serializer_class = CitiesSerializer
    permission_classes = [permissions.IsAuthenticated]


class AddressSerializer(serpy.Serializer):
    street = serpy.StrField()
    street_number = serpy.StrField()
    recipient = serpy.StrField(required=False)
    psc = serpy.StrField(required=False)
    city = serpy.StrField()


class OptionalAddressSerializer(serpy.Serializer):
    street = serpy.StrField(required=False)
    street_number = serpy.StrField(required=False)
    recipient = serpy.StrField(required=False)
    psc = serpy.StrField(required=False)
    city = serpy.StrField(required=False)


class CompaniesListSerializer(serpy.Serializer):
    id = serpy.IntField()
    name = serpy.StrField()


class CompaniesSerializer(serpy.Serializer):
    id = serpy.IntField()
    name = serpy.StrField()
    ico = serpy.StrField(required=False)
    dic = serpy.StrField(required=False)
    note = serpy.StrField(required=False)
    address = AddressSerializer()
    organization_type = serpy.StrField()


class CompaniesDeserializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Company
        fields = (
            "id",
            "name",
            "ico",
            "dic",
            "note",
            "address_street",
            "address_street_number",
            "address_psc",
            "address_city",
            "address_recipient",
            "organization_type",
        )

    def to_internal_value(self, data):
        if data.get("address"):
            address_data = data.pop("address")
            data["address_street"] = address_data.get("street")
            data["address_street_number"] = address_data.get("street_number")
            data["address_recipient"] = address_data.get("recipient")
            data["address_psc"] = address_data.get("psc")
            data["address_city"] = address_data.get("city")
        return super().to_internal_value(data)

    def to_representation(self, value):
        data = super().to_representation(value)
        data["address"] = {
            "street": data.pop("address_street"),
            "street_number": data.pop("address_street_number"),
            "recipient": data.pop("address_recipient"),
            "psc": data.pop("address_psc"),
            "city": data.pop("address_city"),
        }
        return data


class CompaniesSet(viewsets.ModelViewSet):
    def get_queryset(self):
        organization_type = self.kwargs.get("organization_type")
        if organization_type:
            return Company.objects.filter(organization_type=organization_type)
        return Company.objects.all()

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CompaniesSerializer
        if self.action == "list":
            return CompaniesListSerializer
        else:
            return CompaniesDeserializer


class SubsidiariesSerializer(serpy.Serializer):
    id = serpy.IntField()
    # street
    address = AddressSerializer()

    teams = SubsidiaryInCampaignField(
        lambda sic, req: [
            MinimalTeamSerializer(team, context={"request": req}).data
            for team in sic.teams
        ]
    )


class SubsidiariesDeserializer(serializers.HyperlinkedModelSerializer):

    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(), source="city"
    )
    organization_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), source="company"
    )

    class Meta:
        model = Subsidiary
        fields = (
            "id",
            "address_street",
            "address_street_number",
            "address_psc",
            "address_city",
            "address_recipient",
            "organization_id",
            "city_id",
            "active",
            "box_addressee_name",
            "box_addressee_telephone",
            "box_addressee_email",
        )

    def to_internal_value(self, data):
        address_data = data.pop("address")
        data["address_street"] = address_data.get("street")
        data["address_street_number"] = address_data.get("street_number")
        data["address_recipient"] = address_data.get("recipient")
        data["address_psc"] = address_data.get("psc")
        data["address_city"] = address_data.get("city")
        return super().to_internal_value(data)

    def to_representation(self, value):
        data = super().to_representation(value)
        del data["organization_id"]
        data["address"] = {
            "street": data.pop("address_street"),
            "street_number": data.pop("address_street_number"),
            "recipient": data.pop("address_recipient"),
            "psc": data.pop("address_psc"),
            "city": data.pop("address_city"),
        }
        return data


class SubsidiariesSet(viewsets.ModelViewSet):
    # fetches all subsidiaries from a given organization
    def get_queryset(self):
        organization_id = self.kwargs["organization_id"]
        return Subsidiary.objects.filter(company_id=organization_id)

    def create(self, request, *args, **kwargs):

        request_data = request.data.copy()
        request_data["organization_id"] = self.kwargs["organization_id"]

        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return SubsidiariesSerializer
        else:
            return SubsidiariesDeserializer


class TeamsSerializer(serpy.Serializer):
    id = serpy.IntField()
    name = serpy.StrField(required=False)

    members = RequestSpecificField(
        lambda team, req: MinimalUserAttendanceSerializer(
            team.members, context={"request": req}, many=True
        ).data
    )


class TeamsDeserializer(serializers.HyperlinkedModelSerializer):
    campaign_id = serializers.PrimaryKeyRelatedField(
        queryset=Campaign.objects.all(), source="campaign"
    )
    subsidiary_id = serializers.PrimaryKeyRelatedField(
        queryset=Subsidiary.objects.all(), source="subsidiary"
    )
    members = RequestSpecificField(
        lambda team, req: MinimalUserAttendanceSerializer(
            team.members, context={"request": req}, many=True
        ).data
    )

    class Meta:
        model = Team
        fields = ("id", "name", "campaign_id", "subsidiary_id")

    def to_representation(self, value):
        data = super().to_representation(value)
        del data["campaign_id"]
        del data["subsidiary_id"]
        return data


class TeamsSet(viewsets.ModelViewSet):
    # fetches all teams from a given subsidiary
    def get_queryset(self):
        subsidiary_id = self.kwargs["subsidiary_id"]
        return Team.objects.filter(
            subsidiary_id=subsidiary_id,
            campaign_id=self.request.campaign.id,
        )

    def create(self, request, *args, **kwargs):

        request_data = request.data.copy()
        request_data["subsidiary_id"] = self.kwargs["subsidiary_id"]
        request_data["campaign_id"] = self.request.campaign.id

        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return TeamsSerializer
        else:
            return TeamsDeserializer


router = routers.DefaultRouter()
router.register(r"gpx", TripSet, basename="gpxfile")
router.register(r"trips", TripRangeSet, basename="trip")
router.register(r"colleague_trips", ColleagueTripRangeSet, basename="colleague_trip")
router.register(r"team", TeamSet, basename="team")
router.register(r"my_team", MyTeamSet, basename="my_team")
router.register(r"city_in_campaign", CityInCampaignSet, basename="city_in_campaign")
router.register(r"city", CitySet, basename="city")
router.register(r"my_city", MyCitySet, basename="my-city")
router.register(r"userattendance", MyUserAttendanceSet, basename="myuserattendance")
router.register(r"all_userattendance", AllUserAttendanceSet, basename="userattendance")
router.register(r"commute_mode", CommuteModeSet, basename="commute_mode")
router.register(r"campaign", CampaignSet, basename="campaign")
router.register(r"this_campaign", ThisCampaignSet, basename="this-campaign")
router.register(r"campaign_type", CampaignTypeSet, basename="campaigntype")
router.registry.extend(organization_router.registry)
router.register(r"competition", CompetitionSet, basename="competition")
router.register(r"subsidiary", SubsidiarySet, basename="subsidiary")
router.register(r"my_subsidiary", MySubsidiarySet, basename="my-subsidiary")
router.register(r"company", CompanySet, basename="company")
router.register(r"my_company", MyCompanySet, basename="my-company")
router.register(r"notification", NotificationSet, basename="notification")
router.register(
    r"result/(?P<competition_slug>.+)", CompetitionResultSet, basename="result"
)
router.register(r"photo", PhotoSet, basename="photo")
router.register(r"gallery", GallerySet, basename="gallery")
router.register(r"strava_account", StravaAccountSet, basename="strava_account")
router.register(r"landing_page_icon", LandingPageIconSet, basename="landing_page_icon")


router.register(r"coordinators/city", CoordinatedCitySet, basename="coordinated-city")
router.register(
    r"logged-in-user-list", LoggedInUsersListGet, basename="logged_in_user_list"
)
router.register(r"cities", CitiesSet, basename="cities")
router.register(
    rf"organizations/(?P<organization_type>({'|'.join(organization_types)}))",
    CompaniesSet,
    basename="organizations-by-type",
)
router.register(r"organizations", CompaniesSet, basename="organizations")
router.register(
    r"organizations/(?P<organization_id>\d+)/subsidiaries",
    SubsidiariesSet,
    basename="organization-subsidiaries",
)
router.register(
    r"subsidiaries/(?P<subsidiary_id>\d+)/teams", TeamsSet, basename="subsidiary-teams"
)
