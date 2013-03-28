
import datetime
import createsend

DAY_START = 2
DAY_END = 31
DAYS_EXCLUDE = (5,6,8,12,13,19,20,26,27)

def days():
    return [datetime.date(year=2012, month=5, day=d) for d in range(DAY_START,DAY_END+1)
            if d not in DAYS_EXCLUDE]

def days_count():
    d = days()
    today = datetime.date.today()
    for i, day in enumerate(days()):
        if day > datetime.date.today():
            break
    return i+1

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
