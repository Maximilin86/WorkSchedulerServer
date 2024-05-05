import os
import sqlite3
import pathlib
from database import ws_user
DB_DIR = pathlib.Path(__file__).parent

db_file = DB_DIR / 'work_scheduler.db'


def get_db_connection():
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn


def initial():
    try:
        with get_db_connection() as connection:
            with open(pathlib.Path(__file__).parent / 'schema.sql') as f:
                connection.executescript(f.read())
            connection.commit()
        # ws_user.create_initial_users()
    except:
        os.unlink(db_file)
        raise


if not db_file.exists():
    initial()

