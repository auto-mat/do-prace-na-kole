# -*- coding: utf-8 -*-
# Author: Timothy Hobbs <timothy <at> hobbs.cz>

from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^$',
        views.AboutStrava.as_view(),
        name='about_strava',
    ),
    url(
        r'^auth/$',
        views.StravaAuth.as_view(),
        name='strava_auth',
    ),
    url(
        r'^de-auth/$',
        views.StravaDisconnect.as_view(),
        name='strava_deauth',
    ),
]
