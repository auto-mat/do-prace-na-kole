
import datetime
import createsend
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
    today = datetime.date.today()
    for i, day in enumerate(days()):
        if day > datetime.date.today():
            break
    return i+1

def today():
    #return datetime.date(year=2013, month=5, day=15)
    return datetime.date.today()

class Mailing:

    def __init__(self, api_key, list_id):
        createsend.CreateSend.api_key = api_key
        self.list_id = list_id

    def add(self, name, surname, email, city):
        subscriber = createsend.Subscriber()
        r = subscriber.add(self.list_id, email,
                           " ".join([name, surname]),
                           [ { 'Key': "Mesto", 'Value': city } ]
                           , True)
        return r

def redirect(url):
    return HttpResponse("redirect:"+url)
