from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.product import Product
from src.repositories import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Repository for Product model"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Product)

    async def get_active_products(
        self, skip: int = 0, limit: int = 100
    ) -> List[Product]:
        """Get all active products with pagination"""
        query = (
            select(Product)
            .where(Product.is_active == True)
            .order_by(Product.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def search_products(
        self, query_text: str, skip: int = 0, limit: int = 100
    ) -> List[Product]:
        """Search products by name or description"""
        query = (
            select(Product)
            .where(
                and_(
                    Product.is_active == True,
                    (Product.name.ilike(f"%{query_text}%"))
                    | (Product.description.ilike(f"%{query_text}%"))
                    | (Product.name_en.ilike(f"%{query_text}%"))
                    | (Product.description_en.ilike(f"%{query_text}%"))
                )
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_active_products(self) -> int:
        """Count active products"""
        query = select(Product).where(Product.is_active == True)
        result = await self.session.execute(query)
        return len(result.scalars().all())

    async def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
        """Get products with low stock"""
        query = (
            select(Product)
            .where(and_(Product.is_active == True, Product.stock < threshold))
            .order_by(Product.stock)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def decrease_stock(self, product_id: int, quantity: int) -> bool:
        """Decrease product stock"""
        product = await self.get_by_id(product_id)
        if product and product.stock >= quantity:
            product.stock -= quantity
            await self.session.flush()
            return True
        return False

    async def increase_stock(self, product_id: int, quantity: int) -> bool:
        """Increase product stock"""
        product = await self.get_by_id(product_id)
        if product:
            product.stock += quantity
            await self.session.flush()
            return True
        return False
