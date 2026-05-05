from repositories.sqlite_client import cursor, conn


def init_schema() -> None:
    cursor.execute("""CREATE TABLE IF NOT EXISTS profiles (
        telegram_id    INTEGER PRIMARY KEY,
        username       TEXT,
        name           TEXT,
        age            INTEGER,
        city           TEXT,
        gender         TEXT,
        looking_for    TEXT,
        description    TEXT,
        active         INTEGER DEFAULT 1,
        language       TEXT DEFAULT 'ru',
        premium_until  TEXT DEFAULT NULL,
        daily_views    INTEGER DEFAULT 0,
        last_view_date TEXT DEFAULT NULL
    )""")

    # добавляем новые колонки к уже существующим базам — ошибка игнорируется, если колонка уже есть
    for col, definition in [
        ("language", "TEXT DEFAULT 'ru'"),
        ("premium_until", "TEXT DEFAULT NULL"),
        ("daily_views", "INTEGER DEFAULT 0"),
        ("last_view_date", "TEXT DEFAULT NULL"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE profiles ADD COLUMN {col} {definition}")
        except Exception:
            pass

    cursor.execute("""CREATE TABLE IF NOT EXISTS media (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id  INTEGER,
        file_id     TEXT,
        media_type  TEXT,
        position    INTEGER,
        FOREIGN KEY (profile_id) REFERENCES profiles(telegram_id)
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS likes (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user INTEGER,
        to_user   INTEGER,
        action    TEXT
    )""")
    conn.commit()
