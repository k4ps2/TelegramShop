import asyncio
import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from redis.asyncio import from_url

from src.bot.config import settings
from src.core.logging import setup_logging
from src.core.database import init_db
from src.bot.i18n import i18n
from src.bot.handlers.user import router as user_router
from src.bot.handlers.shop import router as shop_router
from src.bot.handlers.cart import router as cart_router
from src.bot.handlers.order import router as order_router
from src.bot.handlers.admin import router as admin_router
from src.bot.middlewares.user import UserMiddleware

logger = structlog.get_logger(__name__)

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()

# Подключаем роутеры
dp.include_router(user_router)
dp.include_router(shop_router)
dp.include_router(cart_router)
dp.include_router(order_router)
dp.include_router(admin_router)

# Middleware
dp.message.middleware(UserMiddleware())
dp.callback_query.middleware(UserMiddleware())


async def main() -> None:
    """Main entry point"""
    setup_logging()

    logger.info(
        "Bot is starting...",
        bot_token_prefix=settings.BOT_TOKEN[:10],
        environment="production"
    )

    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")

        # Test Redis connection
        redis = from_url(settings.redis_url)
        await redis.ping()
        await redis.close()
        logger.info("Redis connection verified")

        # Start polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception("Critical error", exc_info=e)
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

