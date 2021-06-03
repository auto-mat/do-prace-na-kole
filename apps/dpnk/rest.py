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

import denorm

from django.core.exceptions import ValidationError
from django.db.models import F, Window
from django.db.models.functions import DenseRank

from donation_chooser.rest import organization_router

from drf_extra_fields.geo_fields import PointField

from memoize import mproperty
from notifications.models import Notification

import photologue

from rest_framework import mixins, permissions, routers, serializers, viewsets
from rest_framework.reverse import reverse

from .middleware import get_or_create_userattendance
from .models import (
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
from .models.company import CompanyInCampaign
from .models.subsidiary import SubsidiaryInCampaign

from stravasync.models import StravaAccount


class RequestSpecificField(serializers.Field):
    def __init__(self, method, *args, **kwargs):
        self.method = method
        return super().__init__(*args, **kwargs)

    def get_attribute(self, instance):
        # We pass the object instance onto `to_representation`,
        # not just the field attribute.
        return instance

    def to_representation(self, value):
        """
        Serialize the value's class name.
        """
        return self.method(value, self.context["request"])


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


class CompetitionDoesNotExist(serializers.ValidationError):
    status_code = 405
    default_detail = {"competition": "Competition with this slug not found"}


class DistanceMetersSerializer(serializers.IntegerField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        return value / 1000

    def to_representation(self, data):
        value = round(data * 1000)
        return super().to_representation(value)


class MinimalTripSerializer(serializers.ModelSerializer):
    distanceMeters = DistanceMetersSerializer(
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


class TripSerializer(MinimalTripSerializer):
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


class TripDetailSerializer(TripSerializer):
    class Meta(TripSerializer.Meta):
        extra_kwargs = {}


class CollegueTripSeralizer(MinimalTripSerializer):
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

    class Meta:
        model = Trip
        fields = (
            "id",
            "trip_date",
            "direction",
            "commuteMode",
            "durationSeconds",
            "distanceMeters",
            "sourceApplication",
            "user",
            "user_attendance",
            "team",
            "subsidiary",
            "has_track",
        )


class TripUpdateSerializer(TripSerializer):
    class Meta(TripSerializer.Meta):
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
        if self.request.method == "PUT":
            return TripUpdateSerializer
        return TripDetailSerializer if self.action == "retrieve" else TripSerializer

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
        if self.request.method == "PUT":
            return TripUpdateSerializer
        return TripDetailSerializer if self.action == "retrieve" else TripSerializer

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
        qs = Trip.objects.filter(
            user_attendance__team__subsidiary__company=self.ua().team.subsidiary.company.pk,
            user_attendance__campaign=self.ua().campaign,
        ).select_related(
            "user_attendance",
            "user_attendance__team",
            "user_attendance__team__subsidiary",
        )
        start_date = self.request.query_params.get("start", None)
        end_date = self.request.query_params.get("end", None)
        if start_date and end_date:
            qs = qs.filter(
                date__range=[start_date, end_date],
            )
        return qs

    serializer_class = CollegueTripSeralizer
    permission_classes = [permissions.IsAuthenticated]


class CompetitionSerializer(serializers.HyperlinkedModelSerializer):
    results = serializers.SerializerMethodField()

    class Meta:
        model = Competition
        fields = (
            "id",
            "name",
            "slug",
            "competitor_type",
            "competition_type",
            "url",
            "results",
            "priority",
        )

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
    def to_representation(self, value):
        try:
            cic = value.__company_in_campaign
        except AttributeError:
            value.__company_in_campaign = CompanyInCampaign(
                value, self.context["request"].campaign
            )
            cic = value.__company_in_campaign
        return self.method(cic, self.context["request"])


class CompanySerializer(serializers.HyperlinkedModelSerializer):
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

    class Meta:
        model = Company
        fields = (
            "id",
            "name",
            "subsidiaries",
            "eco_trip_count",
            "frequency",
            "emissions",
            "distance",
            "icon",
            "icon_url",
            "gallery",
            "gallery_slug",
            "working_rides_base_count",
        )


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
    def to_representation(self, value):
        try:
            sic = value.__subsidiary_in_campaign
        except AttributeError:
            value.__subsidiary_in_campaign = SubsidiaryInCampaign(
                value, self.context["request"].campaign
            )
            sic = value.__subsidiary_in_campaign
        return self.method(sic, self.context["request"])


class MinimalSubsidiarySerializer(serializers.HyperlinkedModelSerializer):
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
    rest_url = RequestSpecificField(
        lambda sub, req: serializers.HyperlinkedRelatedField(
            read_only=True, view_name="subsidiary-detail"
        ).get_url(sub, "subsidiary-detail", req, None)
    )

    class Meta:
        model = Subsidiary
        fields = (
            "id",
            "address_street",
            "city",
            "frequency",
            "distance",
            "icon_url",
            "rest_url",
            "emissions",
            "eco_trip_count",
            "working_rides_base_count",
        )


class SubsidiarySerializer(MinimalSubsidiarySerializer):
    teams = SubsidiaryInCampaignField(
        lambda sic, req: [
            MinimalTeamSerializer(team, context={"request": req}).data
            for team in sic.teams
        ]
    )

    class Meta:
        model = Subsidiary
        fields = (
            "id",
            "address_street",
            "company",
            "teams",
            "city",
            "eco_trip_count",
            "frequency",
            "emissions",
            "distance",
            "icon",
            "icon_url",
            "gallery",
            "gallery_slug",
            "working_rides_base_count",
        )


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


class MinimalUserAttendanceSerializer(serializers.HyperlinkedModelSerializer):
    distance = serializers.FloatField(
        source="trip_length_total",
        help_text="Distance ecologically traveled in Km",
    )
    rest_url = RequestSpecificField(
        lambda ua, req: serializers.HyperlinkedRelatedField(
            read_only=True, view_name="userattendance-detail"
        ).get_url(ua, "userattendance-detail", req, None)
    )
    emissions = serializers.JSONField(
        source="get_emissions",
        help_text="Emission reduction estimate",
    )
    working_rides_base_count = serializers.IntegerField(
        source="get_working_rides_base_count",
        help_text="Max number of possible trips",
    )
    is_me = RequestSpecificField(
        lambda ua, req: True if ua.userprofile.user.pk == req.user.pk else False,
    )

    class Meta:
        model = UserAttendance
        fields = (
            "id",
            "rest_url",
            "name",
            "frequency",
            "distance",
            "avatar_url",
            "eco_trip_count",
            "working_rides_base_count",
            "emissions",
            "is_me",
        )


class UserAttendanceSerializer(MinimalUserAttendanceSerializer):
    remaining_rides_count = serializers.IntegerField(
        source="get_remaining_rides_count",
        help_text="Remaining number of possible trips",
    )
    sesame_token = RequestSpecificField(
        lambda ua, req: ua.userprofile.get_sesame_token()
        if ua.userprofile.user.pk == req.user.pk
        else None,
    )
    registration_complete = RequestSpecificField(
        lambda ua, req: ua.entered_competition(),
    )
    gallery = RequestSpecificField(
        lambda ua, req: serializers.HyperlinkedRelatedField(
            read_only=True,
            view_name="gallery-detail",
        ).get_url(
            ua.userprofile.get_gallery(),
            "gallery-detail",
            req,
            None,
        ),
    )
    unread_notification_count = RequestSpecificField(
        lambda ua, req: ua.notifications().filter(unread=True).count()
        if ua.userprofile.user.pk == req.user.pk
        else None,
    )

    class Meta:
        model = UserAttendance
        fields = (
            "id",
            "name",
            "frequency",
            "distance",
            "points",
            "points_display",
            "eco_trip_count",
            "team",
            "emissions",
            "avatar_url",
            "working_rides_base_count",
            "remaining_rides_count",
            "sesame_token",
            "registration_complete",
            "gallery",
            "unread_notification_count",
        )


class AllUserAttendanceSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    def get_queryset(self):
        denorm.flush()
        return UserAttendance.objects.all().select_related("userprofile__user")

    serializer_class = UserAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]


class MyUserAttendanceSet(UserAttendanceMixin, viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        denorm.flush()
        return UserAttendance.objects.filter(
            id=self.ua().id,
        ).select_related("userprofile__user")

    serializer_class = UserAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]


class MinimalTeamSerializer(serializers.HyperlinkedModelSerializer):
    distance = serializers.FloatField(
        source="get_length",
        help_text="Distance ecologically traveled in Km",
        read_only=True,
    )
    frequency = serializers.FloatField(
        source="get_frequency",
        help_text="Fequeny of travel in as a fraction (multiply by 100 to get percentage)",
        read_only=True,
    )
    emissions = serializers.JSONField(
        source="get_emissions",
        help_text="Emission reduction estimate",
        read_only=True,
    )
    eco_trip_count = serializers.IntegerField(
        source="get_eco_trip_count",
        help_text="Number of ecologically traveled trips by team members",
        read_only=True,
    )
    working_rides_base_count = serializers.IntegerField(
        source="get_working_trips_count",
        read_only=True,
    )
    rest_url = RequestSpecificField(
        lambda team, req: serializers.HyperlinkedRelatedField(
            read_only=True, view_name="team-detail"
        ).get_url(team, "team-detail", req, None)
    )

    class Meta:
        model = Team
        fields = (
            "name",
            "id",
            "frequency",
            "distance",
            "icon_url",
            "rest_url",
            "eco_trip_count",
            "emissions",
            "working_rides_base_count",
        )


class TeamSerializer(MinimalTeamSerializer):
    members = MinimalUserAttendanceSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Team
        fields = (
            "name",
            "icon",
            "id",
            "subsidiary",
            "members",
            "frequency",
            "distance",
            "eco_trip_count",
            "working_rides_base_count",
            "emissions",
            "campaign",
            "icon_url",
            "gallery",
            "gallery_slug",
        )
        read_only_fields = (
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
        )


class TeamSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    def get_queryset(self):
        return Team.objects.filter(
            campaign__slug=self.request.subdomain,
        )

    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]


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


class CompetitionResultSerializer(serializers.HyperlinkedModelSerializer):
    user_attendance = serializers.CharField(read_only=True)
    company = serializers.CharField(read_only=True)
    place = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source="__str__", read_only=True)
    icon_url = serializers.CharField(source="get_icon_url", read_only=True)
    divident = serializers.IntegerField(source="result_divident", read_only=True)
    divisor = serializers.IntegerField(source="result_divisor", read_only=True)
    emissions = serializers.JSONField(source="get_emissions", read_only=True)

    class Meta:
        model = CompetitionResult
        fields = (
            "id",
            "user_attendance",
            "team",
            "company",
            "competition",
            "result",
            "place",
            "name",
            "icon_url",
            "frequency",
            "divident",
            "divisor",
            "distance",
            "emissions",
        )


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


