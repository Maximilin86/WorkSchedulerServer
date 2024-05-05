import enum
import random
import typing
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from database import ws_holiday, ws_user, ws_order, ws_desire
from ws_utils import daterange, daterange_reverse


class UserMonthWork:

    def __init__(self, row: ws_user.UserRow):
        self.row = row
        self.required_hours = 0
        self.done_hours = 0
        self.plan_hours = 0
        self.rest_score = 0
        self.desire_map: dict[int, ws_desire.DesireRow] = {}
        self.force_rest: dict[int, str] = {}
        self.work8h: set[int] = set()
        self.all_day: set[int] = set()

    def get_desire(self, day: date) -> ws_desire.Desire or None:
        row = self.desire_map.get(day.day)
        if row is None:
            return None
        return row.desire

    def __repr__(self):
        return f'UserWork({self.row.id}:{self.row.first_name})'

    @property
    def left_hours(self):
        return self.required_hours - self.done_hours - self.plan_hours


def get_hours_for_day(order: ws_order.Order, is_rest: bool):
    if order is ws_order.Order.WORK:
        return 8
    if order is ws_order.Order.ALL_DAY:
        return 20 if is_rest else 12
    return 0


def get_work_hours(day: date) -> dict[int, int]:
    is_rest = ws_holiday.is_rest_day(day)
    out = {}
    for row in ws_order.get_orders(day):
        out.setdefault(row.user_id, 0)
        out[row.user_id] += get_hours_for_day(row.order, is_rest)
    return out


class OrdersSnapshot:

    def __init__(self, cur: date):
        self.start = cur.replace(day=1)
        self.end = self.start + relativedelta(months=1)
        self.by_date: dict[int, list[ws_order.OrderRow]] = {}
        for order in ws_order.get_orders_between(self.start, self.end):
            self.by_date.setdefault(order.date.day, []).append(order)

        def order_sort_key(row: ws_order.OrderRow):
            return (int(row.order), row.user_id)
        for orders in self.by_date.values():
            orders.sort(key=order_sort_key)


def _collect_max_left_hours_users(users: typing.Iterable[UserMonthWork]) -> list[UserMonthWork]:
    max_left_hours = 0
    out = []
    for user in users:
        if user.left_hours < max_left_hours:
            continue
        if user.left_hours > max_left_hours:
            max_left_hours = user.left_hours
            out = []
        out.append(user)
    return out


def _collect_min_all_day_users(users: typing.Iterable[UserMonthWork]) -> list[UserMonthWork]:
    min_all_day_count = 31 + 1
    out = []
    for user in users:
        all_day_count = len(user.all_day)
        if all_day_count > min_all_day_count:
            continue
        if all_day_count < min_all_day_count:
            min_all_day_count = all_day_count
            out = []
        out.append(user)
    return out


def _collect_max_rest_score_users(users: typing.Iterable[UserMonthWork], day: date) -> list[UserMonthWork]:
    max_rest_score = 0
    out = []
    for user in users:
        if user.rest_score < max_rest_score:
            continue
        if user.rest_score > max_rest_score:
            max_rest_score = user.rest_score
            out = []
        if user.get_desire(day) is ws_desire.Desire.REST:
            continue
        out.append(user)
    return out


def _collect_users_with_left_hours(users: typing.Iterable[UserMonthWork]) -> list[UserMonthWork]:
    out = []
    for user in users:
        if user.left_hours <= 0:  # уже отработал все часы на этот месяц
            continue
        out.append(user)
    return out


def _collect_all_day_candidates(users: typing.Iterable[UserMonthWork], day: date) -> list[UserMonthWork]:
    out = []
    for user in users:
        if day.day in user.force_rest:  # должен отдыхать в этот день
            continue
        if day.day in user.all_day:  # уже записан на этот день
            continue
        if day.day in user.work8h:  # уже записан на этот день
            continue
        # if user.left_hours <= 0:  # уже отработал все часы на этот месяц
        #     continue
        # закоментировано: так как следующие операции сортируют по отработаным часам,
        #   переработки допустимы ради закрытия дежурств
        out.append(user)
    return out


def _collect_work8h_candidates(users: typing.Iterable[UserMonthWork], day: date) -> list[UserMonthWork]:
    out = []
    for user in users:
        if day.day in user.force_rest:  # должен отдыхать в этот день
            continue
        if day.day in user.work8h:  # уже записан на этот день
            continue
        if day.day in user.all_day:  # уже записан на этот день
            continue
        if user.left_hours <= 0:  # уже отработал все часы на этот месяц
            continue
        out.append(user)
    return out


def _collect_who_desire_all_day(users: typing.Iterable[UserMonthWork], day: date) -> list[UserMonthWork]:
    out = []
    for user in users:
        if day.day in user.force_rest:  # не берем пользователей, которым нужно отдыхать
            continue
        if user.get_desire(day) is ws_desire.Desire.ALL_DAY:
            out.append(user)
            break
    return out


