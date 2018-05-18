
from datetime import datetime, timedelta

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _


class StaleSyncMixin(models.Model):
    last_sync_string = _("Poslední synchronizace")

    last_sync_time = models.DateTimeField(
        last_sync_string,
        null=True,
        default=None,
    )

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field('last_sync_time').verbose_name = self.last_sync_string

    @classmethod
    def get_stale_objects(cls, min_time_between_syncs=60 * 60 * 12):
        stale_cutoff = datetime.now() - timedelta(seconds=min_time_between_syncs)
        return cls.objects.filter(Q(last_sync_time__lte=stale_cutoff) | Q(last_sync_time__isnull=True))

    @classmethod
    def update_sync_time(cls, queryset):
        return queryset.update(last_sync_time=datetime.now())
