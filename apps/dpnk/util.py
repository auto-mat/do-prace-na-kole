
import unidecode
import re
import datetime
from django.http import HttpResponse
import settings
from django.core.exceptions import ObjectDoesNotExist
import models

DAYS_EXCLUDE = (
    datetime.date(year=2014, day=8, month=5),
    datetime.date(year=2015, day=8, month=5),
)


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days + 1)):
        yield start_date + datetime.timedelta(n)


def working_day(day):
    return day not in DAYS_EXCLUDE and day.weekday() not in (5, 6)


def days(campaign):
    days = []
    competition_start = campaign.phase("competition").date_from
    competition_end = campaign.phase("competition").date_to
    for day in daterange(competition_start, competition_end):
        days.append(day)
    return days


def days_active(campaign):
    return [d for d in days(campaign) if day_active(d)]


def days_count(campaign):
    if hasattr(campaign, 'days_count'):
        return campaign.days_count
    today = _today()
    campaign.days_count = len([day for day in days(campaign) if day <= today])
    return campaign.days_count


def _today():
    if hasattr(settings, 'FAKE_DATE'):
        return settings.FAKE_DATE
    return datetime.date.today()


def today():
    return _today()


def redirect(url):
    return HttpResponse("redirect:" + url)


def slugify(str):
    str = unidecode.unidecode(str).lower()
    return re.sub(r'\W+', '-', str)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def format_psc(integer):
    psc_str = str(integer)
    return psc_str[:-2] + " " + psc_str[-2:]


def get_or_none_rm(model, *args, **kwargs):
    try:
        return model.get(*args, **kwargs)
    except ObjectDoesNotExist:
        return None


def get_or_none(model, *args, **kwargs):
    try:
        return model.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        return None


def day_active_last7(day):
    day_today = _today()
    return (
        (day <= day_today)
        and (day > day_today - datetime.timedelta(days=7))
    )


def day_active_last_week(day):
    day_today = _today()
    return (
        (day <= day_today) and
        ((day.isocalendar()[1] == day_today.isocalendar()[1]) or
            (day_today.weekday() == 0 and
                day.isocalendar()[1] + 1 == day_today.isocalendar()[1]))
    )

day_active = day_active_last7


def trip_active(trip, allow_adding_rides=None):
    if not allow_adding_rides:
        allow_adding_rides = models.CityInCampaign.objects.get(city=trip.user_attendance.team.subsidiary.city, campaign=trip.user_attendance.campaign).allow_adding_rides
    if allow_adding_rides:
        return day_active(trip.date)
    return False


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
