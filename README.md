# Online Shop Telegram Bot

A production-ready Telegram shop bot built with **aiogram 3**, **SQLAlchemy 2.0**, **PostgreSQL**, and **Redis**. Features full e-commerce functionality with multi-language support, admin panel, order management, and more.

## 🚀 Features

### User Features
- 📚 **Product Catalog** - Browse products with pagination
- 🔍 **Search** - Search products by name and description
- 🛒 **Shopping Cart** - Add/remove items, manage quantities (Redis-backed)
- 📦 **Orders** - Create orders from cart, track order status
- 🌍 **Multi-language** - Support for English and Russian
- ⚙️ **Settings** - Language preferences per user

### Admin Features
- ➕ **Product Management** - Add new products with bilingual descriptions
- 📋 **Order Management** - View all orders, change order status
- 📊 **Statistics** - Real-time stats on users, products, and orders
- 👥 **User Analytics** - Track active users and user growth

### Technical Features
- ✅ **Type-safe** - Full Python type hints
- 🗄️ **SQLAlchemy 2.0** - Modern async ORM with relationships
- ⚡ **Redis** - Fast cart storage and caching
- 🐳 **Docker** - Production-ready containerization
- 📝 **Structured Logging** - With structlog
- 🔄 **Alembic** - Database migrations
- 🛡️ **Error Handling** - Comprehensive error management

## 🏗️ Project Structure

```
freelance_shop_bot/
├── src/
│   ├── bot/
│   │   ├── handlers/           # Request handlers (user, shop, cart, order, admin)
│   │   ├── keyboards/          # Inline and reply keyboards
│   │   ├── locales/            # i18n JSON files (en.json, ru.json)
│   │   ├── middlewares/        # Aiogram middlewares
│   │   ├── config.py           # Settings with pydantic
│   │   ├── i18n.py             # Internationalization
│   │   └── main.py             # Bot entry point
│   ├── core/
│   │   ├── database.py         # SQLAlchemy setup
│   │   └── logging.py          # Structured logging
│   ├── models/                 # SQLAlchemy models
│   │   ├── user.py
│   │   ├── product.py
│   │   └── order.py
│   ├── repositories/           # Data access layer
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── product.py
│   │   └── order.py
│   └── services/               # Business logic layer
│       ├── user.py
│       ├── product.py
│       ├── cart.py
│       └── order.py
├── alembic/                    # Database migrations
├── Dockerfile                  # Multi-stage Docker build
├── docker-compose.yml          # Production docker-compose
├── pyproject.toml              # Python dependencies
└── README.md                   # This file
```

## 📋 Architecture

The bot follows a **3-layer architecture**:

### 1. **Handlers Layer**
- Located in `src/bot/handlers/`
- Receive user input from Telegram
- Call services for business logic
- Return responses to users

### 2. **Services Layer**
- Located in `src/services/`
- Contain business logic
- Use repositories for data access
- Handle transactions and validation

### 3. **Repository Layer**
- Located in `src/repositories/`
- Handle all database operations
- Provide clean API for data access
- Implement query logic

### Data Flow
```
User Input → Handler → Service → Repository → Database
Response ← Handler ← Service ← Repository ← Database
```

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.12+
- Docker & Docker Compose (for containerized setup)
- PostgreSQL (if running locally)
- Redis (if running locally)

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone <your-repo>
cd freelance_shop_bot

# Create .env file
cp .env.example .env

# Edit .env with your settings
nano .env  # Add BOT_TOKEN, ADMIN_IDS, etc.

# Start containers
docker-compose up -d

# Check logs
docker-compose logs -f bot
```

### Option 2: Local Setup

```bash
# Install Poetry
pip install poetry

# Install dependencies
poetry install

# Create .env file
cp .env.example .env

# Start PostgreSQL and Redis (using Docker or locally installed)
docker run -d -p 5432:5432 \
  -e POSTGRES_DB=shop_bot \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  postgres:16-alpine

docker run -d -p 6379:6379 redis:7-alpine

# Run database migrations
poetry run alembic upgrade head

