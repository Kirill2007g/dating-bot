from repositories.sqlite_client import conn, cursor


def add_like(from_user: int, to_user: int, action: str) -> None:
    cursor.execute(
        "INSERT INTO likes (from_user, to_user, action) VALUES (?, ?, ?)",
        (from_user, to_user, action),
    )
    conn.commit()


def delete_like(from_user: int, to_user: int) -> None:
    cursor.execute(
        "DELETE FROM likes WHERE from_user = ? AND to_user = ? AND action = 'dislike'",
        (from_user, to_user),
    )
    conn.commit()


def check_match(user1: int, user2: int) -> bool:
    cursor.execute(
        "SELECT 1 FROM likes WHERE from_user = ? AND to_user = ? AND action = 'like'",
        (user1, user2),
    )
    return cursor.fetchone() is not None


def get_who_liked_me(telegram_id: int) -> list:
    cursor.execute("""
        SELECT * FROM profiles
        WHERE telegram_id IN (
            SELECT from_user FROM likes
            WHERE to_user = ? AND action = 'like'
        )
        AND telegram_id NOT IN (
            SELECT to_user FROM likes
            WHERE from_user = ?
        )
        AND active = 1
    """, (telegram_id, telegram_id))
    return cursor.fetchall()
