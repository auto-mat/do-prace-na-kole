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
import base64
import time
import hashlib
import logging

from enum import Enum

import stravalib
from stravalib.exc import AccessUnauthorized, RateLimitExceeded

# TODO re-enable or fix denorm
# import denorm

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.validators import validate_email
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import ExpressionWrapper, F, CharField, Value, Window
from django.db.models.functions import Concat, DenseRank
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_page
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from allauth.account.utils import has_verified_email, send_email_confirmation
from donation_chooser.rest import organization_router

from drf_extra_fields.geo_fields import PointField

from memoize import mproperty
from notifications.models import Notification

import photologue

from rest_framework import mixins, permissions, routers, serializers, viewsets

from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.validators import UniqueValidator
from rest_framework.views import APIView
from price_level import models as price_level_models

from .middleware import get_or_create_userattendance
from .models import (
    Address,
    Campaign,
    CampaignType,
    City,
    CityInCampaign,
    CommuteMode,
    Company,
    CompanyAdmin,
    Competition,
    CompetitionResult,
    LandingPageIcon,
    Occupation,
    Payment,
    PAYMENT_STATUSES,
    PayUOrderedProduct,
    Phase,
    Status,
    Subsidiary,
    Team,
    Trip,
    UserAttendance,
    UserProfile,
)
from .models.company import CompanyInCampaign
from .models.subsidiary import SubsidiaryInCampaign
from t_shirt_delivery.models import TShirtSize
from coupons.models import DiscountCoupon

from .models.util import (
    get_competition_competition_type_field_choices,
    get_competition_competitor_type_field_choices,
)
from .util import (
    attrgetter_def_val,
    Cache,
    get_all_logged_in_users,
    get_api_version_from_request,
    register_challenge_serializer_base_cache_key_name,
    today,
)
from .tasks import (
    team_membership_approval_mail,
    team_membership_denial_mail,
    team_membership_invitation_mail,
)
from .templatetags.dpnk_tags import concat_all, concat_cities_into_url_param
from .payu import PayU
from .rest_permissions import IsOwnerOrSuperuser
from .rest_auth import get_tokens_for_user, PayUNotifyOrderRequestAuthentification

from photologue.models import Photo
from stravasync.models import StravaAccount

from stravasync import hashtags

import drf_serpy as serpy

from django.contrib.gis.geos import GEOSGeometry
from django.utils.encoding import smart_str

import json
import requests
from rest_framework import status

from django.db import transaction

logger = logging.getLogger(__name__)

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


class EmptyStrField(serpy.Field):
    """Replace None value with empty string '' value"""

    def to_value(self, value):
        if value is None:
            return ""
        return str(value)


class NullIntField(serpy.Field):
    """Return int value or None (null)"""

    def to_value(self, value):
        if value is None or value == "":
            return None
        return int(value)


class NullStrField(serpy.Field):
    """Return None (null)"""

    def to_value(self, value):
        if value is None:
            return None
        return value


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


