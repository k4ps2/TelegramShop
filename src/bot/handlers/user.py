from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import structlog
from sqlalchemy import select

from src.bot.keyboards.main import get_main_keyboard, get_catalog_keyboard
from src.core.database import AsyncSessionLocal
from src.models.product import Product

logger = structlog.get_logger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Добро пожаловать в <b>Online Shop</b>! 👋\n\n"
        "Выберите действие в меню ниже:",
        reply_markup=get_main_keyboard()
    )
    logger.info("User started bot", user_id=message.from_user.id)

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Это тестовый магазин-бот для портфолио.")

@router.message(F.text == "🛒 Каталог")
async def show_catalog(message: Message):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Product).where(Product.is_active == True).limit(10)
        )
        products = result.scalars().all()

    if not products:
        await message.answer("Каталог пуст.")
        return

    text = "🛍 <b>Доступные товары</b>\n\n"
    for p in products:
        text += f"• <b>{p.name}</b> — {p.price} $ (в наличии: {p.stock})\n"

    await message.answer(text, reply_markup=get_catalog_keyboard())
