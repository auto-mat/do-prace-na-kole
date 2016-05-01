from __future__ import absolute_import

from celery import Celery
app = Celery('apps.dpnk')


@app.task(bind=True)
def recalculate_competitor_task(self, user_attendance_pk):
    import dpnk
    import denorm
    from dpnk.models import UserAttendance
    from dpnk.results import recalculate_result_competitor_nothread

    user_attendance = UserAttendance.objects.get(pk=user_attendance_pk)
    dpnk.util.rebuild_denorm_models([user_attendance.team])
    denorm.flush()
    recalculate_result_competitor_nothread(user_attendance)
