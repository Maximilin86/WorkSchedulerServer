import json
import sqlite3
import pathlib
import work_scheduler as ws

DB_DIR = pathlib.Path(__file__).parent

db_file = DB_DIR / 'work_scheduler.db'


def get_db_connection():
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn


def add_user(user, password, role: ws.Role):
    with get_db_connection() as connection:
        cur = connection.cursor()
        cur.execute("INSERT INTO users (user, password) VALUES (?, ?)",
                    (user, password)
                    )
        connection.commit()


def initial():
    with get_db_connection() as connection:
        with open('schema.sql') as f:
            connection.executescript(f.read())
        connection.commit()
    add_user("Test1", '01234', role=ws.Role.USER)
    add_user("Test2", '43210', role=ws.Role.ADMIN)


if not db_file.exists():
    initial()


def get_users():
    with get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM users').fetchall()
    return [dict(ix) for ix in rows]


def find_user(username: str, password: str):
    with get_db_connection() as conn:
        sql = f'SELECT * FROM users WHERE `user` = \'{username}\' AND `password` = \'{password}\''
        row = conn.execute(sql).fetchone()
    if row is None:
        return None
    return dict(row)


def start_user_session(user_id):

    return 'tok'
