from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, Boolean, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.order import OrderItem

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name_en: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    description: Mapped[str | None] = mapped_column(Text)
    description_en: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="product")

    __table_args__ = (
        Index('idx_product_active', 'is_active'),
        Index('idx_product_name', 'name'),
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"
