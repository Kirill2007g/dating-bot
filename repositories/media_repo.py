from repositories.sqlite_client import conn, cursor


def add_media(profile_id: int, file_id: str, media_type: str) -> bool:
    cursor.execute("SELECT COUNT(*) FROM media WHERE profile_id = ?", (profile_id,))
    count = cursor.fetchone()[0]
    if count >= 3:
        return False
    cursor.execute(
        "INSERT INTO media (profile_id, file_id, media_type, position) VALUES (?, ?, ?, ?)",
        (profile_id, file_id, media_type, count + 1),
    )
    conn.commit()
    return True


def clear_media(profile_id: int) -> None:
    cursor.execute("DELETE FROM media WHERE profile_id = ?", (profile_id,))
    conn.commit()


def get_media(profile_id: int) -> list:
    cursor.execute(
        "SELECT file_id, media_type FROM media WHERE profile_id = ? ORDER BY position",
        (profile_id,),
    )
    return cursor.fetchall()


def update_media(profile_id: int, media_list: list) -> None:
    clear_media(profile_id)
    for i, (file_id, media_type) in enumerate(media_list):
        cursor.execute(
            "INSERT INTO media (profile_id, file_id, media_type, position) VALUES (?, ?, ?, ?)",
            (profile_id, file_id, media_type, i + 1),
        )
    conn.commit()
