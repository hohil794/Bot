# Базовый образ Python
FROM python:3.11-slim

# Метаданные
LABEL maintainer="Odanna Bot"
LABEL description="Telegram-бот Оданна из аниме 'Повар небесной гостиницы'"
LABEL version="1.0"

# Рабочая директория
WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY odanna_bot.py .
COPY .env.example .

# Создание директорий для данных и логов
RUN mkdir -p /app/data /app/logs

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Открываем порт
EXPOSE 8080

# Проверка здоровья контейнера
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import sqlite3; sqlite3.connect('/app/data/odanna_bot.db').close()" || exit 1

# Запуск бота
CMD ["python", "odanna_bot.py"]