import asyncio
import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot.config import settings
from src.core.logging import setup_logging

logger = structlog.get_logger(__name__)

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()

async def main() -> None:
    setup_logging()

    logger.info("Бот запускается...",
                bot_username="@your_bot",
                environment="development")

    # Здесь позже подключим роутеры
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception("Критическая ошибка при запуске бота", exc_info=e)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
