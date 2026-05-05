from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from db import (
    get_next_profile, get_profile, get_media, get_lang,
    add_like, check_match, get_who_liked_me, check_and_increment_views,
    delete_like, check_premium,
)
from keyboards import viewing_kb, liked_me_kb, main_menu_kb, liked_notification_kb, match_kb, first_kb
from strings import t, ALL_BROWSE
from states import Viewing
from services.profile_format import build_profile_caption_from_row
from utils import send_media

router = Router()


def _gender_word(gender: str, lang: str) -> str:
    key = "gender_male_word" if gender == "мужской" else "gender_female_word"
    return t(key, lang)


async def _show_profile(message: Message, profile: tuple, reply_markup=None) -> None:
    media_list = get_media(profile[0])
    await send_media(message, media_list, build_profile_caption_from_row(profile), reply_markup=reply_markup)


async def _send_match(bot: Bot, to_id: int, partner_name: str,
                      partner_username: str | None, reported_id: int, lang: str) -> None:
    link = f"@{partner_username}" if partner_username else partner_name
    try:
        await bot.send_message(
            chat_id=to_id,
            text=t("match", lang).format(link=link),
            reply_markup=match_kb(reported_id),
        )
    except Exception:
        pass


async def _handle_like(my_id: int, other_id: int, message: Message,
                       bot: Bot, msg_text: str | None = None) -> None:
    add_like(my_id, other_id, "like")

    my_profile    = get_profile(my_id)
    other_profile = get_profile(other_id)
    my_lang       = get_lang(my_id)
    other_lang    = get_lang(other_id)

    if check_match(other_id, my_id):
        other_name     = other_profile[2]
        other_username = other_profile[1]
        my_name        = my_profile[2]
        my_username    = my_profile[1]

        other_link = f"@{other_username}" if other_username else other_name
        await message.answer(
            t("match", my_lang).format(link=other_link),
            reply_markup=match_kb(other_id),
        )
        await _send_match(bot, other_id, my_name, my_username, my_id, other_lang)
    else:
        who   = _gender_word(my_profile[5], other_lang)
        liked = get_who_liked_me(other_id)
        count = len(liked)

        text = t("liked_notif_one", other_lang).format(who=who) if count == 1 \
               else t("liked_notif_many", other_lang).format(count=count)

        if msg_text:
            text += t("notif_msg", other_lang).format(msg=msg_text)

        try:
            await bot.send_message(
                chat_id=other_id,
                text=text,
                reply_markup=liked_notification_kb(),
            )
        except Exception:
            pass


async def show_next_or_liked(message: Message, state: FSMContext,
                             user_id: int | None = None) -> None:
    my_id = user_id if user_id is not None else message.from_user.id
    lang  = get_lang(my_id)

    liked_me = get_who_liked_me(my_id)
    if liked_me:
        first = liked_me[0]
        count = len(liked_me)
        who   = _gender_word(first[5], lang)
        header = t("liked_one", lang).format(who=who) if count == 1 \
                 else t("liked_many", lang).format(count=count)

        await state.set_state(Viewing.liked_me)
        await state.update_data(current_id=first[0])
        await message.answer(header)
        await _show_profile(message, first, reply_markup=liked_me_kb)
        return

    if not check_and_increment_views(my_id):
        await state.clear()
        await message.answer(t("daily_limit", lang), reply_markup=main_menu_kb(lang))
        return

    profile = get_next_profile(my_id)
    if profile:
        await state.set_state(Viewing.viewing)
        await state.update_data(current_id=profile[0])
        await _show_profile(message, profile, reply_markup=viewing_kb(check_premium(my_id)))
    else:
        await state.clear()
        await message.answer(t("no_profiles", lang), reply_markup=main_menu_kb(lang))


# Начать просмотр

@router.message(F.text.in_(ALL_BROWSE))
async def start_viewing(message: Message, state: FSMContext):
    await state.clear()
    await show_next_or_liked(message, state)


# Обычный просмотр анкет

