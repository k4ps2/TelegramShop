from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User
from src.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by Telegram ID"""
        return await self.session.get(User, user_id)

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_all_admins(self) -> list[User]:
        """Get all admin users"""
        query = select(User).where(User.is_admin == True).order_by(User.created_at)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get active users"""
        query = (
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_users(self) -> int:
        """Count total users"""
        query = select(User)
        result = await self.session.execute(query)
        return len(result.scalars().all())

    async def count_active_users(self) -> int:
        """Count active users"""
        query = select(User).where(User.is_active == True)
        result = await self.session.execute(query)
        return len(result.scalars().all())
