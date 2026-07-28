# -*- coding: utf-8 -*-
# Author: Timothy Hobbs <timothy <at> hobbs.cz>

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(
        r"^$",
        views.AboutStrava.as_view(),
        name="about_strava",
    ),
    re_path(
        r"^auth/$",
        views.StravaAuth.as_view(),
        name="strava_auth",
    ),
    re_path(
        r"^connect/$",
        views.StravaConnect.as_view(),
        name="strava_connect",
    ),
    re_path(
        r"^de-auth/$",
        views.StravaDisconnect.as_view(),
        name="strava_deauth",
    ),
]
