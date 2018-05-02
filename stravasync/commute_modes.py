# -*- coding: utf-8 -*-
# Author: Timothy Hobbs <timothy <at> hobbs.cz>

from dpnk.models.commute_mode import CommuteMode

strava_commute_modes = {
    "ride": 'bicycle',
    "run": 'by_foot',
    "walk": 'by_foot',
    "hike": 'by_foot',
    "e-bike ride": 'bicycle',
    "handcycle": 'bicycle',
    "inline skate": 'bicycle',
    "nordic ski": 'by_foot',
    "inlineskate": 'by_foot',
}


def get_commute_mode(strava_mode):
    slug = strava_commute_modes[strava_mode.lower()]
    return CommuteMode.objects.get(slug=slug)
