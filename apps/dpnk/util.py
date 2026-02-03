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
import logging
from operator import attrgetter
from itertools import tee
import re

import denorm

from django.conf import settings
from django.core.cache import cache
from django.contrib import contenttypes
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.sites.shortcuts import get_current_site
from django.core.paginator import Paginator
from django.db import connection, OperationalError, transaction
from django.utils import timezone, six
from django.utils.functional import cached_property, lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

import geopy.distance

from ipware.ip import get_real_ip

from . import exceptions

logger = logging.getLogger(__name__)

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
    start_day = (
        competition.date_from or competition.campaign.phase("competition").date_from
    )
    end_day = min(
        competition.date_to or competition.campaign.phase("competition").date_to or day,
        day,
    )
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
    """Get editable days for this competition/campaign"""
    day_today = today()
    potential_days = daterange(
        competition.campaign._first_possibly_active_day(day_today=day_today), day_today
    )
    return [
        d
        for d in potential_days
        if competition.campaign.day_active(d, day_today=day_today)
    ]


def _today():
    if hasattr(settings, "FAKE_DATE"):
        return settings.FAKE_DATE
    return datetime.date.today()


def today():
    return _today()


def get_client_ip(request):
    logger.info(request.META)
    ip = get_real_ip(request)
    logger.info(f"IP address {ip}")
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
        content_type = contenttypes.models.ContentType.objects.get_for_model(
            model.__class__
        )
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
        "co2": round(distance * 129, 1),
        "co": round(distance * 724.4, 1),
        "nox": round(distance * 169.7, 1),
        "n2o": round(distance * 25.0, 1),
        "voc": round(distance * 82.9, 1),
        "ch4": round(distance * 7.7, 1),
        "so2": round(distance * 4.9, 1),
        "solid": round(distance * 35.0, 1),
        "pb": round(distance * 0.011, 1),
    }


def get_base_url(request=None, slug=None):
    return "%s://%s.%s" % (
        request.scheme if request else "https",
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
            length += geopy.distance.vincenty(
                (start_lat, start_long), (end_lat, end_long)
            ).km
    return length


class CustomPaginator(Paginator):
    @cached_property
    def count(self):
        try:
            with transaction.atomic(), connection.cursor() as cursor:
                # Limit to 150 ms
                cursor.execute("SET LOCAL statement_timeout TO 150;")
                return super().count
        except OperationalError:
            pass
        with transaction.atomic(), connection.cursor() as cursor:
            # Obtain estimated values (only valid with PostgreSQL)
            cursor.execute(
                "SELECT reltuples FROM pg_class WHERE relname = %s",
                [self.object_list.query.model._meta.db_table],
            )
            estimate = int(cursor.fetchone()[0])
            return estimate


def get_all_logged_in_users():
    # Query all non-expired sessions
    # use timezone.now() instead of datetime.now() in latest versions of Django
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    uid_list = []

    # Build a list of user ids from that query
    for session in sessions:
        data = session.get_decoded()
        uid_list.append(data.get("_auth_user_id", None))

    # Query all logged in users based on id list
    return User.objects.filter(id__in=uid_list)


def attrgetter_def_val(attrs, instance, def_val=None):
    try:
        attr = attrgetter(attrs)(instance)
        if callable(attr):
            return attr()
        return attr
    except AttributeError:
        return def_val


def get_api_version_from_request(request, defautl_api_version="v1"):
    """Get REST API version from request object

    :param HttpRequest request: Django request object
    :param str defautl_api_version: Default REST API version if request
                                    object doesn't contain any API version

    :return str: REST API version e.g. v1
    """
    api_version = re.search(r"version=(v[1-9])", request.META.get("HTTP_ACCEPT", ""))
    return api_version.group(1) if api_version else defautl_api_version


class Cache:
    def __init__(self, key=None, timeout=None):
        self._data = None
        self._key = key
        self._timeout = timeout

    @property
    def data(self):
        self._data = cache.get(self._key)
        return self._data

    @data.setter
    def data(self, data):
        cache.set(self._key, data, self._timeout)
        self._data = data

    @data.deleter
    def data(self, key=None):
        if self._data or self.data:
            cache.delete(key if key else self._key)


register_challenge_serializer_base_cache_key_name = "register-challenge:serializer:"


def is_payment_with_reward(user_attendance, entry_fee):
    """Check if payment is with reward

    :param UserAttendance user_attendance: UserAttendance model instance
    :param int entry_fee: Entry fee amount

    :return bool: True if entry fee amount is with reward otherwise False
    """
    payment = user_attendance.representative_payment
    price_levels = user_attendance.campaign.pricelevel_set.filter(
        category__icontains="basic"
        if payment.pay_subject == "individual"
        else payment.pay_subject
    ).values(
        "id",
        "price",
        "category",
    )
    return (
        True
        if list(
            filter(
                lambda x: x["price"] == entry_fee and "reward" in x["category"],
                price_levels,
            )
        )
        else False
    )
