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
from rest_framework import routers, serializers, viewsets
from rest_framework.exceptions import APIException
from models import GpxFile, UserAttendance, Campaign
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError


class DuplicateGPX(APIException):
    status_code = 409
    default_detail = "GPX for this day and trip already uploaded"


class GPXParsingFail(APIException):
    status_code = 400
    default_detail = "Can't parse GPX file"


class CampaignDoesNotExist(APIException):
    status_code = 404
    default_detail = "Campaign with this slug not found"


class GpxFileSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        user = self.context['request'].user
        subdomain = self.context['request'].subdomain
        try:
            campaign = Campaign.objects.get(slug=subdomain)
        except Campaign.DoesNotExist:
            raise CampaignDoesNotExist

        try:
            user_attendance = UserAttendance.objects.get(userprofile__user=user, campaign=campaign)
        except UserAttendance.DoesNotExist:
            user_attendance = UserAttendance(
                userprofile=user.userprofile,
                campaign=campaign,
                approved_for_team='undecided',
            )
            user_attendance.save()
        validated_data['user_attendance'] = user_attendance
        try:
            instance = GpxFile(**validated_data)
            instance.clean()
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
        fields = ('trip_date', 'direction', 'file')
        read_only_fields = ('track',)


class GpxFileSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return GpxFile.objects.filter(user_attendance__userprofile__user=self.request.user)
    serializer_class = GpxFileSerializer

router = routers.DefaultRouter()
router.register(r'gpx', GpxFileSet, base_name="gpxfile")
