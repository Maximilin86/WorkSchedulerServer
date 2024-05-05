import datetime
from dateutil.relativedelta import relativedelta

from database import ws_db
from ws_utils import daterange, to_epoch_days


class HolidayRow(dict):

    __slots__ = ['date', 'is_work_day']

    date: datetime.date
    is_work_day: bool

    def __init__(self, row: dict):
        super().__init__(row)
        for k, v in row.items():
            if k == 'date':
                v = datetime.datetime.strptime(v, "%Y-%m-%d").date()
            elif k == 'is_work_day':
                v = True if v != 0 else False
            setattr(self, k, v)


def set_holiday(date: datetime.date, is_work_day: bool = False):
    is_weekend = date.weekday() in [5, 6]  # сб, вс
    is_remove_row = (not is_work_day) == is_weekend
    with ws_db.get_db_connection() as connection:
        cur = connection.cursor()
        if is_remove_row:
            cur.execute(
                "DELETE FROM holidays WHERE"
                f' `date` = ? AND',
                (date,)
            )
        else:
            is_work_day = 1 if is_work_day else 0
            cur.execute(
                "INSERT INTO holidays"
                " (date, is_work_day)"
                " VALUES (?, ?)"
                " ON CONFLICT(date)"  # for sqlite
                " DO UPDATE SET `is_work_day`=?",
                # " ON DUPLICATE KEY UPDATE"  # for mysql
                # " `is_work_day` = ?",
                (date, is_work_day,
                 is_work_day)
            )
        connection.commit()


def _get_holidays_between(fr: datetime.date, to: datetime.date) -> list[HolidayRow]:
    with ws_db.get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM holidays"
            " WHERE date BETWEEN ? AND ?",
            (fr, to)
        ).fetchall()
    return [HolidayRow(dict(ix)) for ix in rows]


def _get_holiday(date: datetime.date) -> HolidayRow or None:
    with ws_db.get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM holidays WHERE"
            " `date` = ?"
            " LIMIT 1",
            (date,)
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return HolidayRow(dict(row))


def is_rest_day(date: datetime.date) -> bool:
    row = _get_holiday(date)
    if row is not None:
        return not row.is_work_day
    is_weekend = date.weekday() in [5, 6]  # сб, вс
    return is_weekend


def get_rest_days_between(fr: datetime.date, to: datetime.date) -> list[int]:
    holidays = _get_holidays_between(fr, to)
    work_days = set()
    rest_days = set()
    for row in holidays:
        if row.is_work_day:
            work_days.add(to_epoch_days(row.date))
        else:
            rest_days.add(to_epoch_days(row.date))
    out = []
    for day in daterange(fr, to):
        is_weekend = day.weekday() in [5, 6]  # сб, вс
        epoch_day = to_epoch_days(day)
        if is_weekend:
            if epoch_day not in work_days:
                out.append(epoch_day)
        else:
            if epoch_day in rest_days:
                out.append(epoch_day)
    return out


def calc_hours_for_month(month: datetime.date):
    start = month.replace(day=1)
    end = start + relativedelta(months=1)
    # week_day = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
    rest_days = get_rest_days_between(start, end)
    hours = 0
    for day in daterange(start, end):
        is_rest = to_epoch_days(day) in rest_days
        # print(day, 'rest' if is_rest else '')
        if is_rest:
            continue
        # if day.weekday() in [5, 6]:  # сб, вс
        #     continue
        hours += 8
    return hours
