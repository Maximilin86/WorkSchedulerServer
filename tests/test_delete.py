import random

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

import work_scheduler
from database import ws_user, ws_desire, ws_permissions, ws_db, ws_holiday, ws_order
from ws_utils import daterange
from fake_users import fake_users


class TestDelete:

    cur = date.today()
    start = cur.replace(day=1)
    end = start + relativedelta(months=1)

    def test_delete_all_users(self):
        with ws_db.get_db_connection() as connection:
            cur = connection.cursor()
            cur.execute("DELETE FROM users")
            connection.commit()

    def test_remove_desires(self):
        with ws_db.get_db_connection() as connection:
            cur = connection.cursor()
            cur.execute(
                "DELETE FROM desires"
                " WHERE date BETWEEN ? AND ?",
                (self.start, self.end)
            )
            connection.commit()
            removed = cur.rowcount
        print()
        if removed:
            print(f"removed {removed}")
        else:
            print(f"nothing removed")
