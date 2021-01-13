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
    "ebikeride": 'bicycle',
    "rollerski": 'by_foot',
    "canoeing": 'by_other_vehicle',
}

def get_commute_mode_slug(strava_mode):
    return strava_commute_modes[strava_mode.lower()]

def get_commute_mode(strava_mode):
    return CommuteMode.objects.get(get_commute_mode_slug(strava_mode))
