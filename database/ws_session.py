from database import ws_db
import string
import secrets


class Session(dict):

    __slots__ = ['id', 'token', 'user_id', 'created_at']
    def __init__(self, row: dict):
        super().__init__(row)
        for k, v in row.items():
            setattr(self, k, v)


def add_session(user_id, token):
    with ws_db.get_db_connection() as connection:
        cur = connection.cursor()
        cur.execute(
            "INSERT INTO sessions"
            " (user_id, token)"
            " VALUES (?, ?)",
            (user_id, token)
        )
        connection.commit()


def find_session_by_token(token: str) -> Session or None:
    with ws_db.get_db_connection() as conn:
        sql = f'SELECT * FROM sessions WHERE `token` = \'{token}\''
        row = conn.execute(sql).fetchone()
    if row is None:
        return None
    return Session(dict(row))


def _generate_new_token():
    alphabet = string.ascii_letters + string.digits
    letters = []
    for i in range(64):
        letter = secrets.choice(alphabet)
        letters.append(letter)
    return ''.join(letters)


def generate_unique_token():
    while True:
        token = _generate_new_token()
        session = find_session_by_token(token)
        if session is None:
            return token


def start_user_session(user_id):
    token = generate_unique_token()
    add_session(user_id, token)
    return token


def get_sessions() -> list[Session]:
    with ws_db.get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM sessions').fetchall()
    return [Session(dict(ix)) for ix in rows]

