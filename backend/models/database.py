import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "queue.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT    NOT NULL,
            code      TEXT    NOT NULL UNIQUE,
            priority  INTEGER NOT NULL DEFAULT 1,
            avg_time  INTEGER NOT NULL DEFAULT 5,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS operators (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name         TEXT    NOT NULL,
            window_number     INTEGER NOT NULL UNIQUE,
            status            TEXT    NOT NULL DEFAULT 'available',
            current_ticket_id INTEGER,
            password_hash     TEXT    NOT NULL DEFAULT 'operator123'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT    NOT NULL UNIQUE,
            service_id    INTEGER NOT NULL REFERENCES services(id),
            operator_id   INTEGER REFERENCES operators(id),
            status        TEXT    NOT NULL DEFAULT 'waiting',
            created_at    TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            called_at     TEXT,
            completed_at  TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    cur.execute("SELECT COUNT(*) FROM services")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO services (name, code, priority, avg_time) VALUES (?,?,?,?)",
            [
                ("Консультация по вопросам", "A", 1, 5),
                ("Подача документов",        "B", 2, 7),
                ("Приём заявлений",          "C", 3, 6),
                ("Оплата услуг",             "D", 2, 3),
            ],
        )

    cur.execute("SELECT COUNT(*) FROM admins")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO admins (username, password) VALUES (?,?)", ("admin", "admin123"))

    cur.execute("SELECT COUNT(*) FROM settings")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO settings (key, value) VALUES (?,?)", [
            ("org_name",   "Электронная очередь"),
            ("ticker_msg", "Уважаемые клиенты! Спасибо за ожидание."),
            ("work_hours", "Пн–Пт: 9:00–18:00  Сб: 9:00–14:00"),
        ])

    conn.commit()
    conn.close()
