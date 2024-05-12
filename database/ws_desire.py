import datetime
import json
import enum

import ws_utils
from database import ws_db
from database import ws_permissions


class Desire(enum.IntEnum):
    REST = 0
    WORK = 1
    ALL_DAY = 2


class DesireRow(dict):

    __slots__ = ['date', 'user_id', 'desire', 'comment', 'created_at']

    date: datetime.date
    user_id: int
    desire: Desire
    comment: str

    def __init__(self, row: dict):
        super().__init__(row)
        for k, v in row.items():
            if k == 'date':
                v = ws_utils.parse_date(v)
            elif k == 'desire_id':
                k = 'desire'
                v = Desire(v)
            setattr(self, k, v)


def set_desire(date: datetime.date, user_id, desire: Desire or None, comment=""):
    with ws_db.get_db_connection() as connection:
        cur = connection.cursor()
        if desire is None:
            cur.execute(
                "DELETE FROM desires WHERE"
                f' `date` = ? AND'
                f' `user_id` = ?',
                (date, user_id)
            )
        else:
            cur.execute(
                "INSERT INTO desires"
                " (date, user_id, desire_id, comment)"
                " VALUES (?, ?, ?, ?)"
                " ON CONFLICT(date, user_id)"  # for sqlite
                " DO UPDATE SET `desire_id`=?, `comment`=?",
                # " ON DUPLICATE KEY UPDATE"  # for mysql
                # " `desire_id` = ?, `comment` = ?",
                (date, user_id, desire, comment,
                 desire, comment)
            )
        connection.commit()


def get_desires_all() -> list[DesireRow]:
    with ws_db.get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM desires').fetchall()
    return [DesireRow(dict(ix)) for ix in rows]


def get_desires(day: datetime.date) -> list[DesireRow]:
    with ws_db.get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM desires WHERE"
            " `date` = ?",
            (day,)
        ).fetchall()
    return [DesireRow(dict(ix)) for ix in rows]


def get_desires_between(fr: datetime.date, to: datetime.date) -> list[DesireRow]:
    with ws_db.get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM desires"
            " WHERE date BETWEEN ? AND ?",
            (fr, to - datetime.timedelta(days=1))
        ).fetchall()
    return [DesireRow(dict(ix)) for ix in rows]


def get_user_desires_between(user_id: int, fr: datetime.date, to: datetime.date) -> list[DesireRow]:
    with ws_db.get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM desires"
            " WHERE `user_id` = ? AND date BETWEEN ? AND ?",
            (user_id, fr, to - datetime.timedelta(days=1))
        ).fetchall()
    return [DesireRow(dict(ix)) for ix in rows]


def get_desire(date: datetime.date, user_id: int) -> DesireRow or None:
    with ws_db.get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM desires WHERE"
            " `date` = ? AND"
            " `user_id` = ?"
            " LIMIT 1",
            (date, user_id)
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return DesireRow(dict(row))
