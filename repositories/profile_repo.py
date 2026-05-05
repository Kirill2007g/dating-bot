import random
from datetime import date

from repositories.sqlite_client import conn, cursor

DAILY_LIMIT = 500


def add_profile(telegram_id: int, username: str, name: str, age: int, city: str,
                gender: str, looking_for: str, description: str) -> None:
    existing = cursor.execute(
        "SELECT language, premium_until FROM profiles WHERE telegram_id = ?", (telegram_id,)
    ).fetchone()
    lang = existing[0] if existing else "ru"
    premium_until = existing[1] if existing else None
    cursor.execute(
        """INSERT OR REPLACE INTO profiles
        (telegram_id, username, name, age, city, gender, looking_for, description, language, premium_until)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (telegram_id, username, name, age, city, gender, looking_for, description,
         lang, premium_until),
    )
    conn.commit()


def get_profile(telegram_id: int) -> tuple | None:
    cursor.execute("SELECT * FROM profiles WHERE telegram_id = ?", (telegram_id,))
    return cursor.fetchone()


def delete_profile(telegram_id: int) -> bool:
    cursor.execute("DELETE FROM profiles WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    return cursor.rowcount > 0


def deactivate_profile(telegram_id: int) -> None:
    cursor.execute("UPDATE profiles SET active = 0 WHERE telegram_id = ?", (telegram_id,))
    conn.commit()


def activate_profile(telegram_id: int) -> None:
    cursor.execute("UPDATE profiles SET active = 1 WHERE telegram_id = ?", (telegram_id,))
    conn.commit()


def update_description(telegram_id: int, description: str) -> None:
    cursor.execute(
        "UPDATE profiles SET description = ? WHERE telegram_id = ?",
        (description, telegram_id),
    )
    conn.commit()


def update_language(telegram_id: int, language: str) -> None:
    cursor.execute(
        "UPDATE profiles SET language = ? WHERE telegram_id = ?",
        (language, telegram_id),
    )
    conn.commit()


def update_username(telegram_id: int, username: str) -> None:
    cursor.execute(
        "UPDATE profiles SET username = ? WHERE telegram_id = ?",
        (username, telegram_id),
    )
    conn.commit()


def get_lang(telegram_id: int) -> str:
    cursor.execute("SELECT language FROM profiles WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    return row[0] if row and row[0] else "ru"


def get_all_active_users() -> list[tuple]:
    cursor.execute("SELECT telegram_id, language FROM profiles WHERE active = 1")
    return cursor.fetchall()


def get_next_profile(telegram_id: int) -> tuple | None:
    my = get_profile(telegram_id)
    if not my:
        return None

    my_age = my[3]
    my_city = my[4]
    my_looking_for = my[6]

    gender_clause = "" if my_looking_for == "все" else "AND gender = ?"
    gender_params = () if my_looking_for == "все" else (my_looking_for,)

    def query(age_min: int, age_max: int) -> tuple | None:
        sql = f"""
            SELECT * FROM profiles
            WHERE telegram_id != ?
            AND active = 1
            AND LOWER(city) = LOWER(?)
            AND age BETWEEN ? AND ?
            {gender_clause}
            AND telegram_id NOT IN (
                SELECT to_user FROM likes WHERE from_user = ?
            )
            ORDER BY CASE WHEN premium_until IS NOT NULL AND premium_until >= DATE('now') THEN 0 ELSE 1 END, RANDOM()
            LIMIT 1
        """
        cursor.execute(sql, (telegram_id, my_city, age_min, age_max) + gender_params + (telegram_id,))
        return cursor.fetchone()

    # в 90% случаев ищем точный возраст — так лента выглядит релевантнее;
    # если никого не нашли, расширяем диапазон по ±1..4 года
    if random.random() < 0.9:
        result = query(my_age, my_age)
        if result:
            return result

    for delta in range(1, 5):
        result = query(my_age - delta, my_age + delta)
        if result:
            return result

    return None


def check_and_increment_views(telegram_id: int) -> bool:
    today = date.today().isoformat()
    row = cursor.execute(
        "SELECT daily_views, last_view_date, premium_until FROM profiles WHERE telegram_id = ?",
        (telegram_id,),
    ).fetchone()
    if not row:
        return False
    daily_views, last_view_date, premium_until = row
    if premium_until and premium_until >= today:
        return True  # премиум — лимит не применяется
    if last_view_date != today:
        daily_views = 0  # новый день — сбрасываем счётчик
    if daily_views >= DAILY_LIMIT:
        return False
    cursor.execute(
        "UPDATE profiles SET daily_views = ?, last_view_date = ? WHERE telegram_id = ?",
        (daily_views + 1, today, telegram_id),
    )
    conn.commit()
    return True