class TripBaseDeserializer(MinimalTripDeserializer):
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
    file_encoded_string = serializers.CharField(
        required=False,
        help_text="GPX file with the track as base64 encoded string",
    )
    description = serializers.CharField(
        required=False, help_text="Description of the trip as input by user"
    )

    class Meta:
        model = Trip
        fields = (
            "id",
            "trip_date",
            "direction",
            "file",
            "file_encoded_string",
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


class TripDeserializer(TripBaseDeserializer):
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


class TripsDeserializer(serializers.Serializer):
    trips = TripBaseDeserializer(many=True)

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
        for trip in validated_data["trips"]:
            if (
                "date" in validated_data
                and not self.user_attendance.campaign.day_recent(validated_data["date"])
            ):
                raise InactiveDayGPX
        return validated_data

    @transaction.atomic
    def create(self, validated_data):
        instances = {"trips": []}
        try:
            for trip in validated_data["trips"]:
                file_encoded_string = trip.pop("file_encoded_string", None)
                if file_encoded_string:
                    format, filestr = file_encoded_string.split(";base64,")
                    ext = format.split("/")[-1]
                    data = ContentFile(base64.b64decode(filestr), name=f"temp.{ext}")
                    trip["gpx_file"] = data
                trip["user_attendance"] = self.user_attendance
                trip["from_application"] = True
                instance, _ = Trip.objects.update_or_create(
                    user_attendance=self.user_attendance,
                    date=trip["date"],
                    direction=trip["direction"],
                    defaults=trip,
                )
                instances["trips"].append(instance)
        except ValidationError:
            raise GPXParsingFail
        except IntegrityError:
            raise TripAlreadyExists

        return instances


class TripSerializer(MinimalTripSerializer):
    sourceId = serpy.StrField(
        required=False,
        attr="source_id",
        # help_text="Any string identifiing the id in the source application",
    )

    file = RequestSpecificField(
        lambda trip, req: (
            req.build_absolute_uri(trip.gpx_file.url) if trip.gpx_file else None
        ),
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
        api_version = get_api_version_from_request(request=self.request)
        if self.action in ["list", "retrieve"]:
            return TripSerializer
        elif self.action in ["update", "partial_update"]:
            return TripUpdateDeserializer
        else:
            if api_version == "v1":
                return TripDeserializer
            elif api_version == "v2":
                return TripsDeserializer

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
        api_version = get_api_version_from_request(request=self.request)
        if self.action in ["list", "retrieve"]:
            return TripSerializer
        elif self.action in ["update", "partial_update"]:
            return TripUpdateDeserializer
        else:
            if api_version == "v1":
                return TripDeserializer
            elif api_version == "v2":
                return TripsDeserializer

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


class CommuteModeMinimalSerializer(serpy.Serializer):
    id = serpy.IntField()
    name_cs = serpy.StrField()
    name_en = serpy.StrField(required=False)
    slug = serpy.StrField()


class CompetitionSerializer(serpy.Serializer):
    results = serpy.MethodField()

    id = serpy.IntField()
    name = serpy.StrField()
    slug = serpy.StrField()
    competitor_type = serpy.StrField()
    competition_type = serpy.StrField()
    url = serpy.StrField(required=False)
    priority = serpy.IntField()
    date_from = serpy.StrField(required=False)
    date_to = serpy.StrField(required=False)
    commute_modes = RequestSpecificField(
        lambda competition, req: CommuteModeMinimalSerializer(
            competition.commute_modes.all(),
            context={"request": req},
            many=True,
        ).data
    )
    description = EmptyStrField()

    def get_results(self, obj):
        return reverse(
            "result-list",
            kwargs={"competition_slug": obj.slug},
            request=self.context["request"],
        )


class CompetitionDeserializer(serializers.ModelSerializer):
    name = serializers.CharField(
        validators=[UniqueValidator(queryset=Competition.objects.all())]
    )
    competition_type = serializers.ChoiceField(
        choices=list(get_competition_competition_type_field_choices().items()),
    )
    competitor_type = serializers.ChoiceField(
        choices=list(get_competition_competitor_type_field_choices().items()),
    )

    def validate(self, data):
        request = self.context["request"]
        data["campaign"] = request.campaign
        data["slug"] = f"FA-{request.campaign.pk}-{slugify(data['name'])[0:30]}"
        return super().validate(data)

    class Meta:
        model = Competition
        fields = [
            "name",
            "url",
            "competition_type",
            "competitor_type",
            "commute_modes",
            "date_from",
            "date_to",
            "description",
        ]


class CompetitionSet(UserAttendanceMixin, viewsets.ModelViewSet):
    def get_queryset(self):
        return self.ua().get_competitions()

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return CompetitionSerializer
        else:
            return CompetitionDeserializer

    permission_classes = [permissions.IsAuthenticated]


class CompetitionFieldsValues(APIView):
    """Get competition fields choices values"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "competition_type": get_competition_competition_type_field_choices(),
                "competitor_type": get_competition_competitor_type_field_choices(),
                "commute_modes": CommuteMode.objects.all().values("id", "name"),
            }
        )


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
    email = RequestSpecificField(lambda ua, req: ua.userprofile.user.email)
    sex = RequestSpecificField(lambda ua, req: ua.userprofile.sex)
    frequency = serpy.FloatField()
    avatar_url = serpy.Field(call=True)
    eco_trip_count = serpy.IntField(call=True)
    approved_for_team = serpy.StrField()


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
        call=True,
        # help_text="Remaining number of possible trips",
    )
    sesame_token = RequestSpecificField(
        lambda ua, req: (
            ua.userprofile.get_sesame_token()
            if ua.userprofile.user.pk == req.user.pk
            else None
        ),
    )
    is_coordinator = RequestSpecificField(
        lambda ua, req: (
            ua.userprofile.administrated_cities.exists()
            if ua.userprofile.user.pk == req.user.pk
            else None
        ),
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
        lambda ua, req: (
            ua.notifications().filter(unread=True).count()
            if ua.userprofile.user.pk == req.user.pk
            else None
        ),
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
    """Only approved team members"""

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
    member_count = serpy.IntField()
    is_full = serpy.Field(call=True)
    unapproved_member_count = serpy.IntField()

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


class TeamWithAllMembersSerializer(TeamSerializer):
    """All team members"""

    members = RequestSpecificField(
        lambda team, req: MinimalUserAttendanceSerializer(
            team.all_members(), context={"request": req}, many=True
        ).data
    )


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


class TeamMembersDeserializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    approved_for_team = serializers.ChoiceField(choices=UserAttendance.TEAMAPPROVAL)
    team = serializers.CharField(
        required=False,
        allow_null=True,
    )
    reason = serializers.CharField(required=False)

    class Meta:
        model = UserAttendance
        fields = ["id", "approved_for_team", "reason", "team"]


class MyTeamMemebersDeserializer(serializers.ModelSerializer):
    members = TeamMembersDeserializer(many=True)

    class Meta:
        model = Team
        fields = ["members"]

    def update(self, instance, validated_data):
        approved_for_team = "approved_for_team"
        team = "team"
        members = "members"
        reason = "reason"
        update_models_approved = []
        update_models_denied = []
        update_fields = []

        if [member for member in validated_data[members] if team in member]:
            update_fields.append(team)

        for user_attendance in validated_data[members]:
            user_attendance_model_instance = instance.users.get(
                id=user_attendance["id"]
            )
            if team in user_attendance:
                user_attendance_model_instance.team = user_attendance[team]
            """
            Update UserAttendance model approved_for_team field value
            only if value is approved, beacuse if you erase team
            approved_for_team field value is automatically updated by
            pre_user_team_changed() func by pre_save signal
            """
            if user_attendance.get(approved_for_team) == "approved":
                user_attendance_model_instance.approved_for_team = user_attendance[
                    approved_for_team
                ]

                if approved_for_team not in update_fields:
                    update_fields.append(approved_for_team)

                update_models_approved.append(
                    {
                        "user_attendance": user_attendance_model_instance,
                        "reason": user_attendance.get(reason),
                    }
                )
            elif user_attendance.get(approved_for_team) == "denied":
                update_models_denied.append(
                    {
                        "user_attendance": user_attendance_model_instance,
                        "reason": user_attendance.get(reason),
                    }
                )
        update_models = [
            *[model["user_attendance"] for model in update_models_approved],
            *[model["user_attendance"] for model in update_models_denied],
        ]
        UserAttendance.objects.bulk_update(
            update_models,
            update_fields,
        )
        # Send email
        team_membership_approval_mail.delay(
            user_attendance_ids=[
                model["user_attendance"].id for model in update_models_approved
            ],
        )
        team_membership_denial_mail.delay(
            team_members=[
                {
                    "user_attendance_id": model["user_attendance"].id,
                    "denier_id": self.context["request"].user.id,
                    "reason": model["reason"],
                }
                for model in update_models_denied
            ]
        )

        return {"members": update_models}

    def validate(self, data):
        id_field_name = "id"
        validated_data = super().validate(data)
        self.user_attendance = get_or_create_userattendance(
            self.context["request"],
            self.context["request"].subdomain,
        )

        if not self.user_attendance.team_id:
            raise serializers.ValidationError(
                _("Účastník kampaně <%(email)s> nemá přiřazený tým.")
                % {"email": self.user_attendance.userprofile.user.email},
            )
        for member in validated_data["members"]:
            if (
                member["id"] == self.user_attendance.id
                and "team" in member
                and member["team"] is None
            ):
                raise serializers.ValidationError(
                    _(
                        "Sám sobě účastníkový kamapane s ID <%(id)s>"
                        " není možné odstranit přiřazený tým."
                    )
                    % {"id": self.user_attendance.id},
                )
        api_version = get_api_version_from_request(request=self.context["request"])
        team_members = self.user_attendance.team.members
        if api_version == "v1":
            team_members = self.user_attendance.team.members
        elif api_version == "v2":
            team_members = self.user_attendance.team.all_members()

        is_not_members_ids = [
            user_attendance[id_field_name]
            for user_attendance in validated_data["members"]
            if user_attendance[id_field_name]
            not in team_members.values_list(id_field_name, flat=True)
        ]
        if is_not_members_ids:
            raise serializers.ValidationError(
                _(
                    "Pouze členové vašeho týmu mohou být povoleni <%(team_members)s>,"
                    " účastník s ID <%(user_attendance_id)s> není členem vašeho týmu."
                )
                % {
                    "team_members": [
                        {
                            "id": user[id_field_name],
                            "email": user["userprofile__user__email"],
                        }
                        for user in list(
                            team_members.values(
                                id_field_name, "userprofile__user__email"
                            )
                        )
                    ],
                    "user_attendance_id": ", ".join(list(map(str, is_not_members_ids))),
                },
            )
        return validated_data

    def validate_members(self, members):
        team = "team"
        self.user_attendance = get_or_create_userattendance(
            self.context["request"],
            self.context["request"].subdomain,
        )
        for member in members:
            if team in member and member[team] is not None:
                raise serializers.ValidationError(
                    _(
                        "Pro odstranení týmu účastníka kampane s"
                        " ID <%(id)s> je povolena pouze hodnota <null>."
                        " Změnit tým není povoleno."
                    )
                    % {"id": self.user_attendance.id},
                )
        return members


class MyTeamSet(UserAttendanceMixin, viewsets.ModelViewSet):
    http_method_names = ["head", "get", "put"]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        pk = self.kwargs.get("pk")
        return Team.objects.filter(id=self.ua().team_id if not pk else pk)

    def get_serializer_class(self):
        api_version = get_api_version_from_request(request=self.request)
        if self.action in ["retrieve", "list"]:
            if api_version == "v1":
                return TeamSerializer
            elif api_version == "v2":
                return TeamWithAllMembersSerializer
        else:
            return MyTeamMemebersDeserializer


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
    city__slug = serpy.StrField(attr="city.slug")
    city__wp_slug = serpy.StrField(attr="city.get_wp_slug", call=True)

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
    slug = serpy.StrField()
    wp_slug = serpy.StrField(attr="get_wp_slug", call=True)
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


class CommuteModeSerializer(CommuteModeMinimalSerializer):
    does_count = serpy.BoolField()
    eco = serpy.BoolField()
    distance_important = serpy.BoolField()
    duration_important = serpy.BoolField()
    minimum_distance = serpy.FloatField()
    minimum_duration = serpy.IntField()
    description_en = serpy.StrField(required=False)
    description_cs = serpy.StrField(required=False)
    icon = OptionalImageField()
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


class PriceLevelSerializer(serpy.Serializer):
    name = serpy.StrField()
    price = serpy.FloatField()
    category = serpy.StrField()
    takes_effect_on = serpy.DateField()


class CampaignSerializer(serpy.Serializer):
    phase_set = PhaseSerializer(many=True)
    price_level = RequestSpecificField(
        lambda campaign, req: [
            PriceLevelSerializer(price_level).data
            for price_level in price_level_models.PriceLevel.objects.filter(
                pricable=req.campaign
            ).only("name", "price", "category", "takes_effect_on")
        ]
    )

    id = serpy.IntField()
    slug = serpy.StrField()
    days_active = serpy.IntField()
    year = serpy.StrField()
    campaign_type = HyperlinkedField("campaigntype-detail")
    max_team_members = serpy.IntField()
    description = serpy.StrField(call=True, attr="interpolate_description")


class CampaignSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return Campaign.objects.all()

    serializer_class = CampaignSerializer
    permission_classes = [permissions.IsAuthenticated]


class ThisCampaignSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return Campaign.objects.filter(slug=self.request.subdomain)

    # @method_decorator(cache_page(60 * 60 * 8))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    serializer_class = CampaignSerializer


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
    warn_user_sync_count = serpy.MethodField()
    max_user_sync_count = serpy.MethodField()
    hashtag_from = serpy.MethodField()
    hashtag_to = serpy.MethodField()
    sync_outcome = serpy.MethodField()
    last_sync_time = serpy.MethodField()

    def _get_lang_code(self, lang_code):
        return "cs" if lang_code == "sk" else lang_code

    def get_warn_user_sync_count(self, obj):
        return settings.STRAVA_MAX_USER_SYNC_COUNT // 2

    def get_max_user_sync_count(self, obj):
        return settings.STRAVA_MAX_USER_SYNC_COUNT

    def get_hashtag_from(self, obj):
        return hashtags.get_hashtag_from(
            campaign_slug=self.context["request"].subdomain,
            lang=self._get_lang_code(
                lang_code=self.context["request"].LANGUAGE_CODE,
            ),
        )

    def get_hashtag_to(self, obj):
        return hashtags.get_hashtag_to(
            campaign_slug=self.context["request"].subdomain,
            lang=self._get_lang_code(
                lang_code=self.context["request"].LANGUAGE_CODE,
            ),
        )

    def get_sync_outcome(self, obj):
        from stravasync import tasks

        result, error = None, None
        if (
            self.context["sync"] or obj.last_sync_time is None
        ) and obj.user_sync_count < settings.STRAVA_MAX_USER_SYNC_COUNT:
            try:
                result = tasks.sync(obj.id)
                result.pop("client")
            except requests.exceptions.ConnectionError:
                error = _("Aplikace Strava není dostupná.")
            except RateLimitExceeded:
                error = _("API limit vyčerpan.")
        if error:
            return {"result": result, "error": error}
        return {"result": result}

    def get_last_sync_time(self, obj):
        if obj.last_sync_time:
            return obj.last_sync_time.astimezone().isoformat()
        return None


class StravaAccountSet(viewsets.ReadOnlyModelViewSet):
    sync = None

    def get_queryset(self):
        if self.sync is None:
            self.sync = self.kwargs.get("sync", None) == "sync"
        return StravaAccount.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"sync": self.sync})
        return context

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
    slug = serpy.StrField()
    wp_slug = serpy.StrField(attr="get_wp_slug", call=True)


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


class CompaniesSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
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


class SubsidiariesSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
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


class TeamsSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
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


class MerchandiseSerializer(serpy.Serializer):
    id = serpy.IntField()
    name = serpy.StrField(attr="name1")
    sex = serpy.StrField()
    size = serpy.StrField()
    author = serpy.StrField()
    material = serpy.StrField()
    description = serpy.StrField()
    t_shirt_preview = OptionalImageField()
    available = serpy.BoolField()


class MerchandiseSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        code = self.kwargs.get("code")
        queryset = {
            "campaign__slug": self.request.subdomain,
            "ship": True,
        }
        if code:
            queryset.update({"code": code})
            if code == "nic":
                queryset.update({"code": code, "ship": False})

        return TShirtSize.objects.filter(**queryset).only(
            "id",
            "name1",
            "sex",
            "size",
            "author",
            "material",
            "description",
            "t_shirt_preview",
            "available",
        )

    serializer_class = MerchandiseSerializer
    permission_classes = [permissions.IsAuthenticated]


class DiscountCouponSerializer(serpy.Serializer):
    name = serpy.StrField(call=True)
    discount = serpy.IntField()
    available = serpy.BoolField(call=True)


class DiscountCouponSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        code = self.kwargs.get("code")
        splitChar = "-"
        if code and splitChar in code:
            prefix, base_code = code.upper().split(splitChar)
            return DiscountCoupon.objects.filter(
                coupon_type__campaign__slug=self.request.subdomain,
                coupon_type__prefix=prefix,
                token=base_code,
            ).only(
                "discount",
            )
        return DiscountCoupon.objects.none()

    serializer_class = DiscountCouponSerializer
    permission_classes = [permissions.IsAuthenticated]


class PayCreateOrderDeserializer(serializers.Serializer):
    amount = serializers.IntegerField(required=True)
    products = serializers.JSONField()
    payment_subject = serializers.ChoiceField(choices=Payment.PAYMENT_SUBJECT)
    payment_category = serializers.ChoiceField(choices=Payment.PAYMENT_CATEGORY)
    client_ip = serializers.IPAddressField(required=True)


class PayUCreateOrderPost(UserAttendanceMixin, APIView):
    """Create new PayU order, save it as new Payment mode  and
    return response data with redirectUri for redirection client to
    PayU payment web page"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PayCreateOrderDeserializer

    def post(self, request):
        deserialized_data = PayCreateOrderDeserializer(data=request.data)
        if not deserialized_data.is_valid():
            return Response(
                {"error": deserialized_data.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ua = self.ua()

        # PayU authorization (get access token)
        payu = PayU(payu_conf=settings.PAYU_CONF)
        response_data = payu.authorize()
        access_token = response_data.get("access_token")
        if not access_token:
            return Response(response_data)

        # Pay create new order
        client_ip = deserialized_data.data["client_ip"]

        data = {
            "notifyUrl": f"{request.scheme}://{request.get_host()}{reverse('payu-notify-order-status')}",
            "amount": deserialized_data.data["amount"],
            "products": deserialized_data.data["products"],
            "customerIp": client_ip if client_ip else "127.0.0.1",
            "extOrderId": f"{request.user.id}-{int(timezone.now().timestamp())}",
            "userAttendance": ua,
            "paymentSubject": deserialized_data.data["payment_subject"],
            "paymentCategory": deserialized_data.data["payment_category"],
            "buyer": {
                "email": request.user.email,
                "phone": ua.userprofile.telephone if ua.userprofile.telephone else "",
                "firstName": request.user.first_name,
                "lastName": request.user.last_name,
                "language": (
                    ua.userprofile.language
                    if ua.userprofile.language
                    else settings.LANGUAGE_CODE
                ),
            },
        }
        return Response(payu.create_order(access_token, data))


class PayUPaymentNotifyPost(APIView):
    """After new PayU order was successfully created and payment was made,
    notification data is sended from PayU system to this URL endpoint.
    To update Payment model status (pay_type, status field) according
    order ID.

    PayU notifications:

    https://developers.payu.com/europe/docs/payment-flows/lifecycle/#notifications

    Pay signature verification:

    https://developers.payu.com/europe/docs/payment-flows/lifecycle/#signature-verification
    """

    authentication_classes = [PayUNotifyOrderRequestAuthentification]

    class PAYU_TO_PAYMENT_ORDER_STATUS(Enum):
        PENDING = Status.COMMENCED
        WAITING_FOR_CONFIRMATION = Status.WAITING_CONFIRMATION
        COMPLETED = Status.DONE
        CANCELED = Status.CANCELED

    def post(self, request):
        payu_signature_header = request.headers.get("OpenPayu-Signature")
        logger.info("Receive posted PayU notification order data <%s>.", request.data)
        if not payu_signature_header:
            logger.error("Missing OpenPayu-Signature request header.")
            return Response(
                {"error": _("Chybějící OpenPayu-Signature záhlaví request objektu.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payu_signature_header = payu_signature_header.split(";")
        signature = [
            i.split("=")[-1] for i in payu_signature_header if "signature" in i
        ][0]
        request_body_payu_second_key = (
            request.body.decode("utf-8")
            + settings.PAYU_CONF["PAYU_REST_API_SECOND_KEY_MD5"]
        )
        expected_signature = hashlib.md5(
            request_body_payu_second_key.encode("utf-8")
        ).hexdigest()
        # Verify request object signature
        if signature != expected_signature:
            logger.error(
                "Process of verification of PayU notification request header"
                " failed, incorrect signature <%s>.",
                signature,
            )
            return Response(
                {
                    "error": _(
                        "Proces ověření podpisu request objektu selhal,"
                        " nesprávny podpis <%(signature)s>."
                    )
                    % {"signature": signature}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = request.data
        order = data.get("order")
        order_status = order.get("status")
        pay_completed_order_status = "COMPLETED"
        pay_canceled_order_status = "CANCELED"

        # Update Payment model status
        if order:
            payment = Payment.objects.filter(order_id=order.get("extOrderId"))
            if payment:
                payment = payment[0]
                payment_status_text = [
                    i[1] for i in PAYMENT_STATUSES if i[0] == payment.status
                ][0]
                # Payment status is COMPLETED or CANCELED, we don't need change it
                if payment.status in (
                    self.PAYU_TO_PAYMENT_ORDER_STATUS[pay_completed_order_status].value,
                    self.PAYU_TO_PAYMENT_ORDER_STATUS[pay_canceled_order_status].value,
                ):
                    return Response(
                        {
                            "status": _(
                                "Platobní stav pre objednávku ID <%(order_id)s>"
                                " se nezměnil pre platobní stav objednávky"
                                " <%(order_status)s>."
                            )
                            % {
                                "order_id": order.get("extOrderId"),
                                "order_status": payment_status_text,
                            }
                        }
                    )
                # Save order new status as payment status
                payment.status = self.PAYU_TO_PAYMENT_ORDER_STATUS[order_status].value
                payment_status_text = [
                    i[1] for i in PAYMENT_STATUSES if i[0] == payment.status
                ][0]
                # If order status is COMPLETED save payment method type PBL, CARD_TOKEN, INSTALLMENTS
                if order_status == pay_completed_order_status:
                    payment.pay_type = order["payMethod"]["type"]
                    payment.save(update_fields=["pay_type", "status"])
                    logger.info(
                        "PayU order ID <%s> status changed to <%s>.",
                        order.get("extOrderId"),
                        order_status,
                    )
                    logger.info(
                        "Update payment model with order_id <%s>, status <%s>, and pay_type <%s>.",
                        payment.order_id,
                        payment.status,
                        payment.pay_type,
                    )

                else:
                    payment.save(update_fields=["status"])
                return Response(
                    {
                        "status": _(
                            "Platobní stav pre objednávku ID <%(order_id)s> byl změněn"
                            " na stav <%(order_status)s>."
                        )
                        % {
                            "order_id": order.get("extOrderId"),
                            "order_status": payment_status_text,
                        }
                    }
                )
            else:
                return Response(
                    {
                        "error": _(
                            "Neexistující platba s ID objednávky <%(order_id)s>."
                        )
                        % {"order_id": order.get("extOrderId")}
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )


class RequestSpecificFieldEmptyStrVal(RequestSpecificField):
    """Replace None value with empty string '' value"""

    def to_value(self, value):
        value = super().to_value(value)
        return value if value else ""


class UserAttendancePaymentWithRewardSerializer(serpy.Serializer):
    is_payment_with_reward = serpy.MethodField()

    def get_is_payment_with_reward(self, obj):
        payment = obj.representative_payment
        if payment:
            if payment.pay_category == "entry_fee-donation":
                entry_fee = payment.payu_ordered_product.get(
                    name__icontains="entry fee"
                ).unit_price
            else:
                entry_fee = payment.amount
            if payment.pay_subject:
                price_levels = obj.campaign.pricelevel_set.filter(
                    category__icontains="basic"
                    if payment.pay_subject == "individual"
                    else payment.pay_subject
                ).values(
                    "id",
                    "price",
                    "category",
                )
                return (
                    True
                    if list(
                        filter(
                            lambda x: x["price"] == entry_fee
                            and "reward" in x["category"],
                            price_levels,
                        )
                    )
                    else False
                )


class UserAttendanceSerializer(UserAttendancePaymentWithRewardSerializer):
    personal_data_opt_in = serpy.BoolField()
    discount_coupon = EmptyStrField()
    payment_subject = EmptyStrField(call=True)
    payment_type = EmptyStrField(call=True)
    payment_status = EmptyStrField()
    payment_amount = NullIntField(call=True)
    payment_category = EmptyStrField(call=True)
    approved_for_team = EmptyStrField()


class PersonalDetailsUserSerializer(serpy.Serializer):
    first_name = EmptyStrField()
    last_name = EmptyStrField()
    email = EmptyStrField()
    is_staff = serpy.BoolField()


class PersonalDetailsUserProfileSerializer(serpy.Serializer):
    id = serpy.IntField()
    nickname = NullStrField()
    sex = EmptyStrField()
    telephone = EmptyStrField()
    telephone_opt_in = serpy.BoolField()
    language = EmptyStrField()
    occupation = EmptyStrField()
    age_group = NullIntField()
    newsletter = EmptyStrField()


class RegisterChallengeSerializer(serpy.Serializer):
    personal_details = RequestSpecificField(
        lambda userprofile, req: PersonalDetailsUserSerializer(userprofile.user).data
        | PersonalDetailsUserProfileSerializer(userprofile).data
        | UserAttendanceSerializer(
            userprofile.userattendance_set.get(campaign__slug=req.subdomain)
        ).data
    )
    team_id = RequestSpecificField(
        lambda userprofile, req: userprofile.userattendance_set.get(
            campaign__slug=req.subdomain
        ).team_id
    )
    organization_id = RequestSpecificField(
        lambda userprofile, req: attrgetter_def_val(
            "team.subsidiary.company_id",
            userprofile.userattendance_set.get(campaign__slug=req.subdomain),
        )
    )
    subsidiary_id = RequestSpecificField(
        lambda userprofile, req: attrgetter_def_val(
            "team.subsidiary_id",
            userprofile.userattendance_set.get(campaign__slug=req.subdomain),
        )
    )
    t_shirt_size_id = RequestSpecificField(
        lambda userprofile, req: userprofile.userattendance_set.get(
            campaign__slug=req.subdomain
        ).t_shirt_size_id
    )
    organization_type = RequestSpecificFieldEmptyStrVal(
        lambda userprofile, req: attrgetter_def_val(
            "team.subsidiary.company.organization_type",
            userprofile.userattendance_set.get(campaign__slug=req.subdomain),
        )
    )
    city_slug = RequestSpecificField(
        lambda userprofile, req: attrgetter_def_val(
            "team.subsidiary.city.slug",
            userprofile.userattendance_set.get(campaign__slug=req.subdomain),
        )
    )
    city_wp_slug = RequestSpecificField(
        lambda userprofile, req: attrgetter_def_val(
            "team.subsidiary.city.get_wp_slug",
            userprofile.userattendance_set.get(campaign__slug=req.subdomain),
        )
    )


class RequestSpecificFieldDeserializer(serializers.Field):
    """Request specific field for deserializer class"""

    def get_attribute(self, instance):
        return instance

    def to_representation(self, instance):
        return attrgetter_def_val(self.source, instance)


class RequestSpecificUserAttendanceFieldDeserializer(RequestSpecificFieldDeserializer):
    """Request specific UserAttendance model instance field for deserializer class"""

    def to_representation(self, instance):
        return attrgetter_def_val(self.source, instance.get("user_attendance"))


class RegisterChallengeDeserializer(serializers.ModelSerializer):
    PAYMENT_SUBJECT = Payment.PAYMENT_SUBJECT[2:]

    id = serializers.IntegerField(
        read_only=True,
    )
    first_name = serializers.CharField(
        required=False,
    )
    last_name = serializers.CharField(
        required=False,
    )
    email = serializers.EmailField(
        required=False,
    )
    is_staff = serializers.BooleanField(
        read_only=True,
    )
    nickname = serializers.CharField(
        required=False,
        allow_null=True,
    )
    sex = serializers.ChoiceField(
        choices=UserProfile.GENDER,
        required=False,
    )
    telephone = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    telephone_opt_in = serializers.BooleanField(
        required=False,
    )
    language = serializers.ChoiceField(
        choices=UserProfile.LANGUAGE,
        required=False,
    )
    occupation_id = serializers.ChoiceField(
        choices=[],
        required=False,
    )
    age_group = serializers.ChoiceField(
        choices=UserProfile.AGE_GROUP,
        required=False,
    )
    newsletter = serializers.ChoiceField(
        choices=UserProfile.NEWSLETTER,
        required=False,
        allow_blank=True,
    )
    personal_data_opt_in = serializers.BooleanField(
        required=False,
    )
    discount_coupon = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    approved_for_team = serializers.ChoiceField(
        choices=UserAttendance.TEAMAPPROVAL,
        required=False,
    )
    payment_subject = serializers.ChoiceField(
        choices=PAYMENT_SUBJECT,
        required=False,
    )
    payment_amount = serializers.IntegerField(
        required=False,
    )
    payment_type = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    payment_category = serializers.ChoiceField(
        choices=Payment.PAYMENT_CATEGORY,
        required=False,
    )
    team_id = serializers.ChoiceField(
        choices=[],
        required=False,
        allow_null=True,
    )
    organization_id = RequestSpecificUserAttendanceFieldDeserializer(
        source="team.subsidiary.company_id",
        read_only=True,
    )
    subsidiary_id = RequestSpecificUserAttendanceFieldDeserializer(
        source="team.subsidiary_id",
        read_only=True,
    )
    t_shirt_size_id = serializers.ChoiceField(
        choices=[],
        required=False,
    )
    organization_type = RequestSpecificUserAttendanceFieldDeserializer(
        source="team.subsidiary.company.organization_type",
        read_only=True,
    )
    city_slug = RequestSpecificUserAttendanceFieldDeserializer(
        source="team.subsidiary.city.slug",
        read_only=True,
    )
    city_wp_slug = RequestSpecificUserAttendanceFieldDeserializer(
        source="team.subsidiary.city.get_wp_slug",
        read_only=True,
    )
    products = serializers.JSONField(required=False)

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "nickname",
            "sex",
            "telephone",
            "telephone_opt_in",
            "language",
            "occupation_id",
            "age_group",
            "newsletter",
            "personal_data_opt_in",
            "discount_coupon",
            "approved_for_team",
            "payment_subject",
            "payment_amount",
            "payment_status",
            "payment_type",
            "payment_category",
            "team_id",
            "organization_id",
            "subsidiary_id",
            "t_shirt_size_id",
            "organization_type",
            "city_slug",
            "city_wp_slug",
            "products",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._empty_string = ""
        # Dynamically set the choices for the fields
        self.fields["occupation_id"].choices = Occupation.objects.all().values_list(
            "id", "name"
        )
        self.fields["team_id"].choices = Team.objects.all().values_list("id", "name")
        t_shirts_queryset = TShirtSize.objects.filter(
            campaign__slug=kwargs["context"]["request"].subdomain,
            available=True,
            ship=True,
        ) | TShirtSize.objects.filter(
            code="nic",
        )
        self.fields["t_shirt_size_id"].choices = t_shirts_queryset.values_list(
            "id", "name"
        )

    def _update_model(self, validated_data, instance=None):
        """Update UserProfile model

        :param dict validated_data: input validated data
        :param UserProfile instance: UserProfile model instance with default None value

        :return None
        """
        none = None
        personal_data_opt_in = validated_data.pop("personal_data_opt_in", none)
        discount_coupon = validated_data.pop("discount_coupon", none)
        approved_for_team = validated_data.pop("approved_for_team", none)
        payment_subject = validated_data.pop("payment_subject", none)
        payment_category = validated_data.pop("payment_category", none)
        payment_amount = validated_data.pop("payment_amount", none)
        products = validated_data.pop("products", none)

        if "team_id" in validated_data:
            team_id = validated_data.pop("team_id")
            if team_id is None:
                team_id = "null"
        else:
            team_id = none
        t_shirt_size_id = validated_data.pop("t_shirt_size_id", none)

        self._get_or_create_user_attendance_model(instance)
        user, user_data = self._update_user_model(validated_data)
        user_profile, user_profile_fields = self._update_user_profile_model(
            validated_data
        )
        user_attendance_update_fields = self._update_user_attendance_model(
            personal_data_opt_in,
            team_id,
            t_shirt_size_id,
            discount_coupon,
            approved_for_team,
        )
        payment_update_fields = self._create_organization_coordinator_payment_model(
            payment_subject,
            payment_amount,
            payment_category,
            products,
            instance,
        )

        self._save_user_attendance_model(
            user_attendance_update_fields, payment_update_fields
        )

        result = {"user_attendance": self.user_attendance}
        result.update({"id": self.user_attendance.userprofile.id})

        # Del unnecessary discount_coupon_used field
        discount_coupon_used_field = "discount_coupon_used"
        if discount_coupon_used_field in user_attendance_update_fields.keys():
            del user_attendance_update_fields[discount_coupon_used_field]

        if user_data.keys():
            result.update(user.values(*user_data.keys())[0])
        if user_attendance_update_fields:
            result.update(user_attendance_update_fields)
        if user_profile_fields:
            result.update(user_profile.values(*user_profile_fields)[0])
        if payment_update_fields.keys():
            result.update(payment_update_fields)

        return result

    def _get_or_create_user_attendance_model(self, instance):
        """Get or create UserAttendance model

        :param instance: UserProfile model instance

        :return None
        """
        request = self.context["request"]
        if instance:
            self.user_attendance = instance.userattendance_set.get(
                campaign__slug=request.subdomain
            )
        else:
            self.user_attendance = request.user_attendance
            if not self.user_attendance:
                self.user_attendance = get_or_create_userattendance(
                    request, request.subdomain
                )

    def _update_user_model(self, validated_data, none=None):
        """Update User model

        :param dict validated_data: input validated data
        :param none none: None value

        :return User user: User model instance
               dict user_data: user data required for updating User model
        """
        # Update User model
        user_model_class = get_user_model()
        user_data = {
            "first_name": validated_data.pop("first_name", none),
            "last_name": validated_data.pop("last_name", none),
            "email": validated_data.pop("email", none),
        }
        user_data = {key: val for key, val in user_data.items() if val is not None}
        user = user_model_class.objects.filter(
            id=self.user_attendance.userprofile.user.id
        )
        user.update(**user_data)
        return user, user_data

    def _update_user_profile_model(self, validated_data):
        """Update UserProfile model

        :param dict validated_data: input validated data

        :return UserProfile user_profile: UserProfile model instance
               list user_profile_fields: UserProfile update fields list
        """
        # Update UserProfile model
        user_profile = UserProfile.objects.filter(
            id=self.user_attendance.userprofile.id
        )
        user_profile_fields = validated_data.keys()
        user_profile.update(**validated_data)
        return user_profile, user_profile_fields

    def _update_user_attendance_model(
        self,
        personal_data_opt_in,
        team_id,
        t_shirt_size_id,
        discount_coupon,
        approved_for_team,
    ):
        """
        Update UserAttendance model

        :param boolean|none personal_data_opt_in: UserAttendance model personal_data_opt_in
                                                  field value
        :param int|none team_id: UserAttendance model team_id field value
        :param int|none t_shirt_size_id: UserAttendance model t_shirt_size_id field value
        :param str|none discount_coupon: UserAttendance model discount_coupon field value
        :param str|none approved_for_team: UserAttendance model approved_for_team field value

        :return dict user_attendance_update_fields: UserAttendance model updated fields
                                                    with value
        """
        # Update UserAttendance model
        user_attendance_update_fields = {}
        if personal_data_opt_in:
            self.user_attendance.personal_data_opt_in = personal_data_opt_in
            user_attendance_update_fields[
                "personal_data_opt_in"
            ] = self.user_attendance.personal_data_opt_in

        if team_id:
            if team_id == "null":
                team_id = None
            self.user_attendance.team_id = team_id
            user_attendance_update_fields["team_id"] = self.user_attendance.team_id

        if t_shirt_size_id:
            self.user_attendance.t_shirt_size_id = t_shirt_size_id
            user_attendance_update_fields[
                "t_shirt_size_id"
            ] = self.user_attendance.t_shirt_size_id

        if discount_coupon is not None:
            if discount_coupon:
                self.user_attendance.discount_coupon = DiscountCoupon.objects.get(
                    token=discount_coupon.split("-")[-1]
                )
            else:
                # discount coupon is empty string ""
                self.user_attendance.discount_coupon = None
            user_attendance_update_fields["discount_coupon"] = (
                ""
                if self.user_attendance.discount_coupon is None
                else self.user_attendance.discount_coupon
            )
            self.user_attendance.discount_coupon_used = timezone.now()
            user_attendance_update_fields[
                "discount_coupon_used"
            ] = self.user_attendance.discount_coupon_used

        if approved_for_team:
            self.user_attendance.approved_for_team = approved_for_team
            user_attendance_update_fields[
                "approved_for_team"
            ] = self.user_attendance.approved_for_team

        return user_attendance_update_fields

    def _create_organization_coordinator_payment_model(
        self,
        payment_subject,
        payment_amount,
        payment_category,
        products,
        instance,
    ):
        """
        Create Payment model if payment subject is Company or School

        1. Individual payment subject create Payment model by PayU REST
           API URL endpoint
        2. Voucher payment subject create Payment model in the case when
           additional payment amount was choosed, created by PayU REST
           API URL endpoint
        3. School/Company payment subject create Payment model

        :param int|none payment_subject: Payment model payment subject field value
                                         see PAYMENT_SUBJECT const
        :param int|none payment_amount: Payment model payment amount field value
        :param str payment_category: Payment category, see Payment model
                                     PAYMENT_CATEGORY constant
        :param list products: PayU ordered products, list of dicts
                              [
                                {
                                  "name": "RTWBB challenge entry fee",
                                  "unitPrice": 400,
                                  "quantity": 1,
                                },
                                {
                                  "name": "RTWBB donation",
                                  "unitPrice": 500,
                                  "quantity": 1,
                                }
                              ]
        :param UserProfile instance: UserProfile model instance

        :return dict payment_update_fields: Payment model update fields dict
        """

        payment_update_fields = {}
        # Create Payment model for Company/School organization type
        if (
            payment_subject
            and payment_subject in ("school", "company")
            and payment_category
            and payment_amount is not None
            and products
        ):
            payu_ordered_products = []
            for product in products:
                query = {
                    "name": product["name"],
                    "unit_price": product["unitPrice"],
                    "quantity": product["quantity"],
                }
                payu_ordered_product = PayUOrderedProduct.objects.filter(**query)
                if not payu_ordered_product:
                    payu_ordered_product = PayUOrderedProduct(**query)
                    payu_ordered_product.save()
                else:
                    payu_ordered_product = payu_ordered_product[0]
                payu_ordered_products.append(payu_ordered_product)

            payment = None
            if instance:
                payment = Payment.objects.filter(
                    user_attendance=self.user_attendance,
                    pay_type="fc",
                ).last()

            if not payment:
                # Create Payment model only for Company/School coordinator (fc)
                payment = Payment(
                    user_attendance=self.user_attendance,
                    amount=payment_amount,
                    pay_type="fc",  # "fc" is company coordinator
                    pay_subject=payment_subject,
                    pay_category=payment_category,
                    status=Status.WAITING_CONFIRMATION,
                )
                payment.save()
            else:
                payment.amount = payment_amount
                payment.pay_subject = payment_subject
                payment.pay_category = payment_category
                payment.save(
                    update_fields=[
                        "amount",
                        "pay_subject",
                        "pay_category",
                    ]
                )
            payment.payu_ordered_product.set(payu_ordered_products)
            payment_update_fields = {
                "payment_subject": payment_subject,
                "payment_category": payment_category,
                "payment_amount": payment_amount,
            }
        return payment_update_fields

    def _save_user_attendance_model(
        self, user_attendance_update_fields, payment_update_fields
    ):
        """Update UserAttendance model fields

        :param dict user_attendance_update_fields: UserAttendance model
                                                   update fields with value
        :param dict payment_update_fields: Payment model update fields dict
        """
        approved_for_team = "approved_for_team"
        update_fields = list(user_attendance_update_fields.keys())
        if update_fields:
            if payment_update_fields:
                # Denorm fields
                denorm_fields = [
                    "representative_payment",
                    "payment_status",
                ]
                update_fields = [
                    *update_fields,
                    *denorm_fields,
                ]
            """
            When UserAttendance model changed, pre_save signal is triggered
            and handled by pre_user_team_changed() func, if save() method is
            called with update_fields param argument ["team"|"team_id"]
            approved_for_team field is not saved automatically inside
            pre_save signal callback func. And therefore we need explicitly
            add "approved_for_team" field name into save() method
            update_fields param arg if we update team or team_id field.
            """
            if not approved_for_team in update_fields and (
                "team" in update_fields or "team_id" in update_fields
            ):
                update_fields.append(approved_for_team)
            self.user_attendance.save(
                update_fields=update_fields,
            )
            try:
                self.user_attendance.refresh_from_db()
            except UserAttendance.DoesNotExist:
                pass

    def update(self, instance, validated_data):
        return self._update_model(validated_data, instance=instance)

    def create(self, validated_data):
        return self._update_model(validated_data=validated_data)

    def to_internal_value(self, data):
        if data.get("personal_details"):
            personal_details = data.pop("personal_details")
            for field in personal_details:
                data[field] = personal_details[field]
        return super().to_internal_value(data)

    def to_representation(self, value):
        data = super().to_representation(value)
        personal_details_fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "nickname",
            "sex",
            "telephone",
            "telephone_opt_in",
            "language",
            "occupation_id",
            "age_group",
            "newsletter",
            "personal_data_opt_in",
            "discount_coupon",
            "approved_for_team",
            "payment_subject",
            "payment_amount",
            "payment_status",
            "payment_type",
            "payment_category",
        )
        data["personal_details"] = {}
        for field in personal_details_fields:
            if field in data:
                data["personal_details"][field] = data.pop(field)
        # Reorder dict keys (personal_details key as first key)
        pos = list(data.keys()).index("personal_details")
        items = list(data.items())
        items.insert(0, items.pop(pos))
        return dict(items)

    def validate_discount_coupon(self, discount_coupon):
        if discount_coupon:
            discount_coupon_exist = DiscountCoupon.objects.filter(
                coupon_type__campaign__slug=self.context["request"].subdomain,
                token=discount_coupon.split("-")[-1],
            ).only("token")
            if not discount_coupon_exist:
                raise serializers.ValidationError(
                    _("Slevový kupón <%(coupon)s> neexistuje.")
                    % {"coupon": discount_coupon},
                )
            else:
                if not discount_coupon_exist[0].available():
                    raise serializers.ValidationError(
                        _("Slevový kupón <%(coupon)s> je neplatný.")
                        % {"coupon": discount_coupon},
                    )

        return discount_coupon

    def validate_email(self, email):
        if email and email in get_user_model().objects.exclude(
            email=self.context["request"].user.email
        ).values_list("email", flat=True):
            raise serializers.ValidationError(
                _(
                    "E-mail adresa <%(email)s> existuje."
                    " Použijte jinou e-mailovou adresu."
                )
                % {"email": email},
            )
        return email

    def get_payment_status(self, obj):
        ua = obj.get("user_attendance")
        return self._empty_string if not ua else ua.payment_status

    def get_payment_type(self, obj):
        ua = obj.get("user_attendance")
        payment_type = self._empty_string
        if ua:
            payment_type = ua.payment_type()
            payment_type = payment_type if payment_type else self._empty_string
        return payment_type


class RegisterChallengeSet(viewsets.ModelViewSet):
    _cache_timeout = 60 * 60 * 24 * 7

    def get_queryset(self):
        pk = self.kwargs.get("pk")
        if pk:
            return UserProfile.objects.filter(pk=pk)
        ua = self.request.user_attendance
        if not ua:
            ua = UserAttendance.objects.filter(
                userprofile__user=self.request.user,
                campaign__slug=self.request.subdomain,
            )
            if ua:
                ua = ua[0]
        return [ua.userprofile] if ua else []

    def list(self, request, *args, **kwargs):
        cache = None
        cached_data = None
        if hasattr(request.user, "userprofile"):
            cache = Cache(
                key=f"{register_challenge_serializer_base_cache_key_name}"
                f"{request.user.userprofile.id}:{request.subdomain}",
                timeout=self._cache_timeout,
            )
            cached_data = cache.data
        if not cached_data:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            cached_data = serializer.data
            if cache:
                cache.data = cached_data
        return Response(
            {
                "count": len(cached_data),
                "next": None,
                "previous": None,
                "results": cached_data,
            }
        )

    def retrieve(self, request, pk=None):
        userprofile = get_object_or_404(
            UserProfile.objects.all(),
            pk=pk,
        )
        self.check_object_permissions(request, userprofile)
        cache = Cache(
            key=f"{register_challenge_serializer_base_cache_key_name}"
            f"{userprofile.id}:{request.subdomain}",
            timeout=self._cache_timeout,
        )
        cached_data = cache.data
        if not cached_data:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            cached_data = serializer.data
            cache.data = cached_data
        return Response(
            {
                "count": len(cached_data),
                "next": None,
                "previous": None,
                "results": cached_data,
            }
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        if hasattr(request.user, "userprofile"):
            cache = Cache(
                key=f"{register_challenge_serializer_base_cache_key_name}"
                f"{request.user.userprofile.id}:{request.subdomain}"
            )
            if cache.data:
                del cache.data
        request_data = request.data.copy()
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @transaction.atomic
    def update(self, request, pk=None):
        if hasattr(request.user, "userprofile"):
            cache = Cache(
                key=f"{register_challenge_serializer_base_cache_key_name}"
                f"{pk}:{request.subdomain}"
            )
            if cache.data:
                del cache.data
        userprofile = get_object_or_404(UserProfile.objects.all(), pk=pk)
        self.check_object_permissions(request, userprofile)
        request_data = request.data.copy()
        serializer = self.get_serializer(
            UserProfile.objects.get(id=pk),
            data=request_data,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
            headers=headers,
        )

    def destroy(self, request, pk=None):
        userprofile = get_object_or_404(
            UserProfile.objects.all(),
            pk=pk,
        )
        self.check_object_permissions(request, userprofile)
        cache = Cache(
            key=f"{register_challenge_serializer_base_cache_key_name}"
            f"{pk}:{request.subdomain}"
        )
        if cache.data:
            del cache.data
        userprofile.user.delete()
        return super().destroy(request, pk)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return RegisterChallengeSerializer
        if self.action == "list":
            return RegisterChallengeSerializer
        else:
            return RegisterChallengeDeserializer

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperuser]


class UserDeserializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["firstName", "lastName"]
        extra_kwargs = {
            "firstName": {"source": "first_name"},
            "lastName": {"source": "last_name"},
        }


class UserSerializer(serpy.Serializer):
    firstName = serpy.StrField(attr="first_name")
    lastName = serpy.StrField(attr="last_name")


class UserAttendanceDeserializer(serializers.ModelSerializer):
    class Meta:
        model = UserAttendance
        fields = ["terms"]
        extra_kwargs = {
            "terms": {"source": "personal_data_opt_in"},
        }


class RegisterCoordinatorUserAttendanceSerializer(serpy.Serializer):
    terms = serpy.BoolField(attr="personal_data_opt_in")


class UserProfileDeserializer(serializers.HyperlinkedModelSerializer):
    user = UserDeserializer()

    class Meta:
        model = UserProfile
        fields = ["user", "newsletter", "phone"]
        extra_kwargs = {
            "phone": {"source": "telephone"},
        }


class UserProfileSerializer(serpy.Serializer):
    user = UserSerializer()
    newsletter = serpy.Field()
    phone = serpy.StrField(attr="telephone")


class RegisterCoordinatorDeserializer(serializers.HyperlinkedModelSerializer):

    user_profile = UserProfileDeserializer(source="userprofile")
    user_attendance = UserAttendanceDeserializer(required=False)

    organizationId = serializers.IntegerField(source="administrated_company_id")

    class Meta:
        model = CompanyAdmin
        fields = (
            "user_profile",
            "user_attendance",
            "organizationId",
            "jobTitle",
            "responsibility",
        )
        extra_kwargs = {
            "jobTitle": {"source": "motivation_company_admin"},
            "responsibility": {"source": "will_pay_opt_in"},
        }

    def _update_user_attendance(self, obj, data):
        if "personal_data_opt_in" in data:
            obj.personal_data_opt_in = data["personal_data_opt_in"]
        obj.save()

    def _update_user_profile(self, obj, data):

        if "telephone" in data:
            obj.telephone = data["telephone"]
        if "newsletter" in data:
            obj.newsletter = data["newsletter"]
        obj.save()

    def _update_user(self, obj, data):
        if "first_name" in data:
            obj.first_name = data["first_name"]
        if "last_name" in data:
            obj.last_name = data["last_name"]
        obj.save()

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        user_attendance = request.user_attendance
        if not user_attendance:
            user_attendance = get_or_create_userattendance(
                request,
                request.subdomain,
            )
        user_profile = user_attendance.userprofile
        user = user_profile.user

        user_attendance_values = validated_data.pop("user_attendance", {})
        self._update_user_attendance(user_attendance, user_attendance_values)
        user_profile_values = validated_data.pop("userprofile", {})
        self._update_user_profile(user_profile, user_profile_values)
        user_values = user_profile_values.pop("user", {})
        self._update_user(user, user_values)

        company_admin, _ = CompanyAdmin.objects.update_or_create(
            campaign=user_attendance.campaign,
            userprofile=user_attendance.userprofile,
            defaults=validated_data,
        )
        return company_admin

    @transaction.atomic
    def update(self, instance, validated_data):
        user_attendance = self.context.get("request").user_attendance
        user_profile = user_attendance.userprofile
        user = user_profile.user

        user_attendance_values = validated_data.pop("user_attendance", {})
        self._update_user_attendance(user_attendance, user_attendance_values)
        user_profile_values = validated_data.pop("userprofile", {})
        self._update_user_profile(user_profile, user_profile_values)
        user_values = user_profile_values.pop("user", {})
        self._update_user(user, user_values)

        return super().update(instance, validated_data)

    def to_internal_value(self, data):
        data = data.copy()
        data["user_attendance"] = {}
        data["user_profile"] = {}
        data["user_profile"]["user"] = {}

        if "firstName" in data:
            data["user_profile"]["user"]["firstName"] = data.pop("firstName")
        if "lastName" in data:
            data["user_profile"]["user"]["lastName"] = data.pop("lastName")
        if "newsletter" in data:
            data["user_profile"]["newsletter"] = data.pop("newsletter")
        if "phone" in data:
            data["user_profile"]["phone"] = data.pop("phone")
        if "terms" in data:
            data["user_attendance"]["terms"] = data.pop("terms")
        return super().to_internal_value(data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        user_attendance_data = representation.pop("user_attendance")
        user_profile_data = representation.pop("user_profile")

        representation["firstName"] = user_profile_data["user"]["firstName"]
        representation["lastName"] = user_profile_data["user"]["lastName"]
        representation["phone"] = user_profile_data["phone"]
        representation["newsletter"] = user_profile_data["newsletter"]
        representation["terms"] = user_attendance_data["terms"]

        return representation


class RegisterCoordinatorSerializer(serpy.Serializer):
    user_profile = UserProfileSerializer(attr="userprofile")
    user_attendance = RequestSpecificField(
        lambda _, req: RegisterCoordinatorUserAttendanceSerializer(
            req.user_attendance
        ).data
    )
    organizationId = NullIntField(attr="administrated_company_id")
    jobTitle = serpy.Field(attr="motivation_company_admin")
    responsibility = serpy.BoolField(attr="will_pay_opt_in")

    def _transform(self, item):

        user_profile = item.pop("user_profile")
        user_attendance = item.pop("user_attendance")

        item["firstName"] = user_profile["user"]["firstName"]
        item["lastName"] = user_profile["user"]["lastName"]
        item["phone"] = user_profile["phone"]
        item["newsletter"] = user_profile["newsletter"]
        item["terms"] = user_attendance["terms"]

        return item

    def to_value(self, instance):
        representation = super().to_value(instance)

        representation = (
            [self._transform(item) for item in representation]
            if self.many
            else self._transform(representation)
        )

        return representation


class RegisterCoordinatorSet(viewsets.ModelViewSet, UserAttendanceMixin):
    def get_queryset(self):
        pk = self.kwargs.get("pk")
        if pk:
            return CompanyAdmin.objects.filter(pk=pk)
        else:
            return CompanyAdmin.objects.filter(
                userprofile=self.ua().userprofile.pk,
                campaign__slug=self.request.subdomain,
            )

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperuser]

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return RegisterCoordinatorSerializer
        else:
            return RegisterCoordinatorDeserializer


class IsUserOrganizationAdmin(APIView):
    """Is user organization admin"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        is_user_organization_admin = False
        if hasattr(request.user, "userprofile"):
            if CompanyAdmin.objects.filter(
                userprofile=request.user.userprofile,
                company_admin_approved="approved",
                campaign__slug=request.subdomain,
                administrated_company__isnull=False,
            ):
                is_user_organization_admin = True
        return Response({"is_user_organization_admin": is_user_organization_admin})


class HasOrganizationAdmin(APIView):
    """Has organization admin"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, organization_id):

        return Response(
            {
                "has_organization_admin": (
                    True
                    if Company.objects.filter(
                        id=organization_id,
                        company_admin__isnull=False,
                        company_admin__campaign__slug=self.request.subdomain,
                        company_admin__company_admin_approved="approved",
                    )
                    else False
                )
            }
        )


class SendRegistrationConfirmationEmail(APIView):
    """Manually send confirmation email in case it hasn't been received"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        send_email = False
        if not has_verified_email(request.user):
            send_email_confirmation(request, request.user, request.user.email)
            send_email = True

        return Response(
            {
                "send_registration_confirmation_email": send_email,
            }
        )


class MyOrganizationAdmin(APIView, UserAttendanceMixin):
    """My organization admin"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        return Response(
            {
                "organization_admin": Company.objects.filter(
                    id=attrgetter_def_val(
                        attrs="team.subsidiary.company_id",
                        instance=self.ua(),
                    ),
                    company_admin__isnull=False,
                    company_admin__campaign__slug=self.request.subdomain,
                    company_admin__company_admin_approved="approved",
                )
                .annotate(
                    admin_name=ExpressionWrapper(
                        Concat(
                            F("company_admin__userprofile__user__first_name"),
                            Value(" "),
                            F("company_admin__userprofile__user__last_name"),
                        ),
                        output_field=CharField(),
                    ),
                    admin_email=F("company_admin__userprofile__user__email"),
                )
                .values("admin_name", "admin_email")
            }
        )


class EmailsField(serializers.Field):
    """Emails field

    Emails strings are separated by "," separator e.g.

    "test0@test.org,test1@test.org"
    """

    def to_representation(self, emails):
        return emails

    def to_internal_value(self, emails):
        emails = [email.strip() for email in emails.split(",")]
        for email in emails:
            validate_email(email)
        return emails


class SendChallengeTeamInvitationEmailDeserializer(serializers.Serializer):
    email = EmailsField(required=True)


class SendChallengeTeamInvitationEmailPost(UserAttendanceMixin, APIView):
    """Send challenge team invitation email"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SendChallengeTeamInvitationEmailDeserializer

    def post(self, request):
        deserialized_data = SendChallengeTeamInvitationEmailDeserializer(
            data=request.data
        )
        if not deserialized_data.is_valid():
            return Response(
                {"error": deserialized_data.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ua = self.ua()
        team_membership_invitation_mail.delay(
            user_attendance_id=ua.id,
            emails=deserialized_data.data["email"],
        )
        return Response(
            {"team_membership_invitation_email_sended": deserialized_data.data["email"]}
        )


class OpenApplicationWithRestToken(APIView):
    """Open application with REST API simple JWT token with customized
    lifetime
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, app_id):
        try:
            rough_url = settings.DPNK_MOBILE_APP_URLS[app_id]
        except IndexError:
            return Response(
                {
                    "error": _("ID aplikace <%(app_id)s> neexistuje.")
                    % {"app_id": app_id},
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        tokens = get_tokens_for_user(
            user=request.user,
            lifetime=settings.DPNK_MOBILE_APP_SIMPLE_JWT_TOKEN_CONFIG["lifetime"],
            lifetime_unit=settings.DPNK_MOBILE_APP_SIMPLE_JWT_TOKEN_CONFIG[
                "lifetime_unit"
            ],
        )
        return Response(
            {
                "app_url": rough_url.format(
                    auth_token=tokens["access"]["token"],
                    campaign_slug_identifier=self.request.campaign.slug_identifier,
                ),
                "token_expiration": tokens["access"]["expiration"],
            }
        )


class StravaConnect(APIView):
    """Connect to Strava account"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, scope=None):
        sclient = stravalib.Client()
        return Response(
            {
                "auth_url": sclient.authorization_url(
                    client_id=settings.STRAVA_CLIENT_ID,
                    redirect_uri=settings.STRAVA_APP_REDIRECT_URL,
                    scope="activity:read_all"
                    if scope == "read_all"
                    else "activity:read",
                )
            }
        )


class StravaAuth(APIView):
    """Auth to Strava account and create/update StravaAccount DB model"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, code=None):
        if code is None:
            Response(
                {
                    "error": _("Chybějící Strava API autorizační kód <%(code)s>.")
                    % {"code": code},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        sclient = stravalib.Client()
        try:
            token_response = sclient.exchange_code_for_token(
                client_id=settings.STRAVA_CLIENT_ID,
                client_secret=settings.STRAVA_CLIENT_SECRET,
                code=code,
            )
            acct, created = StravaAccount.objects.get_or_create(
                user_id=request.user.id,
            )
            acct.strava_username = sclient.get_athlete().username or ""
            acct.first_name = sclient.get_athlete().firstname or ""
            acct.last_name = sclient.get_athlete().lastname or ""
            acct.access_token = token_response["access_token"]
            acct.refresh_token = token_response["refresh_token"]
            acct.save()
        except (stravalib.exc.AccessUnauthorized, stravalib.exc.Fault) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        strava_account = StravaAccountSet.as_view({"get": "list"}, sync="sync")(
            request._request
        ).data["results"]
        response = {
            "account_status": "created" if created else "updated",
            "account": strava_account,
        }
        return Response(response)


class StravaDisconnect(APIView):
    """Disconnect Strava account"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            strava_account = request.user.stravaaccount
        except StravaAccount.DoesNotExist:
            return Response(
                {
                    "error": _("Strava užívateľský účet <%(user)s> neexistuje.")
                    % {"user": request.user}
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        sclient = stravalib.Client(access_token=strava_account.access_token)
        try:
            sclient.deauthorize()
        except AccessUnauthorized:
            pass
        strava_account.delete()
        return Response(
            {
                "success": _(
                    "Strava užívateľský účet <%(user)s> bol úspěšně odstraněn."
                )
                % {"user": request.user}
            }
        )


class DataReportResults(UserAttendanceMixin, APIView):
    """Metabase data resuls report URL

    1. Organization regulariry (Company/City organizator),
    2. Team regularity in the cities (Company/City organizator),
    3. Organization/city performance (Company/City organizator),
    4. Orgaznizations review
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, report_type):
        self.user_attendance = self.ua()
        url = None
        if "regularity" == report_type:
            base_url = settings.METABASE_DPNK_REGULARITY_RESULTS_DATA_REPORT_URL
            # Organization admin
            if (
                attrgetter_def_val(
                    "related_company_admin.is_approved", self.user_attendance
                )
                or CompanyAdmin.objects.filter(
                    userprofile=self.user_attendance.userprofile
                )
            ) and not self.user_attendance.userprofile.administrated_cities.all():
                url = concat_all(
                    base_url,
                    "?org=",
                    self.user_attendance.company(),
                    "&campaign_year=",
                    self.user_attendance.campaign.year,
                )
            # City admin
            elif self.user_attendance.userprofile.administrated_cities.all() and not (
                attrgetter_def_val(
                    "related_company_admin.is_approved", self.user_attendance
                )
                or CompanyAdmin.objects.filter(
                    userprofile=self.user_attendance.userprofile
                )
            ):
                url = concat_all(
                    base_url,
                    "?campaign_year=",
                    self.user_attendance.campaign.year,
                    concat_cities_into_url_param(self.user_attendance.userprofile),
                )
            # Organization admin (registered/unregistered into challenge) or City admin
            elif self.user_attendance.userprofile.administrated_cities.all() and (
                attrgetter_def_val(
                    "related_company_admin.is_approved", self.user_attendance
                )
                or CompanyAdmin.objects.filter(
                    userprofile=self.user_attendance.userprofile
                )
            ):
                url = concat_all(
                    base_url,
                    "?org=",
                    self.user_attendance.company(),
                    concat_cities_into_url_param(self.user_attendance.userprofile),
                    "&campaign_year=",
                    self.user_attendance.campaign.year,
                )
            # Basic challenge member
            else:
                url = concat_all(
                    base_url,
                    "?campaign_year=",
                    self.user_attendance.campaign.year,
                    concat_cities_into_url_param(self.user_attendance.userprofile),
                )
        elif "team-regularity-city" == report_type:
            base_url = (
                settings.METABASE_DPNK_TEAM_REGULARITY_CITY_RESULTS_DATA_REPORT_URL
            )
            # Organization admin (registered/unregistered into challenge) or City admin
            if self.user_attendance.userprofile.administrated_cities.all() or (
                attrgetter_def_val(
                    "related_company_admin.is_approved", self.user_attendance
                )
                or CompanyAdmin.objects.filter(
                    userprofile=self.user_attendance.userprofile
                )
            ):
                url = concat_all(
                    base_url,
                    "?campaign_year=",
                    self.user_attendance.campaign.year,
                    concat_cities_into_url_param(self.user_attendance.userprofile),
                )
            # Basic challenge member
            else:
                url = concat_all(
                    base_url,
                    "?campaign_year=",
                    self.user_attendance.campaign.year,
                    f"&city={self.user_attendance.team.subsidiary.city.name}",
                )
        elif "performance-organization" == report_type:
            base_url = (
                settings.METABASE_DPNK_PERFORMANCE_ORGANIZATION_RESULTS_DATA_REPORT_URL
            )
            url = concat_all(
                base_url,
                "?org=",
                self.user_attendance.company(),
                "&campaign_year=",
                self.user_attendance.campaign.year,
            )
        elif "performance-city" == report_type:
            base_url = settings.METABASE_DPNK_PERFORMANCE_CITY_RESULTS_DATA_REPORT_URL
            url = concat_all(
                base_url,
                "?campaign_year=",
                self.user_attendance.campaign.year,
                concat_cities_into_url_param(self.user_attendance.userprofile),
            )
        elif "organizations-review" == report_type:
            base_url = (
                settings.METABASE_DPNK_ORGANIZATION_REVIEW_RESULTS_DATA_REPORT_URL
            )
            url = concat_all(
                base_url,
            )
        return Response({"data_report_url": url})


class DataReportResultsByChallenge(UserAttendanceMixin, APIView):
    """Metabase data report results by challenge URL

    1. May challenge
    2. September and january challenge
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, challenge):
        self.user_attendance = self.ua()
        url = None
        if "may" == challenge:
            url = concat_all(
                settings.METABASE_DPNK_MAY_CHALLENGE_DATA_REPORT_URL,
                "?u%25C5%25BEivatelsk%25C3%25A9_jm%25C3%25A9no=",
                self.user_attendance.userprofile.user.username,
                "&organizace=",
                self.user_attendance.company(),
                "&m%25C4%259Bsto=",
                attrgetter_def_val("team.subsidiary.city", self.user_attendance),
                "&ro%25C4%258Dn%25C3%25ADk_v%25C3%25BDzvy=",
                self.user_attendance.campaign.year,
            )
        elif "september-january" == challenge:
            base_url = (
                settings.METABASE_DPNK_SEPTEMBER_JANUARY_CHALLENGE_DATA_REPORT_URL
            )
            url = concat_all(
                base_url,
                "?u%25C5%25BEivatelsk%25C3%25A9_jm%25C3%25A9no=",
                self.user_attendance.userprofile.user.username,
                "&m%25C4%259Bsto=",
                attrgetter_def_val("team.subsidiary.city", self.user_attendance),
                "&ro%25C4%258Dn%25C3%25ADk_v%25C3%25BDzvy=",
                self.user_attendance.campaign.year,
            )
        return Response({"data_report_url": url})


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
router.register(
    r"strava_account/(?P<sync>(sync))", StravaAccountSet, basename="strava-account-sync"
)
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
router.register(
    r"merchandise/(?P<code>[\w\-]+)", MerchandiseSet, basename="merchandise-code"
)
router.register(r"merchandise", MerchandiseSet, basename="merchandise")
router.register(
    "discount-coupon/(?P<code>[\w\-]+)",
    DiscountCouponSet,
    basename="discount-coupon-by-code",
)
router.register(
    "register-challenge",
    RegisterChallengeSet,
    basename="register-challenge",
)
router.register(
    "register-coordinator",
    RegisterCoordinatorSet,
    basename="register-coordinator",
)
