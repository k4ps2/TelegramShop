import structlog
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.bot.i18n import i18n
from src.bot.keyboards import AdminKeyboards, MainKeyboards
from src.services.product import ProductService
from src.services.order import OrderService
from src.services import UserService
from src.core.database import AsyncSessionLocal
from src.bot.config import settings
from src.models.order import OrderStatus
from redis.asyncio import from_url

logger = structlog.get_logger(__name__)

router = Router()


class AdminStates(StatesGroup):
    product_name = State()
    product_name_en = State()
    product_description = State()
    product_description_en = State()
    product_price = State()
    product_stock = State()


async def get_redis():
    """Get Redis connection"""
    return from_url(settings.redis_url)


async def get_user_language(user_id: int) -> str:
    """Get user language preference"""
    async with AsyncSessionLocal() as session:
        service = UserService(session)
        user = await service.repository.get_by_id(user_id)
        return user.language if user else "en"


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in settings.ADMIN_IDS


@router.callback_query(F.data == "admin_add_product")
async def admin_add_product(callback: CallbackQuery, state: FSMContext) -> None:
    """Start adding product"""
    if not is_admin(callback.from_user.id):
        await callback.answer(i18n("error_access_denied", "en"))
        return

    language = await get_user_language(callback.from_user.id)
    text = "Enter product name (RU):"
    await callback.message.answer(text)
    await state.set_state(AdminStates.product_name)
    await callback.answer()


@router.message(AdminStates.product_name)
async def admin_product_name(message: Message, state: FSMContext) -> None:
    """Product name (Russian)"""
    await state.update_data(product_name=message.text)
    await message.answer("Enter product name (EN):")
    await state.set_state(AdminStates.product_name_en)


@router.message(AdminStates.product_name_en)
async def admin_product_name_en(message: Message, state: FSMContext) -> None:
    """Product name (English)"""
    await state.update_data(product_name_en=message.text)
    await message.answer("Enter product description (RU):")
    await state.set_state(AdminStates.product_description)


@router.message(AdminStates.product_description)
async def admin_product_description(message: Message, state: FSMContext) -> None:
    """Product description (Russian)"""
    await state.update_data(product_description=message.text)
    await message.answer("Enter product description (EN):")
    await state.set_state(AdminStates.product_description_en)


@router.message(AdminStates.product_description_en)
async def admin_product_description_en(message: Message, state: FSMContext) -> None:
    """Product description (English)"""
    await state.update_data(product_description_en=message.text)
    await message.answer("Enter product price:")
    await state.set_state(AdminStates.product_price)


@router.message(AdminStates.product_price)
async def admin_product_price(message: Message, state: FSMContext) -> None:
    """Product price"""
    try:
        price = float(message.text)
        await state.update_data(product_price=price)
        await message.answer("Enter stock quantity:")
        await state.set_state(AdminStates.product_stock)
    except ValueError:
        await message.answer("Invalid price. Enter number:")


@router.message(AdminStates.product_stock)
async def admin_product_stock(message: Message, state: FSMContext) -> None:
    """Product stock"""
    try:
        stock = int(message.text)
        data = await state.get_data()

        async with AsyncSessionLocal() as session:
            service = ProductService(session)
            product = await service.create_product(
                name=data["product_name"],
                name_en=data["product_name_en"],
                description=data["product_description"],
                description_en=data["product_description_en"],
                price=data["product_price"],
                stock=stock,
            )

        text = f"✅ Product created!\nID: {product.id}\nName: {product.name}"
        await message.answer(text, reply_markup=AdminKeyboards.admin_menu("en"))
        await state.clear()
        logger.info("Product created by admin", admin_id=message.from_user.id, product_id=product.id)
    except ValueError:
        await message.answer("Invalid stock. Enter number:")


@router.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery) -> None:
    """Show all orders (admin)"""
    if not is_admin(callback.from_user.id):
        await callback.answer(i18n("error_access_denied", "en"))
        return

    language = await get_user_language(callback.from_user.id)

    redis = await get_redis()
    async with AsyncSessionLocal() as session:
        order_service = OrderService(session, redis)
        orders, total_pages = await order_service.get_all_orders(page=1)

    if not orders:
        text = i18n("orders_empty", language)
        await callback.message.answer(text, reply_markup=AdminKeyboards.admin_menu(language))
        await callback.answer()
        return

    text = f"<b>{i18n('view_orders', language)}</b>\n\n"

    for order in orders:
        status = i18n(f"status_{order.status.value}", language)
        user_name = order.user.full_name
        date = order.created_at.strftime("%d.%m.%Y %H:%M")

        text += f"#{order.id} | {date}\n"
        text += f"User: {user_name} (ID: {order.user_id})\n"
        text += f"Status: {status} | {order.total_price:.2f}$\n"
        text += f"/admin_order_{order.id}\n\n"

    keyboard = AdminKeyboards.admin_orders_pagination(1, total_pages, language)
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


