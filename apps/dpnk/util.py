
import unidecode
import re
import datetime
from  django.http import HttpResponse

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)

def days(campaign):
    days = []
    competition_start = campaign.phase_set.get(type="competition").date_from
    competition_end = campaign.phase_set.get(type="competition").date_to
    for day in daterange(competition_start, competition_end):
        if day.weekday() not in (5,6):
            days.append(day)
    return days

def days_count():
    today = _today()
    return len([day for day in days() if day <= today])

def _today():
    #return datetime.date(year=2013, month=5, day=15)
    return datetime.date.today()

def today():
    return _today()

def redirect(url):
    return HttpResponse("redirect:"+url)

def slugify(str):
    str = unidecode.unidecode(str).lower()
    return re.sub(r'\W+','-',str)
