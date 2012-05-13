
import datetime

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
    return i