@router.message(Viewing.viewing, F.text == "❤️")
async def on_like(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await _handle_like(message.from_user.id, data["current_id"], message, bot)
    await show_next_or_liked(message, state)


@router.message(Viewing.viewing, F.text == "💌")
async def on_envelope(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    data = await state.get_data()
    other = get_profile(data["current_id"])
    name = other[2] if other else "?"
    await message.answer(t("envelope_prompt", lang).format(name=name), reply_markup=ReplyKeyboardRemove())
    await state.set_state(Viewing.sending_message)


@router.message(Viewing.sending_message)
async def on_send_message(message: Message, state: FSMContext, bot: Bot):
    lang = get_lang(message.from_user.id)
    if not message.text:
        await message.answer(t("envelope_text_only", lang))
        return
    data = await state.get_data()
    await _handle_like(message.from_user.id, data["current_id"], message, bot, msg_text=message.text)
    await show_next_or_liked(message, state)


@router.message(Viewing.viewing, F.text == "👎")
async def on_dislike(message: Message, state: FSMContext):
    data = await state.get_data()
    other_id = data["current_id"]
    add_like(message.from_user.id, other_id, "dislike")
    await state.update_data(last_disliked_id=other_id)
    await show_next_or_liked(message, state)


@router.message(Viewing.viewing, F.text == "↩️")
async def on_undo_dislike(message: Message, state: FSMContext):
    my_id = message.from_user.id
    if not check_premium(my_id):
        return
    data = await state.get_data()
    last_id = data.get("last_disliked_id")
    if not last_id:
        return
    delete_like(my_id, last_id)
    profile = get_profile(last_id)
    if not profile:
        await state.update_data(last_disliked_id=None)
        return
    await state.update_data(current_id=last_id, last_disliked_id=None)
    await state.set_state(Viewing.viewing)
    await _show_profile(message, profile, reply_markup=viewing_kb(True))


@router.message(Viewing.viewing, F.text == "💤")
async def stop_viewing(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    await state.clear()
    await message.answer(t("stop_viewing", lang), reply_markup=main_menu_kb(lang))


# Просмотр тех, кто лайкнул меня

@router.message(Viewing.liked_me, F.text == "❤️")
async def on_like_back(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await _handle_like(message.from_user.id, data["current_id"], message, bot)
    await show_next_or_liked(message, state)


@router.message(Viewing.liked_me, F.text == "👎")
async def on_dislike_back(message: Message, state: FSMContext):
    data = await state.get_data()
    add_like(message.from_user.id, data["current_id"], "dislike")
    await show_next_or_liked(message, state)


# Callback-кнопки (уведомления)

@router.callback_query(F.data == "view_liked")
async def cb_view_liked(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await show_next_or_liked(callback.message, state, user_id=callback.from_user.id)


@router.callback_query(F.data == "skip_liked")
async def cb_skip_liked(callback: CallbackQuery, state: FSMContext):
    lang = get_lang(callback.from_user.id)
    await callback.answer(t("skip_liked", lang))
    await state.clear()
    await callback.message.answer(t("menu_prompt", lang), reply_markup=main_menu_kb(lang))


@router.callback_query(F.data.startswith("report_"))
async def cb_report(callback: CallbackQuery):
    lang = get_lang(callback.from_user.id)
    await callback.answer(t("report_sent", lang), show_alert=True)


# Игнорируем неизвестный ввод во время просмотра

@router.message(Viewing.viewing)
async def noop_viewing(message: Message, state: FSMContext):
    pass


@router.message(Viewing.liked_me)
async def noop_liked_me(message: Message, state: FSMContext):
    pass


# Нет активного состояния — показываем меню или приветствие для незарегистрированных

@router.message(StateFilter(None))
async def catch_no_state(message: Message):
    lang = get_lang(message.from_user.id)
    if get_profile(message.from_user.id):
        await message.answer(t("menu_prompt", lang), reply_markup=main_menu_kb(lang))
    else:
        await message.answer(t("welcome", lang), reply_markup=first_kb)