@router.message(F.text.startswith("/admin_order_"))
async def admin_order_detail(message: Message) -> None:
    """View order details (admin)"""
    if not is_admin(message.from_user.id):
        await message.answer(i18n("error_access_denied", "en"))
        return

    language = await get_user_language(message.from_user.id)

    try:
        order_id = int(message.text.split("_")[2])
    except (ValueError, IndexError):
        await message.answer(i18n("error_invalid_input", language))
        return

    redis = await get_redis()
    async with AsyncSessionLocal() as session:
        order_service = OrderService(session, redis)
        order = await order_service.get_order(order_id)

    if not order:
        await message.answer(i18n("error_order_not_found", language))
        return

    status = i18n(f"status_{order.status.value}", language)
    date = order.created_at.strftime("%d.%m.%Y %H:%M")

    text = f"<b>{i18n('order_details', language)}</b>\n\n"
    text += f"<b>ID:</b> #{order.id}\n"
    text += f"<b>User:</b> {order.user.full_name} (ID: {order.user_id})\n"
    text += f"<b>{i18n('order_date', language)}:</b> {date}\n"
    text += f"<b>{i18n('order_status', language)}:</b> {status}\n\n"

    text += f"<b>{i18n('cart_items', language)}:</b>\n"
    for item in order.items:
        name = item.product.name
        text += f"• {name} x{item.quantity} = {item.price * item.quantity:.2f}$\n"

    text += f"\n<b>{i18n('cart_total', language)}:</b> {order.total_price:.2f}$"

    keyboard = AdminKeyboards.orders_status_selector(order_id, language)
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("order_status:"))
async def admin_update_order_status(callback: CallbackQuery) -> None:
    """Update order status"""
    if not is_admin(callback.from_user.id):
        await callback.answer(i18n("error_access_denied", "en"))
        return

    language = await get_user_language(callback.from_user.id)

    parts = callback.data.split(":")
    order_id = int(parts[1])
    status_value = parts[2]

    try:
        status = OrderStatus(status_value)
    except ValueError:
        await callback.answer(i18n("error_invalid_input", language))
        return

    redis = await get_redis()
    async with AsyncSessionLocal() as session:
        order_service = OrderService(session, redis)
        order = await order_service.update_order_status(order_id, status)

    if order:
        text = f"✅ {i18n('order_marked', language)} {i18n(f'status_{status.value}', language)}"
        await callback.answer(text)
        logger.info("Order status updated", admin_id=callback.from_user.id, order_id=order_id, status=status.value)
    else:
        await callback.answer(i18n("error_operation_failed", language))


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery) -> None:
    """Show statistics"""
    if not is_admin(callback.from_user.id):
        await callback.answer(i18n("error_access_denied", "en"))
        return

    language = await get_user_language(callback.from_user.id)

    redis = await get_redis()
    async with AsyncSessionLocal() as session:
        user_service = UserService(session)
        product_service = ProductService(session)
        order_service = OrderService(session, redis)

        user_stats = await user_service.get_stats()
        product_stats = await product_service.get_stats()
        order_stats = await order_service.get_stats()

    text = f"<b>{i18n('statistics', language)}</b>\n\n"

    text += f"<b>{i18n('users_stats', language)}:</b>\n"
    text += f"• Total: {user_stats['total_users']}\n"
    text += f"• Active: {user_stats['active_users']}\n\n"

    text += f"<b>{i18n('products_stats', language)}:</b>\n"
    text += f"• Total: {product_stats['total_products']}\n"
    text += f"• Low stock: {product_stats['low_stock_count']}\n\n"

    text += f"<b>{i18n('orders_stats', language)}:</b>\n"
    text += f"• Pending: {order_stats['pending']}\n"
    text += f"• Confirmed: {order_stats['confirmed']}\n"
    text += f"• Shipped: {order_stats['shipped']}\n"
    text += f"• Delivered: {order_stats['delivered']}\n"
    text += f"• Cancelled: {order_stats['cancelled']}\n"
    text += f"• Revenue: ${order_stats['total_revenue']:.2f}"

    await callback.message.answer(text, reply_markup=AdminKeyboards.admin_menu(language))
    await callback.answer()
