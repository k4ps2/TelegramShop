from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
import structlog
from redis.asyncio import Redis
from src.bot.config import settings

logger = structlog.get_logger(__name__)
router = Router()
redis = Redis.from_url(settings.redis_url, decode_responses=True)

@router.callback_query(F.data == "add_to_cart")
async def add_to_cart(callback: CallbackQuery):
    # Пока заглушка
    await callback.answer("Товар добавлен в корзину!", show_alert=True)
