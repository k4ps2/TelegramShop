FROM python:3.12-slim

WORKDIR /app

# Установка Poetry
RUN pip install poetry && \
    poetry config virtualenvs.create false

# Копируем зависимости
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --no-dev

# Копируем исходники
COPY src/ ./src/

# Создаём директории для логов и alembic
RUN mkdir -p /app/alembic

CMD ["python", "-m", "src.bot.main"]
