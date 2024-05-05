import random

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

import work_scheduler
from database import ws_user, ws_desire, ws_permissions, ws_db, ws_holiday, ws_order
from ws_utils import daterange
from fake_users import fake_users


class TestCommon:

    cur = date.today()
    start = cur.replace(day=1)
    end = start + relativedelta(months=1)

    def test_suggest_day(self):
        print()
        print(len(ws_desire.get_desires_between(self.start, self.end)))
        day = date.today()
        for desire in ws_desire.get_desires(day):
            print(desire)

    def test_common(self):
        print()
        work_scheduler.auto_alg()


        # user = ws_user.get_user(1)
        # print()
        # for des in ws_desire.get_desires_all():
        #     print(des)
        # ws_desire.set_desire(date.today(), user.id, ws_desire.Desire.REST)
        # ws_desire.set_desire(date.today() + timedelta(days=2), user.id, ws_desire.Desire.WORK)
        # ws_desire.set_desire(date.today() + timedelta(days=4), user.id, ws_desire.Desire.ALL_DAY)
        # # ws_desire.set_desire(date.today() + timedelta(days=4), user.id, None)
        # print()
