from typing import Optional, List
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.order import Order, OrderItem, OrderStatus
from src.repositories import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """Repository for Order model"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Order)

    async def get_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID with items"""
        query = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_user_orders(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get all orders for a user"""
        query = (
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.items))
            .order_by(desc(Order.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_orders_by_status(
        self, status: OrderStatus, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders by status"""
        query = (
            select(Order)
            .where(Order.status == status)
            .options(selectinload(Order.items))
            .order_by(desc(Order.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_all_orders(self, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get all orders"""
        query = (
            select(Order)
            .options(selectinload(Order.items))
            .order_by(desc(Order.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_user_orders(self, user_id: int) -> int:
        """Count orders for a user"""
        query = select(Order).where(Order.user_id == user_id)
        result = await self.session.execute(query)
        return len(result.scalars().all())

    async def count_orders_by_status(self, status: OrderStatus) -> int:
        """Count orders by status"""
        query = select(Order).where(Order.status == status)
        result = await self.session.execute(query)
        return len(result.scalars().all())

    async def update_status(self, order_id: int, status: OrderStatus) -> Optional[Order]:
        """Update order status"""
        order = await self.get_by_id(order_id)
        if order:
            order.status = status
            await self.session.flush()
        return order

    async def get_total_revenue(self) -> float:
        """Get total revenue from delivered orders"""
        query = (
            select(Order)
            .where(Order.status == OrderStatus.DELIVERED)
        )
        result = await self.session.execute(query)
        orders = result.scalars().all()
        return sum(order.total_price for order in orders)


class OrderItemRepository(BaseRepository[OrderItem]):
    """Repository for OrderItem model"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, OrderItem)

    async def get_order_items(self, order_id: int) -> List[OrderItem]:
        """Get all items for an order"""
        query = (
            select(OrderItem)
            .where(OrderItem.order_id == order_id)
            .options(selectinload(OrderItem.product))
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create_item(
        self, order_id: int, product_id: int, quantity: int, price: float
    ) -> OrderItem:
        """Create order item"""
        item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            price=price,
        )
        self.session.add(item)
        await self.session.flush()
        return item
