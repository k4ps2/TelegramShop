from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.user import User

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(self, telegram_id: int, username: str = None, full_name: str = None):
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        
        return user

    async def get_user(self, telegram_id: int):
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
