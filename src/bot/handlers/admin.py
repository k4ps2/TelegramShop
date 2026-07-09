from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from src.bot.config import settings

router = Router()

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("Нет доступа.")
        return

    await message.answer(
        "🛠 <b>Админ-панель</b>\n\n"
        "/stats — статистика\n"
        "/addproduct — добавить товар"
    )
