# -*- coding: utf-8 -*-
# Author: Timothy Hobbs <timothy <at> hobbs.cz>


from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _

from stale_notifications.model_mixins import StaleSyncMixin


class StravaAccount(StaleSyncMixin, models.Model):
    """Účet Strava"""
    class Meta:
        verbose_name = _("Účet Strava")
        verbose_name_plural = _("Účty Strava")

    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE,
    )

    access_token = models.CharField(
        max_length=256,
    )

    refresh_token = models.CharField(
        max_length=256,
    )

    strava_username = models.CharField(
        max_length=64,
    )

    first_name = models.CharField(
        max_length=64,
    )

    last_name = models.CharField(
        max_length=64,
    )

    user_sync_count = models.IntegerField(
        default=0,
    )

    errors = models.TextField(
        default="",
        blank=True,
    )
