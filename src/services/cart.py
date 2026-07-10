import json
import structlog
from redis.asyncio import Redis
from src.models.product import Product
from src.repositories.product import ProductRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

logger = structlog.get_logger(__name__)


class CartService:
    """Service for shopping cart operations using Redis"""

    def __init__(self, redis: Redis, db_session: AsyncSession):
        self.redis = redis
        self.product_repo = ProductRepository(db_session)
        self.cart_expiry = 86400 * 7  # 7 days

    def _get_cart_key(self, user_id: int) -> str:
        """Get Redis key for user cart"""
        return f"cart:{user_id}"

    async def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> bool:
        """Add product to cart"""
        product = await self.product_repo.get_by_id(product_id)
        if not product or not product.is_active:
            logger.warning("Cannot add to cart", product_id=product_id, reason="inactive")
            return False

        if product.stock < quantity:
            logger.warning("Insufficient stock", product_id=product_id)
            return False

        cart_key = self._get_cart_key(user_id)
        cart_data = await self.redis.get(cart_key)
        cart = json.loads(cart_data) if cart_data else {}

        if str(product_id) in cart:
            cart[str(product_id)]["quantity"] += quantity
        else:
            cart[str(product_id)] = {
                "product_id": product_id,
                "quantity": quantity,
                "price": float(product.price),
                "name": product.name,
            }

        await self.redis.setex(cart_key, self.cart_expiry, json.dumps(cart))
        logger.info("Item added to cart", user_id=user_id, product_id=product_id, qty=quantity)
        return True

    async def remove_from_cart(self, user_id: int, product_id: int) -> bool:
        """Remove product from cart"""
        cart_key = self._get_cart_key(user_id)
        cart_data = await self.redis.get(cart_key)
        if not cart_data:
            return False

        cart = json.loads(cart_data)
        if str(product_id) not in cart:
            return False

        del cart[str(product_id)]
        if cart:
            await self.redis.setex(cart_key, self.cart_expiry, json.dumps(cart))
        else:
            await self.redis.delete(cart_key)

        logger.info("Item removed from cart", user_id=user_id, product_id=product_id)
        return True

    async def update_quantity(
        self, user_id: int, product_id: int, quantity: int
    ) -> bool:
        """Update product quantity in cart"""
        if quantity <= 0:
            return await self.remove_from_cart(user_id, product_id)

        product = await self.product_repo.get_by_id(product_id)
        if not product or product.stock < quantity:
            return False

        cart_key = self._get_cart_key(user_id)
        cart_data = await self.redis.get(cart_key)
        if not cart_data:
            return False

        cart = json.loads(cart_data)
        if str(product_id) not in cart:
            return False

        cart[str(product_id)]["quantity"] = quantity
        await self.redis.setex(cart_key, self.cart_expiry, json.dumps(cart))
        logger.info("Cart quantity updated", user_id=user_id, product_id=product_id, qty=quantity)
        return True

    async def get_cart(self, user_id: int) -> dict:
        """Get user cart"""
        cart_key = self._get_cart_key(user_id)
        cart_data = await self.redis.get(cart_key)
        return json.loads(cart_data) if cart_data else {}

    async def get_cart_items_count(self, user_id: int) -> int:
        """Get total items in cart"""
        cart = await self.get_cart(user_id)
        return sum(item["quantity"] for item in cart.values())

    async def get_cart_total(self, user_id: int) -> float:
        """Get cart total price"""
        cart = await self.get_cart(user_id)
        return sum(item["price"] * item["quantity"] for item in cart.values())

    async def clear_cart(self, user_id: int) -> bool:
        """Clear user cart"""
        cart_key = self._get_cart_key(user_id)
        result = await self.redis.delete(cart_key)
        logger.info("Cart cleared", user_id=user_id)
        return result > 0

    async def get_cart_details(self, user_id: int) -> dict:
        """Get detailed cart information"""
        cart = await self.get_cart(user_id)
        items_count = await self.get_cart_items_count(user_id)
        total = await self.get_cart_total(user_id)

        return {
            "items": cart,
            "items_count": items_count,
            "total": total,
            "is_empty": len(cart) == 0,
        }
