import asyncio
import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot.config import settings
from src.core.logging import setup_logging
from src.bot.handlers.user import router as user_router
from src.bot.middlewares.user import UserMiddleware
from src.bot.handlers.shop import router as shop_router
from src.bot.handlers.order import router as order_router

logger = structlog.get_logger(__name__)

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()

# Подключаем роутеры
dp.include_router(user_router)
dp.include_router(shop_router)
dp.include_router(order_router)
dp.message.middleware(UserMiddleware())

async def main() -> None:
    setup_logging()

    logger.info("Бот запускается...",
                bot_username="@your_bot",
                environment="development")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception("Критическая ошибка", exc_info=e)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
