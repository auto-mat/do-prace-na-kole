
import unidecode
import re
import datetime
from  django.http import HttpResponse

DAY_START = 1
DAY_END = 31
DAYS_EXCLUDE = (1,8)

def days():
    days = []
    for d in range(DAY_START,DAY_END+1):
        day = datetime.date(year=2013, month=5, day=d) 
        if d not in DAYS_EXCLUDE and day.weekday() not in (5,6):
            days.append(day)
    return days

def days_count():
    d = days()
    today = _today()
    for i, day in enumerate(days()):
        if day > _today():
            break
    return i+1

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
