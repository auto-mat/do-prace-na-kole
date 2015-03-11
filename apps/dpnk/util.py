
import unidecode
import re
import datetime
from  django.http import HttpResponse
import settings

DAYS_EXCLUDE = (
    datetime.date(year=2014, day=8, month=5),
    datetime.date(year=2015, day=8, month=5),
)

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)

def working_day(day):
    return day not in DAYS_EXCLUDE and day.weekday() not in (5,6)

def days(campaign):
    days = []
    competition_start = campaign.phase("competition").date_from
    competition_end = campaign.phase("competition").date_to
    for day in daterange(competition_start, competition_end):
        days.append(day)
    return days

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
    return HttpResponse("redirect:"+url)

def slugify(str):
    str = unidecode.unidecode(str).lower()
    return re.sub(r'\W+','-',str)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
