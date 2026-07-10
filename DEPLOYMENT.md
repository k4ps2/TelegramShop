# Deployment Guide

Complete guide for deploying the Online Shop Telegram Bot to production.

## 📋 Pre-Deployment Checklist

- [ ] Telegram Bot Token obtained from @BotFather
- [ ] PostgreSQL database configured
- [ ] Redis instance available
- [ ] Docker and Docker Compose installed (v20.10+)
- [ ] Environment variables properly configured
- [ ] Database migrations tested
- [ ] Admin user IDs configured
- [ ] SSL certificates ready (if using HTTPS proxy)

## 🔧 Configuration

### 1. Create Production .env File

```bash
# .env (production)
BOT_TOKEN=YOUR_PRODUCTION_BOT_TOKEN_HERE

# Admin IDs (comma-separated)
ADMIN_IDS=123456789,987654321

# Database Configuration
DB_HOST=db
DB_PORT=5432
DB_USER=shopbot
DB_PASSWORD=STRONG_PASSWORD_HERE
DB_NAME=shop_bot_db

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Bot Settings
ITEMS_PER_PAGE=5
DEFAULT_LANGUAGE=en
```

**⚠️ Security Notes:**
- Use strong passwords (min. 32 chars)
- Never commit `.env` to version control
- Use secrets management for production
- Rotate passwords regularly

### 2. Update docker-compose.yml

For production, ensure:
- Resource limits are set
- Health checks are enabled
- Restart policies are correct
- Logging is configured
- Networks are isolated

## 🚀 Deployment Methods

### Method 1: Docker Compose (Recommended)

#### Setup

```bash
# 1. Clone and navigate to project
git clone <your-repo>
cd freelance_shop_bot

# 2. Create .env file with production values
cp .env.example .env
nano .env  # Edit with production settings

# 3. Build images
docker-compose build

# 4. Start services
docker-compose up -d

# 5. Verify status
docker-compose ps
```

#### Monitor

```bash
# View logs
docker-compose logs -f bot

# Check database
docker-compose exec db psql -U shopbot -d shop_bot_db

# Check Redis
docker-compose exec redis redis-cli ping

# Check health
docker-compose ps  # Should show all services as "Up"
```

#### Maintenance

```bash
# Update code
git pull origin main
docker-compose build

# Apply migrations
docker-compose run bot poetry run alembic upgrade head

# Restart services
docker-compose restart

# Shutdown
docker-compose down

# Full cleanup (WARNING: deletes volumes!)
docker-compose down -v
```

### Method 2: Kubernetes (Advanced)

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shop-bot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: shop-bot
  template:
    metadata:
      labels:
        app: shop-bot
    spec:
      containers:
      - name: bot
        image: your-registry/shop-bot:latest
        envFrom:
        - configMapRef:
            name: bot-config
        - secretRef:
            name: bot-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - import sys; sys.exit(0)
          initialDelaySeconds: 30
          periodSeconds: 30
```

Deploy:
```bash
kubectl apply -f k8s/
kubectl get pods
kubectl logs pod/shop-bot-xxxx -f
```

## 🔐 Security Hardening

### 1. Database Security

```bash
# Use strong password
# Restrict database user permissions
psql -U postgres

CREATE USER shopbot WITH PASSWORD 'STRONG_PASSWORD';
CREATE DATABASE shop_bot_db OWNER shopbot;
GRANT CONNECT ON DATABASE shop_bot_db TO shopbot;
```

### 2. Redis Security

```bash
# Enable authentication in docker-compose
redis:
  command: redis-server --requirepass YOUR_PASSWORD

# In bot .env
REDIS_URL=redis://:YOUR_PASSWORD@redis:6379
```

### 3. Bot Token Protection

```bash
# Use environment variables only
# Never hardcode tokens
# Rotate tokens periodically if compromised

# In production, use:
# - AWS Secrets Manager
# - HashiCorp Vault
# - Google Cloud Secret Manager
```

### 4. Network Isolation

```yaml
# docker-compose.yml
networks:
  shop_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

services:
  bot:
    networks:
      - shop_network
  db:
    networks:
      - shop_network
  redis:
    networks:
      - shop_network
```

## 📊 Monitoring & Alerting

### Docker Stats

```bash
# Real-time resource usage
docker stats shop_bot_app shop_bot_db shop_bot_redis

# Historical logs
docker-compose logs --tail=100 bot | grep "error"
```

### Structured Logs

```bash
# Filter by log level
docker-compose logs bot | grep "ERROR"

# Filter by operation
docker-compose logs bot | grep "Order created"

# Export logs
docker-compose logs bot > logs.txt
```

### Health Checks

```bash
# Bot responds
curl http://localhost/health || echo "Bot down"

# Database connected
docker-compose exec db psql -U shopbot -d shop_bot_db -c "SELECT 1"

