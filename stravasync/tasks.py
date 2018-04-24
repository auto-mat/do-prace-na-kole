# -*- coding: utf-8 -*-
# Author: Timothy Hobbs <timothy <at> hobbs.cz>

import logging
from datetime import datetime

from celery import shared_task

from django.conf import settings
from django.contrib.gis.geos import (LineString, MultiLineString)

from dpnk.forms import FullTripForm
from dpnk.models.phase import Phase
from dpnk.models.trip import Trip
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
    campaigns = []
    for competition_phase in Phase.get_active().filter(phase_type='competition'):
        campaigns.append(competition_phase.campaign)
    hashtag_table = hashtags.HashtagTable(campaigns)
    activities = sclient.get_activities(
        after=datetime.combine(earliest_start_date, datetime.min.time()),
        before=datetime.combine(latest_end_date, datetime.max.time()),
    )
    strava_account.last_sync_time = datetime.now()
    stats = {
        "new_trips": 0,
        "synced_trips": 0,
        "synced_activities": 0,
    }
    for activity in activities:
        sync_activity(activity, hashtag_table, strava_account, sclient, stats)
    strava_account.save()
    return stats


def sync_activity(activity, hashtag_table, strava_account, sclient, stats):
    stats["synced_activities"] += 1
    try:
        campaign, direction = hashtag_table.get_campaign_and_direction_for_activity(activity)
    except hashtags.NoValidHashtagException:
        return
    stats["synced_trips"] += 1
    user_attendance = UserAttendance.objects.get(campaign=campaign, userprofile=strava_account.user.userprofile)
    trip_date = activity.start_date.date()
    exists = Trip.objects.filter(
        trip_date=trip_date,
        direction=direction,
        user_attendance=user_attendance,
    ).exists()
    if not exists:
        stats["new_trips"] += 1
    if activity.map.summary_polyline and (not exists) and settings.STRAVA_FINE_POLYLINES:
        activity = sclient.get_activity(activity.id)
    form_data = {
        'date': trip_date,
        'direction': direction,
        'user_attendance': user_attendance.id,
        'commute_mode': get_commute_mode(activity.type).id,
        'distance': round(stravalib.unithelper.kilometers(activity.distance).get_num(), 2),
        'duration': activity.elapsed_time.total_seconds(),
        'source_application': 'strava',
        'source_id': activity.id,
        'from_application': True,
    }
    if activity.map.summary_polyline and (not exists):
        form_data['track'] = get_track(activity.map.summary_polyline)
    if activity.map.polyline:
        form_data['track'] = get_track(activity.map.polyline)
    trip_form = FullTripForm(data=form_data)

    if trip_form.is_valid():
        trip_form.save()
    else:
        logger.error("Form error:")
        logger.error(trip_form.errors)


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
