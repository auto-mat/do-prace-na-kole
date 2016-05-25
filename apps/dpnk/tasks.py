from __future__ import absolute_import

from . import util
from .models import UserAttendance, GpxFile, Competition, Team
from .rest_ecc import gpx_files_post
from celery import shared_task
import denorm


@shared_task(bind=True)
def recalculate_competitor_task(self, user_attendance_pk):
    from . import results
    user_attendance = UserAttendance.objects.get(pk=user_attendance_pk)
    util.rebuild_denorm_models([user_attendance.team])
    denorm.flush()
    results.recalculate_result_competitor_nothread(user_attendance)


@shared_task(bind=True)
def send_ecc_tracks(self):
    gpx_files = GpxFile.objects.filter(
        trip__commute_mode='bicycle',
        ecc_last_upload__isnull=True,
        user_attendance__team__subsidiary__city__slug='praha',
        user_attendance__payment_status='done',
        user_attendance__campaign__slug='dpnk2016'
    )

    count = gpx_files_post(gpx_files)
    return count


@shared_task(bind=True)
def recalculate_competitions_results(self, queryset=None):
    if not queryset:
        queryset = Competition.objects.filter(campaign__slug='dpnk2016')
    for competition in queryset:
        competition.recalculate_results()
    return len(queryset)


@shared_task(bind=True)
def touch_items(self, queryset):
    util.rebuild_denorm_models(queryset)
    return len(queryset)


@shared_task(bind=True)
def touch_user_attendances(self):
    queryset = UserAttendance.objects.filter(campaign__slug='dpnk2016')
    util.rebuild_denorm_models(queryset)
    return len(queryset)


@shared_task(bind=True)
def touch_teams(self):
    queryset = Team.objects.filter(campaign__slug='dpnk2016')
    util.rebuild_denorm_models(queryset)
    return len(queryset)
