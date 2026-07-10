import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User
from src.repositories.user import UserRepository

logger = structlog.get_logger(__name__)


class UserService:
    """Service for user operations"""

    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)
        self.session = session

    async def get_or_create_user(
        self, user_id: int, username: str | None, full_name: str, language: str = "en"
    ) -> User:
        """Get existing user or create new one"""
        user = await self.repository.get_by_id(user_id)
        if user:
            logger.info("User retrieved", user_id=user_id)
            return user

        user = await self.repository.create(
            id=user_id,
            username=username,
            full_name=full_name,
            language=language,
        )
        await self.repository.commit()
        logger.info("User created", user_id=user_id, username=username)
        return user

    async def update_user_language(self, user_id: int, language: str) -> bool:
        """Update user language preference"""
        user = await self.repository.update(user_id, language=language)
        if user:
            await self.repository.commit()
            logger.info("User language updated", user_id=user_id, language=language)
            return True
        return False

    async def set_admin(self, user_id: int, is_admin: bool = True) -> bool:
        """Set/unset admin status"""
        user = await self.repository.update(user_id, is_admin=is_admin)
        if user:
            await self.repository.commit()
            logger.info("Admin status updated", user_id=user_id, is_admin=is_admin)
            return True
        return False

    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user"""
        user = await self.repository.update(user_id, is_active=False)
        if user:
            await self.repository.commit()
            logger.info("User deactivated", user_id=user_id)
            return True
        return False

    async def get_stats(self) -> dict:
        """Get user statistics"""
        total = await self.repository.count_users()
        active = await self.repository.count_active_users()
        return {
            "total_users": total,
            "active_users": active,
            "inactive_users": total - active,
        }
