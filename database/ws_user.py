import json

from database import ws_db
from database import ws_permissions


class User(dict):

    __slots__ = ['id', 'user', 'password', 'role', 'first_name', 'last_name', 'fathers_name', 'created_at']
    def __init__(self, row: dict):
        super().__init__(row)
        for k, v in row.items():
            if k == 'role':
                v = ws_permissions.parse_role(v)
            setattr(self, k, v)


def add_user(user, password, role: ws_permissions.Role, first_name: str, last_name: str, fathers_name: str=None):
    with ws_db.get_db_connection() as connection:
        cur = connection.cursor()
        cur.execute(
            "INSERT INTO users"
            " (user, password, role, first_name, last_name, fathers_name)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (user, password, role.name, first_name, last_name, fathers_name)
        )
        connection.commit()


def get_users() -> list[User]:
    with ws_db.get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM users').fetchall()
    return [User(dict(ix)) for ix in rows]


def get_user(user_id: int) -> User or None:
    with ws_db.get_db_connection() as conn:
        sql = (
            f'SELECT * FROM users WHERE'
            f' `id` = \'{user_id}\''
            f' LIMIT 1'
        )
        row = conn.execute(sql).fetchone()
    if row is None:
        return None
    return User(dict(row))


def find_user_by_auth(username: str, password: str) -> User or None:
    with ws_db.get_db_connection() as conn:
        sql = (f'SELECT * FROM users WHERE'
               f' `user` = \'{username}\' AND'
               f' `password` = \'{password}\'')
        row = conn.execute(sql).fetchone()
    if row is None:
        return None
    return User(dict(row))


def create_initial_users():
    add_user("Test1", '01234', role=ws_permissions.Role.USER, first_name="Володька", last_name="Яблонски")
    add_user("Test2", '43210', role=ws_permissions.Role.USER, first_name="Хулио", last_name="Трындец", fathers_name="Вячеславович")
    add_user("admin", 'admin', role=ws_permissions.Role.ADMIN, first_name="Максим", last_name="Ильин", fathers_name="Владимирович")