# Start bot
poetry run python -m src.bot.main
```

## 🗄️ Database Migrations

### Create a new migration
```bash
# After changing models in src/models/
poetry run alembic revision --autogenerate -m "description"

# Review the migration file in alembic/versions/
nano alembic/versions/<new_migration>.py

# Apply migrations
poetry run alembic upgrade head
```

### Rollback
```bash
# Rollback one migration
poetry run alembic downgrade -1

# Rollback all
poetry run alembic downgrade base
```

## 📦 Adding Products

### Via Admin Panel (Telegram)
1. Send `/admin` to bot (must be in `ADMIN_IDS`)
2. Click "➕ Add Product"
3. Follow the prompts to enter:
   - Product name (Russian & English)
   - Description (Russian & English)
   - Price
   - Stock quantity

### Via add_products.py Script
```python
# Create and run add_products.py
import asyncio
from src.core.database import AsyncSessionLocal
from src.services.product import ProductService

async def add_sample_products():
    async with AsyncSessionLocal() as session:
        service = ProductService(session)

        await service.create_product(
            name="Ноутбук",
            name_en="Laptop",
            description="Мощный ноутбук для работы",
            description_en="Powerful laptop for work",
            price=999.99,
            stock=5
        )

asyncio.run(add_sample_products())
```

## 🌍 Internationalization (i18n)

Translations are stored in JSON files:
- `src/bot/locales/en.json` - English
- `src/bot/locales/ru.json` - Russian

### Adding a new translation key
1. Add to both JSON files:
```json
{
  "your_key": "Your translated text"
}
```

2. Use in handlers:
```python
from src.bot.i18n import i18n

text = i18n("your_key", language="en")
```

## 👨‍💼 Admin Panel

### Access
- Must be in `ADMIN_IDS` list in `.env`
- Command: `/admin` or button in main menu

### Features
- **Add Product** - Create new products
- **View Orders** - See all orders with status
- **Statistics** - Real-time dashboard with:
  - Total users & active users
  - Total products & low stock items
  - Order stats by status
  - Total revenue

### Order Status Management
1. View order in admin panel
2. Click on order ID
3. Select new status from buttons
4. Status updates in real-time

## 🛒 Cart System

Cart is stored in **Redis** with automatic expiry:
- Default expiry: 7 days
- Cart structure: `cart:{user_id}` → JSON of items
- Items include: product ID, quantity, price, name

### Cart Operations
```python
from src.services.cart import CartService
from redis.asyncio import from_url

redis = from_url(settings.redis_url)
cart_service = CartService(redis, session)

# Add item
await cart_service.add_to_cart(user_id, product_id, quantity)

# Get cart
cart = await cart_service.get_cart(user_id)

# Get total
total = await cart_service.get_cart_total(user_id)

# Clear cart
await cart_service.clear_cart(user_id)
```

## 📦 Order System

### Order Status Flow
```
PENDING → CONFIRMED → SHIPPED → DELIVERED
         (optional)   (optional)
   ↓
CANCELLED (at any point)
```

### Order Management
```python
from src.services.order import OrderService

async with AsyncSessionLocal() as session:
    order_service = OrderService(session, redis)

    # Create from cart
    order = await order_service.create_order_from_cart(user_id)

    # Get user's orders
    orders, total_pages = await order_service.get_user_orders(user_id, page=1)

    # Update status
    await order_service.update_order_status(order_id, OrderStatus.CONFIRMED)

    # Cancel (releases stock)
    await order_service.cancel_order(order_id)
```

## 🔧 Configuration

### Environment Variables (.env)

```
# Bot
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=shop_bot

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Bot Settings
ITEMS_PER_PAGE=5
DEFAULT_LANGUAGE=en
```

## 📊 Monitoring & Logging

Logs are structured using `structlog`:

```python
import structlog

logger = structlog.get_logger(__name__)

# Log with context
logger.info("User registered", user_id=user_id, username=username)

# Log error
logger.error("Database error", error=str(e), exc_info=e)
```

View logs:
```bash
# Docker logs
docker-compose logs -f bot

