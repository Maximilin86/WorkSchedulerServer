
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    first_name TEXT NOT NULL,  /* имя */
    last_name TEXT NOT NULL,  /* фамилия */
    fathers_name TEXT,  /* отчество (опционально) */
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS session;
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
DROP TABLE IF EXISTS desires;
CREATE TABLE desires(
    date DATE NOT NULL,
    user_id INTEGER NOT NULL,
    desire_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    CONSTRAINT desires_date_user_id_unique UNIQUE (date,user_id)
);
DROP TABLE IF EXISTS orders;
CREATE TABLE orders(
    date DATE NOT NULL,
    user_id INTEGER NOT NULL,
    the_order TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    CONSTRAINT orders_date_user_id_unique UNIQUE (date,user_id)
);