def _collect_who_desire_work8h(users: typing.Iterable[UserMonthWork], day: date) -> list[UserMonthWork]:
    out = []
    for user in users:
        if day.day in user.force_rest:  # не берем пользователей, которым нужно отдыхать
            continue
        if user.get_desire(day) is ws_desire.Desire.WORK:
            out.append(user)
            break
    return out


class DistributionAlg:

    def __init__(self, cur: date):
        """
        Это инструмент для дозаполнения недозаполненных дней и недоработанных рабочих часов.
        Если у пользователя план перевыполнен, убирайте у него дни вручную
        (возможно можно как то реализовать перевыполнение через
         автоматическое убирание рабочих дней с конца месяца
         или через бонусы на след месяц если убирать нечего)
        """
        self.cur = cur
        self.start = self.cur.replace(day=1)
        self.end = self.start + relativedelta(months=1)
        self.user_map = {row.id: UserMonthWork(row) for row in ws_user.get_users()}
        self.old_orders_snapshot = OrdersSnapshot(cur)
        self.rest_days = ws_holiday.get_rest_days_between(self.start, self.end)
        self.days = list(daterange(self.cur, self.end))
        random.shuffle(self.days)  # перемешиваем порядок дней для увеличения равномерности распределения

        # результат выполнения: изменения для БД
        # нельзя применять изменения к БД в процессе рассчетов,
        #  т.к. в середине рассчетев может вылететь иключение
        self.make_all_day: dict[int, tuple[UserMonthWork, list[str]]] = {}
        self.error_all_day: dict[int, str] = {}
        self.make_work8h: dict[int, list[tuple[UserMonthWork, list[str]]]] = {}

    def prepare(self):
        # * * *  Подготовка * * *
        # вычисляем сколько каждый должен отработать за текущий месяц
        required_hours = ws_holiday.calc_hours_for_month(self.start)
        for user in self.user_map.values():  # type: UserMonthWork
            user.required_hours = required_hours
            # учитываем штрафы/бонусы из предыдущего месяца
            # todo: штрафные/бонусные часы
        # собираем отработанные часы с начала месяца до текущего дня
        for day in daterange(self.start, self.cur):
            is_rest = day.day in self.rest_days
            for row in ws_order.get_orders(day):
                user = self.user_map[row.user_id]
                user.done_hours += get_hours_for_day(row.order, is_rest)
                if row.order is ws_order.Order.ALL_DAY:
                    user.all_day.add(day.day)
        # достаем модификаторы выбора пользователя
        #   учитываем пожелания
        for row in ws_desire.get_desires_between(self.cur, self.end):
            user = self.user_map[row.user_id]
            assert row.date.day not in user.desire_map
            user.desire_map[row.date.day] = row
        #     пожелание отдыха в один день почти гарантирует выбор в другой день
            if row.desire is ws_desire.Desire.REST:
                user.rest_score += 1
        #   учитываем особые условия для отдыха
        #     если юзер работал all_day в день до начала распределения
        ad_user_id = ws_order.get_all_day_order_user_id(self.cur - timedelta(days=1))
        if ad_user_id is not None:
            self.user_map[ad_user_id].force_rest[1] = 'last_month_all_day'

    def run(self):
        # * * *  Алгоритм * * *
        # сохраняем старое значение для всех кто устанавливался ранее на all_day
        ignore_days = []
        for day in daterange(self.cur, self.end):
            ad_user_id = self._get_old_user_all_day(day)
            if ad_user_id is not None:
                self._on_user_set_all_day(day, self.user_map[ad_user_id])
                ignore_days.append(day.day)
        # сохраняем старое значение для всех кто устанавливался ранее на work8h
        for day in daterange(self.cur, self.end):
            user_ids = self._get_old_users_work8h(day)
            for user_id in user_ids:
                self._on_user_set_work8h(day, self.user_map[user_id])
        # распределяем all_day
        self._run_all_day(ignore_days)
        # распределяем work8h
        self._run_work8h()

    def _run_all_day(self, ignore_days: list):
        missing_days: list[date] = []
        for day in self.days:
            if day.day in ignore_days:
                continue
            # выбираем тех, кого можно добавить на этот день
            candidates: list[UserMonthWork] = _collect_all_day_candidates(self.user_map.values(), day)
            # стараемся учесть пожелания
            who_desire = _collect_who_desire_all_day(candidates, day)
            if who_desire:  # если есть желающие на этот день
                reason = [f'by_desire:{len(who_desire)}/{len(candidates)}']
                candidates = who_desire
                max_rest_score = _collect_max_rest_score_users(candidates, day)
                if max_rest_score:
                    if len(max_rest_score) != len(candidates):
                        reason.append(f'by_rest_score:{len(max_rest_score)}/{len(candidates)}')
                    candidates = max_rest_score
                # выбраем тех, у кого меньше всего дежурства за этот месяц
                candidates = _collect_min_all_day_users(candidates)
                # затем выбраем тех, у кого осталось больше всего неотработанных часов
                candidates = _collect_max_left_hours_users(candidates)
                # только затем рандом
                user: UserMonthWork = random.choice(candidates)
                self.make_all_day[day.day] = (user, reason)
                self._on_user_set_all_day(day, user)
                continue
            # запоминаем дни без дежурства, чтобы заполнить позже
            missing_days.append(day)

        # заполняем оставшиеся пустые позиции
        for day in missing_days:
            candidates = _collect_all_day_candidates(self.user_map.values(), day)
            if not candidates:
                self.error_all_day[day.day] = 'no user to select'
                continue
            reason = []  # модификаторы, повлиявшие на выбор
            # выбраем тех, у кого меньше всего дежурства за этот месяц
            candidates = _collect_min_all_day_users(candidates)
            # затем выбраем тех, у кого больше всего показатель отдыха
            max_rest_score = _collect_max_rest_score_users(candidates, day)
            if max_rest_score:
                if len(max_rest_score) != len(candidates):
                    reason.append(f'by_rest_score:{len(max_rest_score)}/{len(candidates)}')
                candidates = max_rest_score
            # затем выбраем тех, у кого осталось больше всего неотработанных часов
            candidates = _collect_max_left_hours_users(candidates)
            # только затем рандом
            user: UserMonthWork = random.choice(candidates)
            self.make_all_day[day.day] = (user, reason)
            self._on_user_set_all_day(day, user)

    def _run_work8h(self):
        # выполняем балансировку нагрузки по дням
        ignore_days = set()
        while True:
            # пока есть юзеры с непогашенными рабочими часами
            left_users = _collect_users_with_left_hours(self.user_map.values())
            if not left_users:
                break
            # ищем менее нагруженный день по количеству сотрудников
            day = self._find_less_overload_day(ignore_days)
            if day is None:
                # случай, когда есть пользователи с неотработанными часами,
                # но не осталось дней куда можно было бы их вписать
                self.notify = f'has users but has no days {left_users}'
                break
            # выбираем тех, кого можно добавить на этот день
            candidates = _collect_work8h_candidates(left_users, day)  # те кто могут работать в этот день
            if not candidates:
                # в этот день никто не может. игнорируем его
                ignore_days.add(day.day)
                # print(f'ignore {day}')
                continue
            # стараемся учесть пожелания
            who_desire = _collect_who_desire_work8h(candidates, day)
            reason = []  # модификаторы, повлиявшие на выбор
            if who_desire:  # если есть желающие, то выбираем среди них
                if len(who_desire) != len(candidates):
                    reason.append(f'by_desire:{len(who_desire)}/{len(candidates)}')
                candidates = who_desire
            # затем выбраем тех, у кого больше всего показатель отдыха
            max_rest_score = _collect_max_rest_score_users(candidates, day)
            if max_rest_score:
                if len(max_rest_score) != len(candidates):
                    reason.append(f'by_rest_score:{len(max_rest_score)}/{len(candidates)}')
                candidates = max_rest_score
            # затем выбраем тех, у кого осталось больше всего неотработанных часов
            candidates = _collect_min_all_day_users(candidates)
            # только затем рандом
            user: UserMonthWork = random.choice(candidates)
            self.make_work8h.setdefault(day.day, []).append((user, reason))
            self._on_user_set_work8h(day, user)

    def _get_old_user_all_day(self, day):
        for order_row in self.old_orders_snapshot.by_date.get(day, []):
            if order_row.order is ws_order.Order.ALL_DAY:
                return order_row.user_id
        return None

    def _get_old_users_work8h(self, day) -> list[int]:
        out = []
        for order_row in self.old_orders_snapshot.by_date.get(day, []):
            if order_row.order is ws_order.Order.WORK:
                out.append(order_row.user_id)
        return out

    def _on_user_set_all_day(self, day: date, user: UserMonthWork):
        # запоминаем что след день это отдых
        user.force_rest[day.day + 1] = 'after all_day'
        # обновляем рабочие часы
        user.plan_hours += get_hours_for_day(ws_order.Order.ALL_DAY, day.day in self.rest_days)
        user.all_day.add(day.day)

    def _on_user_set_work8h(self, day: date, user: UserMonthWork):
        # обновляем рабочие часы
        user.plan_hours += get_hours_for_day(ws_order.Order.WORK, day.day in self.rest_days)
        user.work8h.add(day.day)

    def _find_less_overload_day(self, ignore_days: set[int]):
        out = None
        min_work8h_count = 10_000_000
        for day in self.days:
            if day.day in ignore_days:
                continue
            work8h_count = 0
            for user in self.user_map.values():
                if day.day in user.work8h:
                    work8h_count += 1
            if work8h_count < min_work8h_count:
                min_work8h_count = work8h_count
                out = day
        return out


def auto_alg():
    alg = DistributionAlg(date.today())
    print(alg.start, alg.cur, alg.end)
    alg.prepare()
    alg.run()

    for day in daterange(alg.cur, alg.end):
        print(day)
        print(f'  all day {alg.make_all_day.get(day.day)}')
        for user in sorted(alg.make_work8h.get(day.day, []), key=lambda e: e[0].row.id):
            print(f'  work8h {user}')
        err = alg.error_all_day.get(day.day)
        if err:
            print(f'  err {err}')




