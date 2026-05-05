from aiogram import Bot, Dispatcher, F
from aiogram.types import ChatMemberUpdated, Message, PreCheckoutQuery
import asyncio
import random

from config import BOT_TOKEN
from handlers import start, profile, viewing
from db import init_db, deactivate_profile, activate_profile, activate_premium, get_lang, get_all_active_users
from strings import t, SAFETY_TIPS
from keyboards import main_menu_kb

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start.router)
dp.include_router(profile.router)
dp.include_router(viewing.router)


@dp.my_chat_member()
async def on_chat_member_update(update: ChatMemberUpdated):
    if update.new_chat_member.status == "kicked":
        deactivate_profile(update.from_user.id)
    elif update.new_chat_member.status == "member":
        activate_profile(update.from_user.id)


@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@dp.message(F.successful_payment)
async def on_successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload  
    days = int(payload.split("_")[1])
    activate_premium(message.from_user.id, days)
    lang = get_lang(message.from_user.id)
    await message.answer(
        t("premium_activated", lang).format(days=days),
        reply_markup=main_menu_kb(lang),
    )


async def _safety_tips_loop(bot: Bot) -> None:
    while True:
        await asyncio.sleep(3600)
        users = get_all_active_users()
        for tg_id, lang in users:
            tip = random.choice(SAFETY_TIPS.get(lang, SAFETY_TIPS["ru"]))
            try:
                await bot.send_message(tg_id, tip)
            except Exception:
                pass
            await asyncio.sleep(0.05)  # пауза между сообщениями, чтобы не словить флуд-бан


async def main():
    init_db()
    asyncio.create_task(_safety_tips_loop(bot))
    await dp.start_polling(bot)


asyncio.run(main())
