import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.order import Order, OrderStatus, OrderItem
from src.repositories.order import OrderRepository, OrderItemRepository
from src.repositories.product import ProductRepository
from src.services.cart import CartService
from redis.asyncio import Redis
from typing import List

logger = structlog.get_logger(__name__)


class OrderService:
    """Service for order operations"""

    def __init__(self, session: AsyncSession, redis: Redis):
        self.order_repo = OrderRepository(session)
        self.order_item_repo = OrderItemRepository(session)
        self.product_repo = ProductRepository(session)
        self.cart_service = CartService(redis, session)
        self.session = session

    async def create_order_from_cart(self, user_id: int, notes: str = "") -> Order | None:
        """Create order from user's cart"""
        cart = await self.cart_service.get_cart(user_id)
        if not cart:
            logger.warning("Cannot create order from empty cart", user_id=user_id)
            return None

        # Calculate total
        total_price = await self.cart_service.get_cart_total(user_id)

        # Create order
        order = await self.order_repo.create(
            user_id=user_id,
            total_price=total_price,
            notes=notes,
            status=OrderStatus.PENDING,
        )

        # Create order items and reserve stock
        for product_id_str, item_data in cart.items():
            product_id = int(product_id_str)
            quantity = item_data["quantity"]

            # Create order item
            await self.order_item_repo.create_item(
                order_id=order.id,
                product_id=product_id,
                quantity=quantity,
                price=item_data["price"],
            )

            # Reserve stock
            await self.product_repo.decrease_stock(product_id, quantity)

        await self.order_repo.commit()
        await self.cart_service.clear_cart(user_id)

        logger.info(
            "Order created",
            order_id=order.id,
            user_id=user_id,
            total=total_price,
            items=len(cart),
        )
        return order

    async def get_user_orders(
        self, user_id: int, page: int = 1, page_size: int = 10
    ) -> tuple[List[Order], int]:
        """Get user's orders with pagination"""
        skip = (page - 1) * page_size
        orders = await self.order_repo.get_user_orders(user_id, skip=skip, limit=page_size)
        total = await self.order_repo.count_user_orders(user_id)
        total_pages = (total + page_size - 1) // page_size
        return orders, total_pages

    async def get_order(self, order_id: int) -> Order | None:
        """Get order by ID"""
        return await self.order_repo.get_by_id(order_id)

    async def update_order_status(self, order_id: int, status: OrderStatus) -> Order | None:
        """Update order status"""
        order = await self.order_repo.update_status(order_id, status)
        if order:
            await self.order_repo.commit()
            logger.info("Order status updated", order_id=order_id, status=status)
        return order

    async def cancel_order(self, order_id: int) -> bool:
        """Cancel order and release stock"""
        order = await self.order_repo.get_by_id(order_id)
        if not order or order.status != OrderStatus.PENDING:
            return False

        # Release stock for all items
        for item in order.items:
            await self.product_repo.increase_stock(item.product_id, item.quantity)

        # Update order status
        order.status = OrderStatus.CANCELLED
        await self.order_repo.commit()

        logger.info("Order cancelled", order_id=order_id, user_id=order.user_id)
        return True

    async def get_all_orders(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[List[Order], int]:
        """Get all orders (for admin)"""
        skip = (page - 1) * page_size
        orders = await self.order_repo.get_all_orders(skip=skip, limit=page_size)
        # Calculate total from all orders
        all_orders = await self.order_repo.get_all_orders(skip=0, limit=10000)
        total = len(all_orders)
        total_pages = (total + page_size - 1) // page_size
        return orders, total_pages

    async def get_orders_by_status(
        self, status: OrderStatus, page: int = 1, page_size: int = 20
    ) -> tuple[List[Order], int]:
        """Get orders by status"""
        skip = (page - 1) * page_size
        orders = await self.order_repo.get_orders_by_status(status, skip=skip, limit=page_size)
        total = await self.order_repo.count_orders_by_status(status)
        total_pages = (total + page_size - 1) // page_size
        return orders, total_pages

    async def get_stats(self) -> dict:
        """Get order statistics"""
        pending = await self.order_repo.count_orders_by_status(OrderStatus.PENDING)
        confirmed = await self.order_repo.count_orders_by_status(OrderStatus.CONFIRMED)
        shipped = await self.order_repo.count_orders_by_status(OrderStatus.SHIPPED)
        delivered = await self.order_repo.count_orders_by_status(OrderStatus.DELIVERED)
        cancelled = await self.order_repo.count_orders_by_status(OrderStatus.CANCELLED)
        revenue = await self.order_repo.get_total_revenue()

        return {
            "pending": pending,
            "confirmed": confirmed,
            "shipped": shipped,
            "delivered": delivered,
            "cancelled": cancelled,
            "total_revenue": revenue,
        }
