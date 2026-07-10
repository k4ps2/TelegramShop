import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.product import Product
from src.repositories.product import ProductRepository
from typing import List

logger = structlog.get_logger(__name__)


class ProductService:
    """Service for product operations"""

    def __init__(self, session: AsyncSession):
        self.repository = ProductRepository(session)
        self.session = session

    async def get_products_paginated(
        self, page: int = 1, page_size: int = 5
    ) -> tuple[List[Product], int]:
        """Get products with pagination"""
        skip = (page - 1) * page_size
        products = await self.repository.get_active_products(skip=skip, limit=page_size)
        total = await self.repository.count_active_products()
        total_pages = (total + page_size - 1) // page_size
        logger.info("Products retrieved", page=page, total_products=len(products))
        return products, total_pages

    async def search_products(
        self, query: str, page: int = 1, page_size: int = 5
    ) -> tuple[List[Product], int]:
        """Search products"""
        skip = (page - 1) * page_size
        products = await self.repository.search_products(
            query, skip=skip, limit=page_size
        )
        logger.info("Products searched", query=query, found=len(products))
        return products, (len(products) // page_size) + 1

    async def get_product(self, product_id: int) -> Product | None:
        """Get product by ID"""
        product = await self.repository.get_by_id(product_id)
        return product

    async def create_product(
        self,
        name: str,
        name_en: str,
        description: str | None,
        description_en: str | None,
        price: float,
        stock: int,
    ) -> Product:
        """Create new product"""
        product = await self.repository.create(
            name=name,
            name_en=name_en,
            description=description,
            description_en=description_en,
            price=price,
            stock=stock,
            is_active=True,
        )
        await self.repository.commit()
        logger.info("Product created", product_id=product.id, name=name)
        return product

    async def update_product(
        self,
        product_id: int,
        **kwargs
    ) -> Product | None:
        """Update product"""
        product = await self.repository.update(product_id, **kwargs)
        if product:
            await self.repository.commit()
            logger.info("Product updated", product_id=product_id)
        return product

    async def deactivate_product(self, product_id: int) -> bool:
        """Deactivate product"""
        product = await self.repository.update(product_id, is_active=False)
        if product:
            await self.repository.commit()
            logger.info("Product deactivated", product_id=product_id)
            return True
        return False

    async def check_stock(self, product_id: int, quantity: int) -> bool:
        """Check if enough stock available"""
        product = await self.repository.get_by_id(product_id)
        return product is not None and product.stock >= quantity

    async def reserve_stock(self, product_id: int, quantity: int) -> bool:
        """Reserve stock for order"""
        success = await self.repository.decrease_stock(product_id, quantity)
        if success:
            await self.repository.commit()
            logger.info("Stock reserved", product_id=product_id, quantity=quantity)
        return success

    async def release_stock(self, product_id: int, quantity: int) -> bool:
        """Release reserved stock"""
        success = await self.repository.increase_stock(product_id, quantity)
        if success:
            await self.repository.commit()
            logger.info("Stock released", product_id=product_id, quantity=quantity)
        return success

    async def get_low_stock_products(self) -> List[Product]:
        """Get products with low stock"""
        return await self.repository.get_low_stock_products()

    async def get_stats(self) -> dict:
        """Get product statistics"""
        total = await self.repository.count_active_products()
        low_stock = await self.repository.get_low_stock_products()
        return {
            "total_products": total,
            "low_stock_count": len(low_stock),
        }
