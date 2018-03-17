# -*- coding: utf-8 -*-
# Author: Timothy Hobbs <timothy <at> hobbs.cz>

import logging
from datetime import datetime

from celery import shared_task

from django.conf import settings
from django.contrib.gis.geos import (LineString, MultiLineString)

from dpnk.forms import FullGpxFileForm
from dpnk.models.gpxfile import GpxFile
from dpnk.models.phase import Phase
from dpnk.models.user_attendance import UserAttendance

import polyline

import stravalib

from stravasync import hashtags
from stravasync.commute_modes import get_commute_mode
from stravasync.models import StravaAccount

logger = logging.getLogger(__name__)


def get_track(polyline_data):
    coords = polyline.decode(polyline_data)
    coords = [(x, y) for (y, x) in coords]
    return MultiLineString([LineString(coords, srid=4326)], srid=4326)


@shared_task(bind=False)
def sync_task(strava_account_id):
    sync(strava_account_id, manual_sync=False)


def sync(strava_account_id, manual_sync=True):
    """
    Sync with a specific strava account.

    May raise stravalib.exc.RateLimitExceeded
    """
    strava_account = StravaAccount.objects.get(id=strava_account_id)
    if manual_sync:
        strava_account.user_sync_count += 1
    else:
        strava_account.user_sync_count = 0
    sclient = stravalib.Client(access_token=strava_account.access_token)
    earliest_start_date, latest_end_date = Phase.get_active_range('competition')
    activities = sclient.get_activities(
        after=datetime.combine(earliest_start_date, datetime.min.time()),
        before=datetime.combine(latest_end_date, datetime.max.time()),
    )
    strava_account.last_sync_time = datetime.now()
    synced_activities = 0
    synced_trips = 0
    new_trips = 0
    for activity in activities:
        synced_activities += 1
        try:
            campaign, direction = hashtags.get_campaign_and_direction(activity.name)
        except hashtags.NoValidHashtagException as e:
            continue
        synced_trips += 1
        user_attendance = UserAttendance.objects.get(campaign=campaign, userprofile=strava_account.user.userprofile)
        trip_date = activity.start_date.date()
        exists = GpxFile.objects.filter(
            trip_date=trip_date,
            direction=direction,
            user_attendance=user_attendance,
        ).exists()
        if not exists:
            new_trips += 1

        if activity.map.summary_polyline and (not exists) and settings.STRAVA_FINE_POLYLINES:
            activity = sclient.get_activity(activity.id)
        form_data = {
            'trip_date': trip_date,
            'direction': direction,
            'user_attendance': user_attendance.id,
            'commute_mode': get_commute_mode(activity.type).id,
            'distance': round(stravalib.unithelper.meters(activity.distance).get_num()),
            'duration': activity.elapsed_time.total_seconds(),
            'source_application': 'strava',
            'from_application': True,
        }
        if activity.map.summary_polyline and (not exists):
            form_data['track'] = get_track(activity.map.summary_polyline)
        if activity.map.polyline:
            form_data['track'] = get_track(activity.map.polyline)
        gpx_file_form = FullGpxFileForm(data=form_data)

        if gpx_file_form.is_valid():
            gpx_file_form.save()
        else:
            logger.error("Form error:")
            logger.error(gpx_file_form.errors)
    strava_account.save()
    return {
        "new_trips": new_trips,
        "synced_trips": synced_trips,
        "synced_activities": synced_activities,
    }


@shared_task(bind=False)
def sync_stale(min_time_between_syncs=60 * 60 * 12, max_batch_size=300):
    """
    Syncs any accounts which have not been synced for at least min_time_between_syncs seconds.
    Will sync at most max_batch_size accounts.
    You need to run this multiple times at > 15 minute intervals
    if you wish to sync with more accounts than can by synced safely within your api request rate limit.

    The sync_stale task will either consume 1 request per stale account as well as 1 request per new trip if STRAVA_FINE_POLYLINES is True.
    """
    for account in StravaAccount.stale_accounts(min_time_between_syncs).all():
        if max_batch_size <= 0:
            return
        sync(account.id)
        max_batch_size -= 1
