from aiogram.types import Message


def extract_media_from_message(message: Message) -> tuple[str, str] | None:
    if message.photo:
        return message.photo[-1].file_id, "photo"  # берём последний размер — самое высокое качество
    if message.video_note:
        return message.video_note.file_id, "video_note"
    if message.video:
        return message.video.file_id, "video"
    return None
