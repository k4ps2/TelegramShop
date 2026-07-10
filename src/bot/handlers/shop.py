import structlog
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.bot.i18n import i18n
from src.bot.keyboards import ProductKeyboards, CartKeyboards, MainKeyboards
from src.services.product import ProductService
from src.services.cart import CartService
from src.core.database import AsyncSessionLocal
from src.bot.config import settings
from redis.asyncio import from_url

logger = structlog.get_logger(__name__)

router = Router()


class SearchStates(StatesGroup):
    searching = State()


async def get_redis():
    """Get Redis connection"""
    return from_url(settings.redis_url)


async def get_user_language(user_id: int) -> str:
    """Get user language preference"""
    async with AsyncSessionLocal() as session:
        from src.services import UserService
        service = UserService(session)
        user = await service.repository.get_by_id(user_id)
        return user.language if user else "en"


@router.message(F.text.contains("📚"))
async def show_catalog(message: Message, state: FSMContext) -> None:
    """Show catalog with pagination"""
    user_id = message.from_user.id
    language = await get_user_language(user_id)

    async with AsyncSessionLocal() as session:
        service = ProductService(session)
        products, total_pages = await service.get_products_paginated(page=1, page_size=settings.ITEMS_PER_PAGE)

    if not products:
        await message.answer(i18n("error_product_not_found", language))
        return

    await state.clear()
    await show_products_page(message, products, page=1, total_pages=total_pages, language=language)
    logger.info("Catalog viewed", user_id=user_id)


@router.callback_query(F.data.startswith("catalog_page:"))
async def catalog_pagination(callback: CallbackQuery) -> None:
    """Handle catalog pagination"""
    user_id = callback.from_user.id
    language = await get_user_language(user_id)

    page = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        service = ProductService(session)
        products, total_pages = await service.get_products_paginated(page=page, page_size=settings.ITEMS_PER_PAGE)

    if not products:
        await callback.answer(i18n("error_product_not_found", language))
        return

    await show_products_page(callback.message, products, page=page, total_pages=total_pages, language=language)
    await callback.answer()


async def show_products_page(message, products, page: int, total_pages: int, language: str) -> None:
    """Display products page"""
    text = f"<b>{i18n('shop_catalog', language)}</b>\n\n"

    for i, product in enumerate(products, 1):
        name = product.name if language == "ru" else product.name_en
        description = product.description if language == "ru" else product.description_en
        stock = i18n("stock", language)

        text += f"{i}. <b>{name}</b>\n"
        if description:
            text += f"<i>{description[:50]}...</i>\n"
        text += f"💰 {product.price}$ | {stock}: {product.stock}\n"
        text += f"/product_{product.id}\n\n"

    keyboard = ProductKeyboards.catalog_pagination(page, total_pages, language)
    await message.answer(text, reply_markup=keyboard)


@router.message(F.text.startswith("/product_"))
async def show_product_detail(message: Message) -> None:
    """Show product details"""
    user_id = message.from_user.id
    language = await get_user_language(user_id)

    try:
        product_id = int(message.text.split("_")[1])
    except (ValueError, IndexError):
        await message.answer(i18n("error_invalid_input", language))
        return

    async with AsyncSessionLocal() as session:
        service = ProductService(session)
        product = await service.get_product(product_id)

    if not product:
        await message.answer(i18n("error_product_not_found", language))
        return

    name = product.name if language == "ru" else product.name_en
    description = product.description if language == "ru" else product.description_en
    stock = i18n("stock", language)

    text = f"<b>{i18n('product_details', language)}</b>\n\n"
    text += f"<b>{name}</b>\n"
    if description:
        text += f"{description}\n\n"
    text += f"💰 <b>{i18n('price', language)}:</b> {product.price}$\n"
    text += f"📦 <b>{stock}:</b> {product.stock}\n"

    keyboard = ProductKeyboards.product_detail(product_id, language)
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("add_to_cart:"))
async def add_to_cart_quantity(callback: CallbackQuery) -> None:
    """Ask for quantity"""
    language = await get_user_language(callback.from_user.id)
    product_id = int(callback.data.split(":")[1])

    text = i18n("select_quantity", language)
    keyboard = ProductKeyboards.select_quantity(product_id, language)

    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("qty_select:"))
async def confirm_add_to_cart(callback: CallbackQuery) -> None:
    """Add to cart with selected quantity"""
    user_id = callback.from_user.id
    language = await get_user_language(user_id)

    parts = callback.data.split(":")
    product_id = int(parts[1])
    quantity = int(parts[2])

    redis = await get_redis()
    cart_service = CartService(redis, AsyncSessionLocal())

    success = await cart_service.add_to_cart(user_id, product_id, quantity)

    if success:
        text = i18n("add_to_cart_success", language)
    else:
        text = i18n("error_operation_failed", language)

    await callback.message.answer(text)
    await callback.answer()
    logger.info("Item added to cart", user_id=user_id, product_id=product_id, qty=quantity)


@router.callback_query(F.data == "catalog_back")
async def back_to_catalog(callback: CallbackQuery) -> None:
    """Back to catalog"""
    user_id = callback.from_user.id
    language = await get_user_language(user_id)

    async with AsyncSessionLocal() as session:
        service = ProductService(session)
        products, total_pages = await service.get_products_paginated(page=1, page_size=settings.ITEMS_PER_PAGE)

    await show_products_page(callback.message, products, page=1, total_pages=total_pages, language=language)
    await callback.answer()

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
