import asyncio
from src.core.database import AsyncSessionLocal, init_db
from src.models.product import Product

async def add_sample_products():
    await init_db()
    async with AsyncSessionLocal() as session:
        products = [
            Product(name="iPhone 15", description="128GB, Black", price=799.99, stock=10),
            Product(name="Samsung Galaxy S24", description="256GB", price=899.99, stock=8),
            Product(name="MacBook Air M3", description="13 inch, 16GB", price=1299.99, stock=5),
        ]
        for p in products:
            session.add(p)
        await session.commit()
    print("✅ Тестовые товары добавлены!")

asyncio.run(add_sample_products())
