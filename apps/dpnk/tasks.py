from __future__ import absolute_import

from celery import shared_task
from .models import UserAttendance
from .results import recalculate_result_competitor_nothread
import denorm
import dpnk


@shared_task(bind=True)
def recalculate_competitor_task(self, user_attendance_pk):

    user_attendance = UserAttendance.objects.get(pk=user_attendance_pk)
    dpnk.util.rebuild_denorm_models([user_attendance.team])
    denorm.flush()
    recalculate_result_competitor_nothread(user_attendance)
