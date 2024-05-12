import json

from database import ws_db
from database import ws_permissions


class UserRow(dict):

    __slots__ = ['id', 'login', 'password', 'role', 'first_name', 'last_name', 'fathers_name', 'created_at']

    id: int
    login: str
    password: str
    role: ws_permissions.Role
    first_name: str
    last_name: str
    fathers_name: str

    def __init__(self, row: dict):
        super().__init__(row)
        for k, v in row.items():
            if k == 'role':
                v = ws_permissions.parse_role(v)
            setattr(self, k, v)


def add_user(login, password, role: ws_permissions.Role, first_name: str, last_name: str, fathers_name: str=None) -> int:
    with ws_db.get_db_connection() as connection:
        cur = connection.cursor()
        cur.execute(
            "INSERT INTO users"
            " (login, password, role, first_name, last_name, fathers_name)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (login, password, role.name, first_name, last_name, fathers_name)
        )
        user_id = cur.lastrowid
        connection.commit()
    return user_id


def update_user(row: UserRow):
    with ws_db.get_db_connection() as connection:
        cur = connection.cursor()
        cur.execute(
            "UPDATE users SET login = ?, password = ?, role = ?, first_name = ?, last_name = ?, fathers_name = ? WHERE"
            " `id` = ?",
            (row.login, row.password, row.role.name, row.first_name, row.last_name, row.fathers_name,
             row.id)
        )
        connection.commit()


def get_users() -> list[UserRow]:
    with ws_db.get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM users').fetchall()
    return [UserRow(dict(ix)) for ix in rows]


def get_user(user_id: int) -> UserRow or None:
    with ws_db.get_db_connection() as conn:
        sql = (
            f'SELECT * FROM users WHERE'
            f' `id` = \'{user_id}\''
            f' LIMIT 1'
        )
        row = conn.execute(sql).fetchone()
    if row is None:
        return None
    return UserRow(dict(row))


def delete_user(user_id: int) -> bool:
    with ws_db.get_db_connection() as connection:
        cur = connection.cursor()
        cur.execute(
            "DELETE FROM users WHERE"
            " `id` = ?",
            (user_id,)
        )
        return cur.rowcount != 0


def find_user_by_auth(login: str, password: str) -> UserRow or None:
    with ws_db.get_db_connection() as conn:
        sql = (f'SELECT * FROM users WHERE'
               f' `login` = \'{login}\' AND'
               f' `password` = \'{password}\'')
        row = conn.execute(sql).fetchone()
    if row is None:
        return None
    return UserRow(dict(row))


def find_user_by_login(login: str) -> UserRow or None:
    with ws_db.get_db_connection() as conn:
        sql = (f'SELECT * FROM users WHERE'
               f' `login` = \'{login}\'')
        row = conn.execute(sql).fetchone()
    if row is None:
        return None
    return UserRow(dict(row))


def create_initial_users():
    add_user("Test1", '01234', role=ws_permissions.Role.USER, first_name="Володька", last_name="Яблонски")
    add_user("Test2", '43210', role=ws_permissions.Role.USER, first_name="Хулио", last_name="Трындец", fathers_name="Вячеславович")
    add_user("admin", 'admin', role=ws_permissions.Role.ADMIN, first_name="Максим", last_name="Ильин", fathers_name="Владимирович")

