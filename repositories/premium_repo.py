from datetime import date, timedelta

from repositories.sqlite_client import conn, cursor


def activate_premium(telegram_id: int, days: int) -> None:
    cursor.execute("SELECT premium_until FROM profiles WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    today = date.today()
    # если премиум ещё активен — продлеваем от текущей даты окончания, а не от сегодня
    if row and row[0] and row[0] >= today.isoformat():
        base = date.fromisoformat(row[0])
    else:
        base = today
    new_until = (base + timedelta(days=days)).isoformat()
    cursor.execute(
        "UPDATE profiles SET premium_until = ? WHERE telegram_id = ?",
        (new_until, telegram_id),
    )
    conn.commit()


def check_premium(telegram_id: int) -> bool:
    cursor.execute("SELECT premium_until FROM profiles WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    return bool(row and row[0] and row[0] >= date.today().isoformat())
