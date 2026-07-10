# Quick Start Guide

Get the bot running in 5 minutes!

## ⚡ 5-Minute Setup

### Prerequisites
- Docker & Docker Compose installed
- Telegram Bot Token (from @BotFather)
- Git

### Steps

1. **Clone the repository**
```bash
git clone <your-repo>
cd freelance_shop_bot
```

2. **Create .env file**
```bash
cp .env.example .env
```

3. **Edit .env with your bot token**
```bash
# Linux/Mac
nano .env

# Windows
notepad .env
```

Update:
```
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
ADMIN_IDS=YOUR_TELEGRAM_ID
```

Find your Telegram ID: https://t.me/userinfobot

4. **Start the bot**
```bash
docker-compose up -d
```

5. **Verify it's running**
```bash
docker-compose logs -f bot

# Should see: "Bot is starting..."
```

6. **Test the bot**
- Open Telegram
- Find your bot
- Send `/start`
- You should see the main menu! 🎉

## 📱 Using the Bot

### User Features
- `/start` - Main menu
- `/help` - Help info
- 📚 Browse catalog
- 🛒 Add items to cart
- 📦 View orders
- 🌍 Switch language

### Admin Features (if you're in ADMIN_IDS)
- `/admin` - Admin panel
- Add products
- View orders
- Check statistics

## ➕ Add Your First Product

### Option A: Via Bot (Easiest)
1. Send `/admin`
2. Click "➕ Add Product"
3. Enter product details:
   - Name (Russian)
   - Name (English)
   - Description (Russian)
   - Description (English)
   - Price
   - Stock quantity

### Option B: Via Python Script
```python
# Save as add_products.py
import asyncio
from src.core.database import AsyncSessionLocal
from src.services.product import ProductService

async def main():
    async with AsyncSessionLocal() as session:
        service = ProductService(session)

        await service.create_product(
            name="iPhone 15",
            name_en="iPhone 15",
            description="Последний iPhone",
            description_en="Latest iPhone",
            price=999.99,
            stock=10
        )
        print("✅ Product added!")

asyncio.run(main())
```

Then run:
```bash
docker-compose exec bot python add_products.py
```

## 🔧 Common Commands

```bash
# View logs
docker-compose logs -f bot

# Stop bot
docker-compose down

# Restart bot
docker-compose restart bot

# Access database
docker-compose exec db psql -U postgres -d shop_bot

# Access Redis
docker-compose exec redis redis-cli
```

## 🐛 Troubleshooting

### Bot doesn't start
```bash
# Check logs
docker-compose logs bot

# Verify BOT_TOKEN is correct
grep BOT_TOKEN .env

# Restart
docker-compose restart bot
```

### Can't add products
```bash
# Check database
docker-compose exec db psql -U postgres -d shop_bot -c "SELECT * FROM products;"

# View app logs
docker-compose logs bot | grep -i "product"
```

### Database connection error
```bash
# Restart database
docker-compose restart db

# Check status
docker-compose ps
```

## 📚 Next Steps

1. Read full [README.md](README.md) for complete documentation
2. Check [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
3. Explore the code in `src/` directory
4. Customize handlers in `src/bot/handlers/`
5. Add more languages in `src/bot/locales/`

## 🎓 Learning Resources

- Aiogram 3 Docs: https://docs.aiogram.dev/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Redis: https://redis.io/documentation
- PostgreSQL: https://www.postgresql.org/docs/

## 💬 Need Help?

- Check logs: `docker-compose logs bot`
- Read troubleshooting in README.md
- Check existing issues on GitHub

## ✅ Verification Checklist

After 5-minute setup, verify:
- [ ] Docker containers are running (`docker-compose ps`)
- [ ] Bot responds to `/start`
- [ ] Main menu appears
- [ ] Can browse catalog
- [ ] Can add items to cart
- [ ] Admin can add products (`/admin`)
- [ ] Database is working
- [ ] Redis is working

All green? Congratulations! 🎉 Your bot is ready!

## 🚀 What's Next?

- **Customize**: Edit keyboards, messages, colors
- **Scale**: Add more products, features
- **Deploy**: Move to production (see DEPLOYMENT.md)
- **Monitor**: Set up logging and alerts
- **Extend**: Add payment integration, notifications, etc.

Happy coding! 💻
