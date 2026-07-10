import structlog
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from datetime import datetime

from src.bot.i18n import i18n
from src.bot.keyboards import OrderKeyboards, MainKeyboards
from src.services.order import OrderService
from src.core.database import AsyncSessionLocal
from src.models.order import OrderStatus
from src.bot.config import settings
from redis.asyncio import from_url

logger = structlog.get_logger(__name__)

router = Router()


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


@router.message(F.text.contains("📦"))
async def show_orders(message: Message) -> None:
    """Show user's orders"""
    user_id = message.from_user.id
    language = await get_user_language(user_id)

    redis = await get_redis()
    async with AsyncSessionLocal() as session:
        order_service = OrderService(session, redis)
        orders, total_pages = await order_service.get_user_orders(user_id, page=1)

    if not orders:
        text = i18n("orders_empty", language)
        await message.answer(text, reply_markup=OrderKeyboards.orders_list(1, 1, language))
        return

    text = f"<b>{i18n('my_orders', language)}</b>\n\n"

    for order in orders:
        status = i18n(f"status_{order.status.value}", language)
        date = order.created_at.strftime("%d.%m.%Y %H:%M")
        text += f"#{order.id} | {date}\n"
        text += f"{i18n('order_status', language)}: {status} | {order.total_price:.2f}$\n"
        text += f"/order_{order.id}\n\n"

    keyboard = OrderKeyboards.orders_list(1, total_pages, language)
    await message.answer(text, reply_markup=keyboard)
    logger.info("Orders viewed", user_id=user_id)


@router.message(F.text.startswith("/order_"))
async def show_order_detail(message: Message) -> None:
    """Show order details"""
    user_id = message.from_user.id
    language = await get_user_language(user_id)

    try:
        order_id = int(message.text.split("_")[1])
    except (ValueError, IndexError):
        await message.answer(i18n("error_invalid_input", language))
        return

    redis = await get_redis()
    async with AsyncSessionLocal() as session:
        order_service = OrderService(session, redis)
        order = await order_service.get_order(order_id)

    if not order or order.user_id != user_id:
        await message.answer(i18n("error_order_not_found", language))
        return

    status = i18n(f"status_{order.status.value}", language)
    date = order.created_at.strftime("%d.%m.%Y %H:%M")

    text = f"<b>{i18n('order_details', language)}</b>\n\n"
    text += f"<b>ID:</b> #{order.id}\n"
    text += f"<b>{i18n('order_date', language)}:</b> {date}\n"
    text += f"<b>{i18n('order_status', language)}:</b> {status}\n\n"

    text += f"<b>{i18n('cart_items', language)}:</b>\n"
    for item in order.items:
        name = item.product.name
        text += f"• {name} x{item.quantity} = {item.price * item.quantity:.2f}$\n"

    text += f"\n<b>{i18n('cart_total', language)}:</b> {order.total_price:.2f}$"

    if order.notes:
        text += f"\n\n<b>Notes:</b> {order.notes}"

    keyboard = OrderKeyboards.order_detail(order_id, language)
    await message.answer(text, reply_markup=keyboard)
    logger.info("Order detail viewed", user_id=user_id, order_id=order_id)


@router.callback_query(F.data.startswith("orders_page:"))
async def orders_pagination(callback: CallbackQuery) -> None:
    """Handle orders pagination"""
    user_id = callback.from_user.id
    language = await get_user_language(user_id)

    page = int(callback.data.split(":")[1])

    redis = await get_redis()
    async with AsyncSessionLocal() as session:
        order_service = OrderService(session, redis)
        orders, total_pages = await order_service.get_user_orders(user_id, page=page)

    if not orders:
        text = i18n("orders_empty", language)
        await callback.message.answer(text)
        await callback.answer()
        return

    text = f"<b>{i18n('my_orders', language)}</b>\n\n"

    for order in orders:
        status = i18n(f"status_{order.status.value}", language)
        date = order.created_at.strftime("%d.%m.%Y %H:%M")
        text += f"#{order.id} | {date}\n"
        text += f"{i18n('order_status', language)}: {status} | {order.total_price:.2f}$\n"
        text += f"/order_{order.id}\n\n"

    keyboard = OrderKeyboards.orders_list(page, total_pages, language)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "orders_back")
async def back_to_orders(callback: CallbackQuery) -> None:
    """Back to orders list"""
    user_id = callback.from_user.id
    language = await get_user_language(user_id)

    redis = await get_redis()
    async with AsyncSessionLocal() as session:
        order_service = OrderService(session, redis)
        orders, total_pages = await order_service.get_user_orders(user_id, page=1)

    if not orders:
        text = i18n("orders_empty", language)
        keyboard = OrderKeyboards.orders_list(1, 1, language)
    else:
        text = f"<b>{i18n('my_orders', language)}</b>\n\n"
        for order in orders:
            status = i18n(f"status_{order.status.value}", language)
            date = order.created_at.strftime("%d.%m.%Y %H:%M")
            text += f"#{order.id} | {date}\n"
            text += f"{i18n('order_status', language)}: {status} | {order.total_price:.2f}$\n"
            text += f"/order_{order.id}\n\n"

        keyboard = OrderKeyboards.orders_list(1, total_pages, language)

    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()
