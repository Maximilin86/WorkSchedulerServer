from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


def to_epoch_days(day: date):
    return (day - date(1970, 1, 1)).days


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(days=n)


def daterange_reverse(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield end_date - timedelta(days=n + 1)
