from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.order import Order

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    full_name: Mapped[str] = mapped_column(String(128))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[str] = mapped_column(String(5), default="en")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")

    __table_args__ = (
        Index('idx_user_is_admin', 'is_admin'),
        Index('idx_user_is_active', 'is_active'),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, is_admin={self.is_admin})>"
