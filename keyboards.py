from aiogram.types import (
    KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup,
)
from strings import t



first_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="👍")]],
    resize_keyboard=True,
)

done_media_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Готово ✅")]],
    resize_keyboard=True,
)

def viewing_kb(is_premium: bool = False) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text="❤️"), KeyboardButton(text="💌"),
             KeyboardButton(text="👎"), KeyboardButton(text="💤")]]
    if is_premium:
        rows.append([KeyboardButton(text="↩️")])  # отмена дизлайка — только для премиума
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

liked_me_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❤️"), KeyboardButton(text="👎")]],
    resize_keyboard=True,
)


language_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Українська"),
            KeyboardButton(text="Русский"),
            KeyboardButton(text="English"),
        ],
        [KeyboardButton(text="Назад")],
    ],
    resize_keyboard=True,
)



def back_only_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("btn_back", lang))]],
        resize_keyboard=True,
    )


def skip_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("btn_skip", lang))]],
        resize_keyboard=True,
    )


def gender_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text=t("btn_male", lang)),
            KeyboardButton(text=t("btn_female", lang)),
        ]],
        resize_keyboard=True,
    )


def looking_for_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text=t("btn_guys", lang)),
            KeyboardButton(text=t("btn_girls", lang)),
            KeyboardButton(text=t("btn_anyone", lang)),
        ]],
        resize_keyboard=True,
    )


def end_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text=t("btn_yes", lang)),
            KeyboardButton(text=t("btn_edit", lang)),
        ]],
        resize_keyboard=True,
    )


def main_menu_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t("btn_browse", lang)),
                KeyboardButton(text=t("btn_my_profile", lang)),
            ],
            [
                KeyboardButton(text=t("btn_refill", lang)),
                KeyboardButton(text=t("btn_change_photo", lang)),
            ],
            [
                KeyboardButton(text=t("btn_change_text", lang)),
                KeyboardButton(text=t("btn_settings", lang)),
            ],
            [KeyboardButton(text=t("btn_premium", lang))],
        ],
        resize_keyboard=True,
    )


def settings_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("btn_change_lang", lang))],
            [KeyboardButton(text=t("btn_back", lang))],
        ],
        resize_keyboard=True,
    )


def premium_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("btn_2d", lang)),  KeyboardButton(text=t("btn_10d", lang))],
            [KeyboardButton(text=t("btn_30d", lang)), KeyboardButton(text=t("btn_90d", lang))],
            [KeyboardButton(text=t("btn_back", lang))],
        ],
        resize_keyboard=True,
    )


# Inline-клавиатуры

def liked_notification_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Посмотреть 👀", callback_data="view_liked"),
        InlineKeyboardButton(text="Не сейчас",    callback_data="skip_liked"),
    ]])


def match_kb(reported_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Пожаловаться", callback_data=f"report_{reported_id}"),
    ]])
