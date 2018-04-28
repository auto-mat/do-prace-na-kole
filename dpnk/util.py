# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2015 o.s. Auto*Mat
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import datetime
from itertools import tee

import denorm

from django.conf import settings
from django.contrib import contenttypes
from django.contrib.sites.shortcuts import get_current_site
from django.utils import six
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

import geopy.distance

from ipware.ip import get_real_ip

from . import exceptions

mark_safe_lazy = lazy(mark_safe, six.text_type)

DAYS_EXCLUDE = (
    datetime.date(year=2016, day=5, month=7),
    datetime.date(year=2016, day=6, month=7),
    datetime.date(year=2016, day=28, month=9),
    datetime.date(year=2016, day=28, month=10),
)


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days + 1)):
        yield start_date + datetime.timedelta(n)


def working_day(day):
    if day.day in (1, 8) and day.month == 5:  # Public holiday at may
        return False
    return day not in DAYS_EXCLUDE and day.weekday() not in (5, 6)


def dates(competition, day=None):
    if not day:
        day = _today()
    start_day = competition.date_from or competition.campaign.phase("competition").date_from
    end_day = min(competition.date_to or competition.campaign.phase("competition").date_to or day, day)
    return start_day, end_day


def working_days(competition, day=None):
    start_day, end_day = dates(competition, day)
    return [d for d in daterange(start_day, end_day) if working_day(d)]


def non_working_days(competition, day=None):
    start_day, end_day = dates(competition, day)
    return [d for d in daterange(start_day, end_day) if not working_day(d)]


def days(competition, day=None):
    start_day, end_day = dates(competition, day)
    return daterange(start_day, end_day)


def days_count(competition, day=None):
    start_day, end_day = dates(competition, day)
    return end_day - start_day + datetime.timedelta(1)


def days_active(competition):
    """ Get editable days for this competition/campaign """
    return [d for d in days(competition) if competition.campaign.day_active(d)]


def _today():
    if hasattr(settings, 'FAKE_DATE'):
        return settings.FAKE_DATE
    return datetime.date.today()


def today():
    return _today()


def get_client_ip(request):
    ip = get_real_ip(request)
    if ip is not None:
        return ip
    else:
        return "0.0.0.0"


def format_psc(integer):
    if integer is None:
        return ""
    psc_str = str(integer)
    return " ".join([psc_str[:-2], psc_str[-2:]]).strip()


# TODO: move this to denorm application
def rebuild_denorm_models(models):
    for model in models:
        content_type = contenttypes.models.ContentType.objects.get_for_model(model.__class__)
        denorm.models.DirtyInstance.objects.create(
            content_type=content_type,
            object_id=model.pk,
        )
        denorm.flush()


def parse_date(date):
    try:
        return datetime.datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise exceptions.TemplatePermissionDenied(_("Datum není platné."))


def get_emissions(distance):
    return {
        'co2': round(distance * 129, 1),
        'co': round(distance * 724.4, 1),
        'nox': round(distance * 169.7, 1),
        'n2o': round(distance * 25.0, 1),
        'voc': round(distance * 82.9, 1),
        'ch4': round(distance * 7.7, 1),
        'so2': round(distance * 4.9, 1),
        'solid': round(distance * 35.0, 1),
        'pb': round(distance * 0.011, 1),
    }


def get_base_url(request, slug=None):
    return '%s://%s.%s' % (
        request.scheme,
        slug if slug is not None else request.campaign.slug,
        get_current_site(request).domain,
    )


def get_redirect(request, slug=None):
    return get_base_url(request, slug=slug) + request.path


# https://docs.python.org/3/library/itertools.html#itertools-recipes
def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def get_multilinestring_length(mls):
    """
    Returns the length of a multiline string in kilometers.
    """
    length = 0
    for linestring in mls:
        for (start_long, start_lat), (end_long, end_lat) in pairwise(linestring):
            length += geopy.distance.vincenty((start_lat, start_long), (end_lat, end_long)).km
    return length
