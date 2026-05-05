from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, LabeledPrice
from aiogram.fsm.context import FSMContext
from datetime import date

from keyboards import (
    main_menu_kb, done_media_kb, settings_kb,
    language_kb, premium_kb, back_only_kb,
)
from strings import (
    t,
    ALL_MY_PROFILE, ALL_REFILL, ALL_CHANGE_PHOTO,
    ALL_CHANGE_TEXT, ALL_SETTINGS, ALL_PREMIUM,
    ALL_CHANGE_LANG, ALL_BACK, ALL_DONE,
    ALL_PREMIUM_DURATIONS, DURATION_MAP, LANGUAGE_BUTTONS,
)
from db import (
    get_profile, get_media, get_lang,
    update_media, update_description, update_language,
)
from services.media_flow import collect_media_step
from services.profile_format import build_profile_caption_from_row
from states import ProfileMenu, Premium, StartRegistration
from utils import send_media

router = Router()


# Моя анкета

@router.message(F.text.in_(ALL_MY_PROFILE))
async def my_profile(message: Message, state: FSMContext):
    await state.clear()
    lang = get_lang(message.from_user.id)
    profile = get_profile(message.from_user.id)
    if not profile:
        await message.answer(t("no_profile", lang))
        return
    media_list = get_media(message.from_user.id)
    await send_media(message, media_list, build_profile_caption_from_row(profile))
    await message.answer(t("menu_prompt", lang), reply_markup=main_menu_kb(lang))


# Заполнить анкету заново

@router.message(F.text.in_(ALL_REFILL))
async def refill_profile(message: Message, state: FSMContext):
    await state.clear()
    lang = get_lang(message.from_user.id)
    await message.answer(t("refill_start", lang), reply_markup=ReplyKeyboardRemove())
    await state.set_state(StartRegistration.age)


# Изменить фото/видео

@router.message(F.text.in_(ALL_CHANGE_PHOTO))
async def change_photo_start(message: Message, state: FSMContext):
    await state.clear()
    lang = get_lang(message.from_user.id)
    media_list = get_media(message.from_user.id)
    if media_list:
        profile = get_profile(message.from_user.id)
        caption = build_profile_caption_from_row(profile)
        await send_media(message, media_list, caption)
    await message.answer(t("enter_new_photo", lang), reply_markup=ReplyKeyboardRemove())
    await state.update_data(temp_media=[])
    await state.set_state(ProfileMenu.new_photo)


@router.message(ProfileMenu.new_photo)
async def save_new_photo(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    data = await state.get_data()
    temp_media: list = data.get("temp_media", [])

    if message.text in ALL_DONE:
        if not temp_media:
            await message.answer(t("send_at_least_one", lang))
            return
        update_media(message.from_user.id, temp_media)
        await state.clear()
        await message.answer(t("photo_updated", lang), reply_markup=main_menu_kb(lang))
        return

    step = collect_media_step(message, temp_media, max_items=3)
    if step["status"] == "limit_reached":
        await message.answer(t("max_media", lang), reply_markup=done_media_kb)
        return
    if step["status"] == "invalid_media":
        await message.answer(t("send_media", lang))
        return
    temp_media = step["temp_media"]
    await state.update_data(temp_media=temp_media)
    remaining = step["remaining"]
    if remaining > 0:
        await message.answer(t("media_added", lang).format(n=remaining), reply_markup=done_media_kb)
    else:
        update_media(message.from_user.id, temp_media)
        await state.clear()
        await message.answer(t("photo_updated", lang), reply_markup=main_menu_kb(lang))


# Изменить описание

@router.message(F.text.in_(ALL_CHANGE_TEXT))
async def change_text_start(message: Message, state: FSMContext):
    await state.clear()
    lang = get_lang(message.from_user.id)
    await message.answer(t("enter_new_text", lang), reply_markup=back_only_kb(lang))
    await state.set_state(ProfileMenu.new_description)


@router.message(ProfileMenu.new_description)
async def save_new_description(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    if message.text in ALL_BACK:
        await state.clear()
        await message.answer(t("menu_prompt", lang), reply_markup=main_menu_kb(lang))
        return
    if not message.text or len(message.text) > 500:
        await message.answer(t("text_too_long", lang))
        return
    update_description(message.from_user.id, message.text)
    await state.clear()
    await message.answer(t("text_updated", lang), reply_markup=main_menu_kb(lang))


# Настройки

@router.message(F.text.in_(ALL_SETTINGS))
async def settings_menu(message: Message, state: FSMContext):
    await state.clear()
    lang = get_lang(message.from_user.id)
    await message.answer(t("settings_prompt", lang), reply_markup=settings_kb(lang))
    await state.set_state(ProfileMenu.settings)


@router.message(ProfileMenu.settings, F.text.in_(ALL_CHANGE_LANG))
async def choose_language(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    await message.answer(t("choose_language", lang), reply_markup=language_kb)
    await state.set_state(ProfileMenu.language)


@router.message(ProfileMenu.settings, F.text.in_(ALL_BACK))
async def settings_back(message: Message, state: FSMContext):
    await state.clear()
    lang = get_lang(message.from_user.id)
    await message.answer(t("menu_prompt", lang), reply_markup=main_menu_kb(lang))


@router.message(ProfileMenu.language)
async def save_language(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)

    # "Назад" возвращает в настройки на текущем языке — до смены
    if message.text in ALL_BACK or message.text == "Назад":
        await message.answer(t("settings_prompt", lang), reply_markup=settings_kb(lang))
        await state.set_state(ProfileMenu.settings)
        return

    if message.text not in LANGUAGE_BUTTONS:
        await message.answer(t("choose_button", lang), reply_markup=language_kb)
        return

    new_lang = LANGUAGE_BUTTONS[message.text]
    update_language(message.from_user.id, new_lang)
    await state.clear()
    # подтверждение уже на новом языке, иначе пользователь не поймёт, что изменилось
    await message.answer(
        t("language_saved", new_lang).format(lang=message.text),
        reply_markup=main_menu_kb(new_lang),
    )


# Премиум

@router.message(F.text.in_(ALL_PREMIUM))
async def premium_menu(message: Message, state: FSMContext):
    await state.clear()
    lang = get_lang(message.from_user.id)
    profile = get_profile(message.from_user.id)
    until = profile[10] if profile else None
    if until and until >= date.today().isoformat():
        text = t("premium_already", lang).format(until=until) + t("premium_terms", lang)
    else:
        text = t("premium_menu", lang) + t("premium_terms", lang)
    await message.answer(text, reply_markup=premium_kb(lang), parse_mode="Markdown")
    await state.set_state(Premium.choosing)


@router.message(Premium.choosing, F.text.in_(ALL_BACK))
async def premium_back(message: Message, state: FSMContext):
    await state.clear()
    lang = get_lang(message.from_user.id)
    await message.answer(t("menu_prompt", lang), reply_markup=main_menu_kb(lang))


@router.message(Premium.choosing, F.text.in_(ALL_PREMIUM_DURATIONS))
async def premium_buy(message: Message):
    lang = get_lang(message.from_user.id)
    days, stars = DURATION_MAP[message.text]

    await message.answer_invoice(
        title=f"Premium {days}д" if lang == "ru" else f"Premium {days}д" if lang == "uk" else f"Premium {days}d",
        description=t("premium_menu", lang).split("\n\n")[0],
        payload=f"premium_{days}",
        currency="XTR",
        prices=[LabeledPrice(label="Telegram Stars", amount=stars)],
    )
