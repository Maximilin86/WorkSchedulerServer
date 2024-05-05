import datetime
import json
import enum

from database import ws_db
from database import ws_permissions


class Order(enum.IntEnum):
    REST = 0
    WORK = 1
    ALL_DAY = 2


class OrderRow(dict):

    __slots__ = ['date', 'user_id', 'order', 'comment', 'created_at']

    date: datetime.date
    user_id: int
    order: Order
    comment: str

    def __init__(self, row: dict):
        super().__init__(row)
        for k, v in row.items():
            if k == 'date':
                v = datetime.datetime.strptime(v, "%Y-%m-%d").date()
            elif k == 'order_id':
                k = 'order'
                v = Order(v)
            setattr(self, k, v)


def set_order(date: datetime.date, user_id, order: Order or None, comment=""):
    with ws_db.get_db_connection() as connection:
        if order is Order.ALL_DAY:
            # check no one has all day here
            ad_user_id = get_all_day_order_user_id(date)
            if ad_user_id is not None:
                raise Exception(f'{date}: cant set all_day for user {user_id} because user {ad_user_id} already all_day')
        cur = connection.cursor()
        if order is None:
            cur.execute(
                "DELETE FROM orders WHERE"
                f' `date` = ? AND'
                f' `user_id` = ?',
                (date, user_id)
            )
        else:
            cur.execute(
                "INSERT INTO orders"
                " (date, user_id, order_id, comment)"
                " VALUES (?, ?, ?, ?)"
                " ON CONFLICT(date, user_id)"  # for sqlite
                " DO UPDATE SET `order_id`=?, `comment`=?",
                # " ON DUPLICATE KEY UPDATE"  # for mysql
                # " `order_id` = ?, `comment` = ?",
                (date, user_id, order, comment,
                 order, comment)
            )
        connection.commit()


def get_orders_all() -> list[OrderRow]:
    with ws_db.get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM orders').fetchall()
    return [OrderRow(dict(ix)) for ix in rows]


def get_orders(day: datetime.date) -> list[OrderRow]:
    with ws_db.get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM orders WHERE"
            " `date` = ?",
            (day,)
        ).fetchall()
    return [OrderRow(dict(ix)) for ix in rows]


def get_orders_between(fr: datetime.date, to: datetime.date) -> list[OrderRow]:
    with ws_db.get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM orders"
            " WHERE date BETWEEN ? AND ?",
            (fr, to)
        ).fetchall()
    return [OrderRow(dict(ix)) for ix in rows]


def get_order(date: datetime.date, user_id: int) -> OrderRow or None:
    with ws_db.get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM orders WHERE"
            " `date` = ? AND"
            " `user_id` = ?"
            " LIMIT 1",
            (date, user_id)
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return OrderRow(dict(row))


def get_all_day_order_user_id(date: datetime.date) -> int or None:
    with ws_db.get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT user_id FROM orders WHERE"
            " `date` = ? AND"
            " `order_id` = ?"
            " LIMIT 1",
            (date, Order.ALL_DAY)
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return row['user_id']
