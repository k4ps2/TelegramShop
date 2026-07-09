from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.core.database import AsyncSessionLocal
from src.models.user import User

logger = structlog.get_logger(__name__)

class UserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        user = event.from_user
        async with AsyncSessionLocal() as session:
            db_user = await session.get(User, user.id)
            if not db_user:
                db_user = User(
                    id=user.id,
                    username=user.username,
                    full_name=user.full_name or user.username or "Unknown"
                )
                session.add(db_user)
                await session.commit()
                logger.info("New user registered", user_id=user.id)
            else:
                # Можно обновлять данные
                pass

        data["session"] = session  # для использования в handlers
        return await handler(event, data)
