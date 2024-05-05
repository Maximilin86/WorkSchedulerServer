import random

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from database import ws_user, ws_desire, ws_permissions, ws_db, ws_holiday, ws_order
from ws_utils import daterange
from fake_users import fake_users


class TestFill:

    cur = date.today()
    start = cur.replace(day=1)
    end = start + relativedelta(months=1)

    def test_fill_users(self):
        ws_user.add_user("test1", '01234', role=ws_permissions.Role.USER, first_name="Володька", last_name="Яблонски")
        ws_user.add_user("test2", '43210', role=ws_permissions.Role.USER, first_name="Хулио", last_name="Трындец", fathers_name="Вячеславович")
        ws_user.add_user("admin", 'admin', role=ws_permissions.Role.ADMIN, first_name="Максим", last_name="Ильин", fathers_name="Владимирович")

        for login, password, name1, name2, name3 in fake_users[:4]:
            ws_user.add_user(
                login, password, role=ws_permissions.Role.USER,
                first_name=name1, last_name=name2, fathers_name=name3
            )

        print()
        for user in ws_user.get_users():
            print(user)

    def test_fill_desires(self):
        days_in_month = (self.end - self.start).days
        for user in ws_user.get_users():
            for i in range(7):
                day = self.start + timedelta(days=random.randint(0, days_in_month - 1))
                desire = random.choice([ch for ch in ws_desire.Desire])
                ws_desire.set_desire(day, user.id, desire)

    def test_fill_holidays(self):
        ws_holiday.set_holiday(date(2024, 5, 1))
        ws_holiday.set_holiday(date(2024, 5, 4), is_work_day=True)
        ws_holiday.set_holiday(date(2024, 5, 9))
        ws_holiday.set_holiday(date(2024, 5, 10))

    def test_fill_month_orders(self):
        users = [user for user in ws_user.get_users()]
        for day in daterange(self.start, self.cur):
            all_day_user = random.choice(users)  # type: ws_user.UserRow
            ad_user_id = ws_order.get_all_day_order_user_id(day)
            if ad_user_id is None:
                ws_order.set_order(day, all_day_user.id, ws_order.Order.ALL_DAY, "random")
            for i in range(random.randint(3, 7)):
                work_user = random.choice(users)  # type: ws_user.UserRow
                if work_user.id == all_day_user.id:
                    print(f'ignore {work_user.first_name}')
                    continue
                ws_order.set_order(day, work_user.id, ws_order.Order.WORK, "random")