class CityInCampaignSerializer(serializers.HyperlinkedModelSerializer):
    city__name = serializers.CharField(source="city.name")
    city__location = PointField(source="city.location")
    city__wp_url = serializers.CharField(source="city.get_wp_url")

    class Meta:
        model = CityInCampaign
        fields = (
            "id",
            "city__name",
            "city__location",
            "city__wp_url",
            "competitor_count",
        )


class CityInCampaignSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return CityInCampaign.objects.filter(campaign__slug=self.request.subdomain)

    serializer_class = CityInCampaignSerializer
    permission_classes = [permissions.AllowAny]


class CitySerializer(serializers.HyperlinkedModelSerializer):
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
            serializers.HyperlinkedRelatedField(  # noqa
                read_only=True,
                view_name="subsidiary-detail",
            ).get_url(subsidiary, "subsidiary-detail", req, None)
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
    wp_url = serializers.CharField(
        source="get_wp_url",
    )

    class Meta:
        model = City
        fields = (
            "id",
            "name",
            "location",
            "wp_url",
            "competitor_count",
            "trip_stats",
            # 'frequency', TODO
            "emissions",
            "subsidiaries",
            "eco_trip_count",
            "distance",
            "organizer",
            "organizer_url",
            "description",
            "competitions",
        )


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


class CommuteModeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CommuteMode
        fields = (
            "id",
            "slug",
            "does_count",
            "eco",
            "distance_important",
            "duration_important",
            "minimum_distance",
            "minimum_duration",
            "description_en",
            "description_cs",
            "icon",
            "name_en",
            "name_cs",
            "points",
            # icon TODO
        )


class CommuteModeSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return CommuteMode.objects.all()

    serializer_class = CommuteModeSerializer
    permission_classes = [permissions.IsAuthenticated]


class CampaignTypeSerializer(serializers.HyperlinkedModelSerializer):
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
        return False


class CampaignTypeSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return CampaignType.objects.all()

    serializer_class = CampaignTypeSerializer
    permission_classes = [IsAdminOrReadOnly]


class PhaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Phase
        fields = (
            "phase_type",
            "date_from",
            "date_to",
        )


class CampaignSerializer(serializers.HyperlinkedModelSerializer):
    phase_set = PhaseSerializer(many=True, read_only=True)

    class Meta:
        model = Campaign
        fields = (
            "id",
            "slug",
            "days_active",
            "year",
            "campaign_type",
            "phase_set",
        )


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


class NotificationSerializer(serializers.HyperlinkedModelSerializer):
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

    class Meta:
        model = Notification
        fields = (
            "id",
            "level",
            "unread",
            "deleted",
            "verb",
            "description",
            "timestamp",
            "data",
            "mark_as_read",
            "mark_as_unread",
        )


class NotificationSet(UserAttendanceMixin, viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return self.ua().notifications()

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]


class PhotoSerializer(serializers.HyperlinkedModelSerializer):
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

    serializer_class = PhotoSerializer
    permission_classes = [permissions.IsAuthenticated]


class PhotoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = photologue.models.Photo
        fields = (
            "id",
            "caption",
            "image",
        )


class GallerySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = photologue.models.Gallery
        fields = (
            "title",
            "slug",
            "description",
            "photos",
        )


class GallerySet(
    UserAttendanceMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    def get_queryset(self):
        return photologue.models.Gallery.objects.all()

    serializer_class = GallerySerializer
    permission_classes = [permissions.IsAuthenticated]


class StravaAccountSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = StravaAccount
        fields = (
            "strava_username",
            "first_name",
            "last_name",
            "user_sync_count",
            "errors",
        )


class StravaAccountSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return StravaAccount.objects.filter(user=self.request.user)

    serializer_class = StravaAccountSerializer
    permission_classes = [permissions.IsAuthenticated]


class LandingPageIconSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LandingPageIcon
        fields = (
            "file",
            "role",
            "min_frequency",
            "max_frequency",
        )


class LandingPageIconSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return LandingPageIcon.objects.all()

    serializer_class = LandingPageIconSerializer
    permission_classes = [permissions.IsAuthenticated]


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