# Redis working
docker-compose exec redis redis-cli PING
```

### Alert Rules

Set up alerts for:
- Bot stops responding
- Database connection errors
- Redis memory usage > 80%
- Disk space < 5%
- Order processing delays > 5min

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t shop-bot:${{ github.sha }} .

      - name: Run tests
        run: docker run shop-bot:${{ github.sha }} pytest

      - name: Push to registry
        run: |
          docker tag shop-bot:${{ github.sha }} your-registry/shop-bot:latest
          docker push your-registry/shop-bot:latest

      - name: Deploy to production
        run: |
          ssh user@production-server << 'EOF'
          cd /app/shop-bot
          docker-compose pull
          docker-compose up -d
          EOF
```

## 🆘 Troubleshooting

### Bot Not Starting

```bash
# Check logs
docker-compose logs bot | tail -50

# Common issues:
# 1. Invalid BOT_TOKEN
docker-compose exec bot python -c "from src.bot.config import settings; print(settings.BOT_TOKEN)"

# 2. Database not ready
docker-compose exec bot poetry run alembic current

# 3. Redis not available
docker-compose exec bot redis-cli -h redis ping
```

### Database Migration Failed

```bash
# Rollback
docker-compose run bot poetry run alembic downgrade -1

# Check current state
docker-compose run bot poetry run alembic current

# Reapply
docker-compose run bot poetry run alembic upgrade head
```

### Disk Space Issues

```bash
# Check usage
docker system df

# Clean unused images
docker image prune -a

# Clean unused volumes
docker volume prune

# Cleanup logs
docker-compose logs --tail=0 bot > /dev/null
truncate -s 0 /var/lib/docker/containers/*/*-json.log
```

## 📈 Scaling

### Horizontal Scaling (Multiple Instances)

For high-traffic scenarios:

```yaml
# docker-compose.yml
version: '3.9'
services:
  bot:
    deploy:
      replicas: 3  # Multiple instances
    environment:
      - WORKER_ID=${HOSTNAME}
    depends_on:
      - db
      - redis
```

### Load Balancing

Use Redis for job queue:

```python
# Distributed task processing
import redis
from rq import Worker, Queue

redis_conn = redis.from_url(settings.redis_url)
queue = Queue(connection=redis_conn)

# Enqueue tasks
job = queue.enqueue('process_order', order_id)

# Workers process
worker = Worker([queue], connection=redis_conn)
worker.work()
```

## 💾 Backup & Recovery

### Database Backups

```bash
# Automated daily backup
# Add to crontab
0 2 * * * docker-compose exec db pg_dump -U shopbot shop_bot_db > /backups/shop_bot_db_$(date +\%Y\%m\%d).sql

# Manual backup
docker-compose exec db pg_dump -U shopbot shop_bot_db > backup.sql

# Restore
docker-compose exec db psql -U shopbot shop_bot_db < backup.sql
```

### Redis Persistence

Redis automatically saves with `--appendonly yes`:

```bash
# Check persistence
docker-compose exec redis redis-cli BGSAVE

# View AOF file
docker-compose logs redis | grep "AOF"
```

## 🔍 Logging & Monitoring

### Centralized Logging

```yaml
# Optional: Send logs to ELK Stack
# Install beats
docker-compose exec bot pip install filebeat

# Configure
filebeat -c filebeat.yml
```

### Performance Metrics

```bash
# Monitor bot performance
docker stats --no-stream
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

## 📝 Post-Deployment Tasks

- [ ] Test all bot features
- [ ] Verify database connectivity
- [ ] Test Redis caching
- [ ] Add sample products
- [ ] Test admin functions
- [ ] Verify logging
- [ ] Set up monitoring alerts
- [ ] Document production URLs
- [ ] Create runbooks for common operations
- [ ] Train team on operations

## 🎯 Performance Optimization

### Database

```python
# Add indexes for frequently queried fields
# Already done in models with Index()

# Use connection pooling
# Already configured with AsyncSessionLocal
```

### Redis

```python
# Use Redis pipelining
pipe = redis.pipeline()
for i in range(1000):
    pipe.set(f'key:{i}', f'value:{i}')
pipe.execute()
```

### API Rate Limiting

```python
# Implement rate limiting
from aiogram_rates import RateLimiter

rate_limiter = RateLimiter(max_requests=10, window=60)

@dp.message(rate_limiter)
async def handle_message(message: Message):
    pass
```

## 📞 Support & Incidents

### On-Call Runbook

1. **Bot not responding**
   - Check Docker status: `docker-compose ps`
   - View logs: `docker-compose logs -f bot`
   - Restart: `docker-compose restart bot`

2. **Database error**
   - Check logs: `docker-compose logs db`
   - Verify connection: `docker-compose exec db psql -U shopbot -d shop_bot_db -c "SELECT 1"`
   - Restart database: `docker-compose restart db`

3. **Redis error**
   - Check status: `docker-compose exec redis redis-cli ping`
   - View memory: `docker-compose exec redis redis-cli INFO memory`
   - Restart: `docker-compose restart redis`

## ✅ Conclusion

Your bot is now production-ready! Remember to:
- Keep dependencies updated
- Monitor logs regularly
- Backup data periodically
- Update documentation
- Train your team
