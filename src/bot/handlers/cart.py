import structlog
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.bot.i18n import i18n
from src.bot.keyboards import CartKeyboards, MainKeyboards
from src.services.cart import CartService
from src.core.database import AsyncSessionLocal
from src.bot.config import settings
from redis.asyncio import from_url

logger = structlog.get_logger(__name__)

router = Router()


class CheckoutStates(StatesGroup):
    waiting_notes = State()


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


@router.message(F.text.contains("🛒"))
async def show_cart(message: Message) -> None:
    """Show user's cart"""
    user_id = message.from_user.id
    language = await get_user_language(user_id)

    redis = await get_redis()
    cart_service = CartService(redis, AsyncSessionLocal())
    cart_details = await cart_service.get_cart_details(user_id)

    if cart_details["is_empty"]:
        text = i18n("cart_empty", language)
        await message.answer(text, reply_markup=CartKeyboards.cart_menu(is_empty=True, language=language))
        return

    text = f"<b>{i18n('cart_items', language)}:</b>\n\n"
    total_items = 0

    for product_id_str, item in cart_details["items"].items():
        product_id = int(product_id_str)
        name = item["name"]
        qty = item["quantity"]
        price = item["price"]
        item_total = qty * price
        total_items += qty

        text += f"• {name}\n"
        text += f"  {qty}x {price}$ = <b>{item_total}$</b>\n"

    text += f"\n<b>{i18n('cart_total', language)}: {cart_details['total']:.2f}$</b>\n"

    await message.answer(text, reply_markup=CartKeyboards.cart_menu(is_empty=False, language=language))


@router.callback_query(F.data.startswith("cart_increase:"))
async def increase_quantity(callback: CallbackQuery) -> None:
    """Increase item quantity"""
    user_id = callback.from_user.id
    language = await get_user_language(user_id)

    product_id = int(callback.data.split(":")[1])

    redis = await get_redis()
    cart_service = CartService(redis, AsyncSessionLocal())
    cart = await cart_service.get_cart(user_id)

    if str(product_id) in cart:
        current_qty = cart[str(product_id)]["quantity"]
        await cart_service.update_quantity(user_id, product_id, current_qty + 1)
        await callback.answer(i18n("success", language))
    else:
        await callback.answer(i18n("error_operation_failed", language))

    logger.info("Cart quantity increased", user_id=user_id, product_id=product_id)


@router.callback_query(F.data.startswith("cart_decrease:"))
async def decrease_quantity(callback: CallbackQuery) -> None:
    """Decrease item quantity"""
    user_id = callback.from_user.id
    language = await get_user_language(user_id)

    product_id = int(callback.data.split(":")[1])

    redis = await get_redis()
    cart_service = CartService(redis, AsyncSessionLocal())
    cart = await cart_service.get_cart(user_id)

    if str(product_id) in cart:
        current_qty = cart[str(product_id)]["quantity"]
        if current_qty > 1:
            await cart_service.update_quantity(user_id, product_id, current_qty - 1)
        else:
            await cart_service.remove_from_cart(user_id, product_id)
        await callback.answer(i18n("success", language))
    else:
        await callback.answer(i18n("error_operation_failed", language))

    logger.info("Cart quantity decreased", user_id=user_id, product_id=product_id)


@router.callback_query(F.data.startswith("cart_remove:"))
async def remove_from_cart(callback: CallbackQuery) -> None:
    """Remove item from cart"""
    user_id = callback.from_user.id
    language = await get_user_language(user_id)

    product_id = int(callback.data.split(":")[1])

    redis = await get_redis()
    cart_service = CartService(redis, AsyncSessionLocal())
    success = await cart_service.remove_from_cart(user_id, product_id)

    if success:
        await callback.answer(i18n("success", language))
    else:
        await callback.answer(i18n("error_operation_failed", language))

    logger.info("Item removed from cart", user_id=user_id, product_id=product_id)


@router.callback_query(F.data == "clear_cart_confirm")
async def confirm_clear_cart(callback: CallbackQuery) -> None:
    """Confirm clear cart"""
    language = await get_user_language(callback.from_user.id)

    text = f"{i18n('error', language)}?"
    await callback.message.answer(text, reply_markup=CartKeyboards.confirm_clear_cart(language))
    await callback.answer()


@router.callback_query(F.data == "clear_cart_yes")
async def clear_cart_yes(callback: CallbackQuery) -> None:
    """Clear cart confirmed"""
    user_id = callback.from_user.id
    language = await get_user_language(user_id)

    redis = await get_redis()
    cart_service = CartService(redis, AsyncSessionLocal())
    await cart_service.clear_cart(user_id)

    text = f"{i18n('success', language)} - {i18n('cart', language)} {i18n('error_product_not_found', language).lower()}"
    await callback.message.answer(text, reply_markup=CartKeyboards.cart_menu(is_empty=True, language=language))
    await callback.answer()
    logger.info("Cart cleared", user_id=user_id)


@router.callback_query(F.data == "clear_cart_no")
async def clear_cart_no(callback: CallbackQuery) -> None:
    """Cancel clear cart"""
    await callback.answer()


@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, state: FSMContext) -> None:
    """Start checkout process"""
    user_id = callback.from_user.id
    language = await get_user_language(user_id)

    redis = await get_redis()
    cart_service = CartService(redis, AsyncSessionLocal())
    cart = await cart_service.get_cart(user_id)

    if not cart:
        await callback.answer(i18n("cart_empty", language), show_alert=True)
        return

    text = f"<b>{i18n('order_details', language)}</b>\n\n"
    text += f"{i18n('order_total', language)}: {await cart_service.get_cart_total(user_id):.2f}$\n\n"
    text += f"<b>{i18n('success', language)}</b>"

    await callback.message.answer(text, reply_markup=MainKeyboards.back_to_menu(language))
    await state.set_state(CheckoutStates.waiting_notes)

    from src.services.order import OrderService
    async with AsyncSessionLocal() as session:
        order_service = OrderService(session, redis)
        order = await order_service.create_order_from_cart(user_id)

    if order:
        text = f"✅ {i18n('success', language)}\n"
        text += f"ID: #{order.id}\n"
        text += f"{i18n('order_total', language)}: {order.total_price:.2f}$"
        await callback.message.answer(text)
        logger.info("Order created", user_id=user_id, order_id=order.id)
    else:
        await callback.message.answer(i18n("error_operation_failed", language))

    await state.clear()
    await callback.answer()
