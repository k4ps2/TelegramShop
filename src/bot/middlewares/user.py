from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
import structlog

from src.core.database import AsyncSessionLocal
from src.services import UserService

logger = structlog.get_logger(__name__)


class UserMiddleware(BaseMiddleware):
    """Middleware for user tracking and creation"""

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        """Process update and ensure user exists in database"""

        user = None

        if isinstance(event, Message) and event.from_user:
            user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            user = event.from_user

        if user:
            try:
                async with AsyncSessionLocal() as session:
                    user_service = UserService(session)
                    db_user = await user_service.get_or_create_user(
                        user_id=user.id,
                        username=user.username,
                        full_name=user.full_name or "User",
                        language="en"
                    )
                    logger.debug("User processed", user_id=user.id)
            except Exception as e:
                logger.error("Error in UserMiddleware", error=str(e), user_id=user.id)

        return await handler(event, data)

