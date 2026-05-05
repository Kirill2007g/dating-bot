from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from states import StartRegistration
from keyboards import (
    first_kb, done_media_kb, end_kb,
    skip_kb, gender_kb, looking_for_kb, main_menu_kb,
)
from strings import (
    t,
    GENDER_MAP, LOOKING_MAP,
    ALL_SKIP, ALL_DONE, ALL_YES, ALL_EDIT,
)
from db import (
    add_profile, get_profile, get_lang,
    add_media, clear_media, get_media,
)
from services.geocoding import normalize_city as geocode_city
from services.media_flow import collect_media_step
from services.profile_format import build_profile_caption, build_profile_caption_from_row
from utils import send_media

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    lang = get_lang(message.from_user.id)
    profile = get_profile(message.from_user.id)
    if profile:
        media_list = get_media(message.from_user.id)
        await message.answer(t("welcome_back", lang))
        await send_media(message, media_list, build_profile_caption_from_row(profile))
        await message.answer(t("menu_prompt", lang), reply_markup=main_menu_kb(lang))
    else:
        await message.answer(t("welcome", lang), reply_markup=first_kb)


@router.message(F.text == "👍")
async def cmd_yes(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    await message.answer(t("ask_age", lang), reply_markup=ReplyKeyboardRemove())
    await state.set_state(StartRegistration.age)


@router.message(StartRegistration.age)
async def get_age(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    if not message.text or not message.text.isdigit():
        await message.answer(t("enter_age_number", lang))
        return
    age = int(message.text)
    if age < 13 or age > 99:
        await message.answer(t("age_range", lang))
        return
    await state.update_data(age=age)
    await message.answer(t("ask_gender", lang), reply_markup=gender_kb(lang))
    await state.set_state(StartRegistration.gender)


@router.message(StartRegistration.gender)
async def get_gender(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    if message.text not in GENDER_MAP:
        await message.answer(t("choose_button", lang), reply_markup=gender_kb(lang))
        return
    await state.update_data(gender=GENDER_MAP[message.text])
    await message.answer(t("ask_looking_for", lang), reply_markup=looking_for_kb(lang))
    await state.set_state(StartRegistration.looking_for)


@router.message(StartRegistration.looking_for)
async def get_looking_for(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    if message.text not in LOOKING_MAP:
        await message.answer(t("choose_button", lang), reply_markup=looking_for_kb(lang))
        return
    await state.update_data(looking_for=LOOKING_MAP[message.text])
    await message.answer(t("ask_city", lang), reply_markup=ReplyKeyboardRemove())
    await state.set_state(StartRegistration.city)


@router.message(StartRegistration.city)
async def get_city(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    if not message.text or message.text.isdigit() or len(message.text.strip()) < 2:
        await message.answer(t("enter_city", lang))
        return
    city = await geocode_city(message.text.strip())
    await state.update_data(city=city)
    await message.answer(t("ask_name", lang))
    await state.set_state(StartRegistration.name)


@router.message(StartRegistration.name)
async def get_name(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    if not message.text or message.text.isdigit() or len(message.text.strip()) < 2:
        await message.answer(t("enter_name", lang))
        return
    if len(message.text.strip()) > 50:
        await message.answer(t("name_too_long", lang))
        return
    await state.update_data(name=message.text.strip())
    await message.answer(t("ask_description", lang), reply_markup=skip_kb(lang))
    await state.set_state(StartRegistration.description)


@router.message(StartRegistration.description)
async def get_description(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    if not message.text:
        await message.answer(t("enter_text", lang), reply_markup=skip_kb(lang))
        return
    if len(message.text) > 500:
        await message.answer(t("text_too_long", lang))
        return
    description = "" if message.text in ALL_SKIP else message.text
    await state.update_data(description=description, temp_media=[])
    await message.answer(t("ask_photo", lang), reply_markup=ReplyKeyboardRemove())
    await state.set_state(StartRegistration.photo)


@router.message(StartRegistration.photo)
async def get_photo(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    data = await state.get_data()
    temp_media: list = data.get("temp_media", [])

    if message.text in ALL_DONE:
        if not temp_media:
            await message.answer(t("send_at_least_one", lang))
            return
        await _show_confirmation(message, state, lang, data, temp_media)
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
        await _show_confirmation(message, state, lang, data, temp_media)


async def _show_confirmation(message: Message, state: FSMContext, lang: str, data: dict, temp_media: list):
    caption = build_profile_caption(data["name"], data["age"], data["city"], data["description"])
    await message.answer(t("profile_preview", lang))
    await send_media(message, temp_media, caption)
    await message.answer(t("confirm_prompt", lang), reply_markup=end_kb(lang))
    await state.set_state(StartRegistration.confirm)


@router.message(StartRegistration.confirm)
async def confirm(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    data = await state.get_data()

    if message.text in ALL_YES:
        add_profile(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            name=data["name"],
            age=data["age"],
            city=data["city"],
            gender=data["gender"],
            looking_for=data["looking_for"],
            description=data["description"],
        )
        clear_media(message.from_user.id)
        for file_id, media_type in data["temp_media"]:
            add_media(message.from_user.id, file_id, media_type)
        await state.clear()
        await message.answer(t("profile_saved", lang), reply_markup=main_menu_kb(lang))

    elif message.text in ALL_EDIT:
        await state.clear()
        await message.answer(t("ask_age", lang), reply_markup=ReplyKeyboardRemove())
        await state.set_state(StartRegistration.age)

    else:
        await message.answer(t("choose_button", lang), reply_markup=end_kb(lang))