# With filtering
docker-compose logs bot | grep "error"
```

## 🧪 Testing

```bash
# Run tests
poetry run pytest

# With coverage
poetry run pytest --cov=src

# Specific test file
poetry run pytest tests/test_services.py -v
```

## 🚀 Deployment

### Docker Hub
```bash
# Build image
docker build -t your-username/shop-bot:latest .

# Push to registry
docker push your-username/shop-bot:latest

# Pull and run
docker pull your-username/shop-bot:latest
docker-compose up -d
```

### Production Checklist
- [ ] Set `BOT_TOKEN` to production token
- [ ] Update `ADMIN_IDS` with real admins
- [ ] Use strong database password
- [ ] Set `DEFAULT_LANGUAGE` correctly
- [ ] Configure proper logging/monitoring
- [ ] Set up database backups
- [ ] Use Redis persistence (`--appendonly yes`)
- [ ] Configure SSL/TLS if needed
- [ ] Set resource limits in docker-compose

## 🐛 Troubleshooting

### Bot not responding
```bash
# Check bot logs
docker-compose logs bot

# Verify BOT_TOKEN is correct
# Restart bot
docker-compose restart bot
```

### Database connection error
```bash
# Check database health
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Redis connection error
```bash
# Check Redis status
docker-compose ps redis

# Test Redis connection
redis-cli -h localhost -p 6379 ping

# Restart Redis
docker-compose restart redis
```

### Migration issues
```bash
# Check current version
poetry run alembic current

# See migration history
poetry run alembic history --oneline

# Downgrade and reapply
poetry run alembic downgrade base
poetry run alembic upgrade head
```

## 📚 API Reference

### User Service
```python
user_service = UserService(session)

# Get or create
user = await user_service.get_or_create_user(user_id, username, full_name)

# Update language
await user_service.update_user_language(user_id, "ru")

# Get stats
stats = await user_service.get_stats()
```

### Product Service
```python
product_service = ProductService(session)

# Get paginated products
products, total_pages = await product_service.get_products_paginated(page=1)

# Search
products, pages = await product_service.search_products("laptop", page=1)

# Create
product = await product_service.create_product(
    name="...", name_en="...",
    description="...", description_en="...",
    price=99.99, stock=10
)

# Reserve stock
await product_service.reserve_stock(product_id, quantity)
```

### Order Service
```python
order_service = OrderService(session, redis)

# Create from cart
order = await order_service.create_order_from_cart(user_id)

# Get orders
orders, pages = await order_service.get_user_orders(user_id, page=1)

# Update status
await order_service.update_order_status(order_id, OrderStatus.SHIPPED)

# Stats
stats = await order_service.get_stats()
```

### Cart Service
```python
cart_service = CartService(redis, session)

# Add item
await cart_service.add_to_cart(user_id, product_id, quantity=1)

# Get cart
cart = await cart_service.get_cart(user_id)

# Update quantity
await cart_service.update_quantity(user_id, product_id, new_quantity)

# Get total
total = await cart_service.get_cart_total(user_id)

# Clear
await cart_service.clear_cart(user_id)
```

## 📝 License

MIT License - feel free to use this project for learning and development.

## 👨‍💻 Author

Created as a portfolio project demonstrating modern Python backend development with async/await, microservices patterns, and production-ready code.

## 🔗 Technologies

- **Framework**: aiogram 3
- **Database**: PostgreSQL + SQLAlchemy 2.0
- **Cache**: Redis
- **ORM**: SQLAlchemy with asyncpg
- **Migrations**: Alembic
- **Config**: pydantic-settings
- **Logging**: structlog
- **Containerization**: Docker & Docker Compose
- **Type Checking**: Python 3.12+ type hints

## 💡 Future Improvements

- [ ] Payment integration (Stripe, PayPal)
- [ ] Email notifications
- [ ] Advanced analytics dashboard
- [ ] Product categories and tags
- [ ] User reviews and ratings
- [ ] Discount codes and promotions
- [ ] Inventory alerts
- [ ] Customer support chat
- [ ] Mobile app integration

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues and questions, please open an issue on GitHub.
