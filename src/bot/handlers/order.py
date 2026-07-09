from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import structlog
from redis.asyncio import Redis
from src.bot.config import settings

logger = structlog.get_logger(__name__)
router = Router()
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

@router.message(Command("checkout"))
async def checkout(message: Message):
    user_id = message.from_user.id
    cart = await redis_client.smembers(f"cart:{user_id}")

    if not cart:
        await message.answer("Корзина пуста.")
        return

    # Здесь можно добавить логику создания заказа в БД
    await message.answer(
        "✅ Заказ оформлен!\n\n"
        "Мы свяжемся с вами для подтверждения.\n"
        "Спасибо за покупку! 🎉"
    )

    # Очищаем корзину
    await redis_client.delete(f"cart:{user_id}")
    logger.info("Order completed", user_id=user_id, items=len(cart))
