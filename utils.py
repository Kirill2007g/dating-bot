from aiogram.types import Message, InputMediaPhoto, InputMediaVideo

_CAPTION_MAX = 1024


async def send_media(message: Message, media_list: list, caption: str,
                     reply_markup=None) -> None:
    caption = caption[:_CAPTION_MAX]
    if not media_list:
        await message.answer(caption, reply_markup=reply_markup)
        return

    # video_note нельзя добавить в media_group, поэтому отправляем всё по одному
    has_video_note = any(mt == "video_note" for _, mt in media_list)

    if len(media_list) == 1:
        file_id, media_type = media_list[0]
        if media_type == "photo":
            await message.answer_photo(photo=file_id, caption=caption,
                                       reply_markup=reply_markup)
        elif media_type == "video":
            await message.answer_video(video=file_id, caption=caption,
                                       reply_markup=reply_markup)
        elif media_type == "video_note":
            await message.answer(caption)
            await message.answer_video_note(video_note=file_id,
                                            reply_markup=reply_markup)
    elif has_video_note:
        last_idx = len(media_list) - 1
        for i, (file_id, media_type) in enumerate(media_list):
            kb = reply_markup if i == last_idx else None
            if media_type == "photo":
                await message.answer_photo(photo=file_id,
                                           caption=caption if i == 0 else None,
                                           reply_markup=kb)
            elif media_type == "video":
                await message.answer_video(video=file_id,
                                           caption=caption if i == 0 else None,
                                           reply_markup=kb)
            elif media_type == "video_note":
                if i == 0:
                    await message.answer(caption)
                await message.answer_video_note(video_note=file_id,
                                                reply_markup=kb)
    else:
        group = []
        for i, (file_id, media_type) in enumerate(media_list):
            cap = caption if i == 0 else None
            if media_type == "photo":
                group.append(InputMediaPhoto(media=file_id, caption=cap))
            elif media_type == "video":
                group.append(InputMediaVideo(media=file_id, caption=cap))
        await message.answer_media_group(media=group)
        if reply_markup is not None:
            # reply_markup нельзя прикрепить к media_group — шлём пустое сообщение-носитель
            await message.answer("​", reply_markup=reply_markup)
