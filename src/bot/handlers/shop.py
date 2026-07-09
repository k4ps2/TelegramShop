from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy import select
import structlog

from src.core.database import AsyncSessionLocal
from src.models.product import Product
from src.bot.keyboards.main import get_main_keyboard

logger = structlog.get_logger(__name__)
router = Router()

@router.message(F.text == "🛒 Каталог")
async def show_catalog(message: Message):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product).where(Product.is_active == True))
        products = result.scalars().all()

    if not products:
        await message.answer("Каталог пуст.")
        return

    text = "🛍 <b>Каталог товаров</b>\n\n"
    for p in products:
        text += f"<b>{p.name}</b> — {p.price}$ (в наличии: {p.stock})\n"
        text += f"/add_{p.id} — добавить в корзину\n\n"

    await message.answer(text)

@router.message(F.text.startswith("/add_"))
async def add_to_cart(message: Message):
    try:
        product_id = int(message.text.split("_")[1])
        user_id = message.from_user.id

        # Добавляем в Redis
        await redis_client.sadd(f"cart:{user_id}", product_id)
        await message.answer("✅ Товар добавлен в корзину!")
    except:
        await message.answer("Ошибка.")

@router.message(F.text == "🛍 Мои заказы")
async def show_cart(message: Message):
    user_id = message.from_user.id
    cart_items = await redis_client.smembers(f"cart:{user_id}")

    if not cart_items:
        await message.answer("Корзина пуста.")
        return

    text = "🛍 Ваша корзина:\n\n"
    total = 0
    async with AsyncSessionLocal() as session:
        for pid in cart_items:
            product = await session.get(Product, int(pid))
            if product:
                text += f"• {product.name} — {product.price}$\n"
                total += product.price

    text += f"\nИтого: {total:.2f}$"
    await message.answer(text)
