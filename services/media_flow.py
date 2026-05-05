from aiogram.types import Message

from services.media_input import extract_media_from_message


# Возможные статусы: "limit_reached", "invalid_media", "added"
def collect_media_step(message: Message, temp_media: list[tuple[str, str]], max_items: int = 3) -> dict:
    if len(temp_media) >= max_items:
        return {"status": "limit_reached", "temp_media": temp_media, "remaining": 0}

    media = extract_media_from_message(message)
    if media is None:
        return {"status": "invalid_media", "temp_media": temp_media, "remaining": max_items - len(temp_media)}

    new_media = [*temp_media, media]
    remaining = max_items - len(new_media)
    return {"status": "added", "temp_media": new_media, "remaining": remaining}
