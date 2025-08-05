# 📖 Инструкции по установке и настройке

## 🚀 Быстрый старт (демо-версия)

### Шаг 1: Клонирование и подготовка
```bash
# Клонируйте репозиторий или скачайте файлы
git clone <repository_url>
cd telegram-odann-bot

# Или если у вас есть файлы проекта:
cd /path/to/odann-bot
```

### Шаг 2: Установка Python зависимостей
```bash
# Создание виртуального окружения (рекомендуется)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка базовых зависимостей
pip install python-dotenv
```

### Шаг 3: Запуск демо-версии
```bash
python demo.py
```

## 🤖 Полная настройка для Telegram

### Шаг 1: Создание Telegram бота

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Введите имя бота (например: "Odann Bot")
   - Введите username бота (например: "odann_anime_bot")
4. Сохраните полученный токен

### Шаг 2: Настройка окружения

1. Скопируйте файл `.env`:
```bash
cp .env .env.local
```

2. Отредактируйте `.env.local` и замените токен:
```
BOT_TOKEN=1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
```

### Шаг 3: Установка полных зависимостей

```bash
# Активируйте виртуальное окружение
source venv/bin/activate

# Установите все зависимости
pip install -r requirements.txt
```

**Примечание**: Установка `torch` и `transformers` может занять время и требует много места (~2-3 ГБ).

### Шаг 4: Запуск бота

```bash
# Используйте launcher
python run.py

# Или напрямую
python bot.py
```

## 🔧 Решение проблем

### Python версия
Убедитесь, что используете Python 3.8 или новее:
```bash
python3 --version
```

### Права доступа (Linux/Mac)
Если возникают проблемы с правами:
```bash
chmod +x run.py demo.py
```

### Проблемы с зависимостями

#### На Ubuntu/Debian:
```bash
sudo apt update
sudo apt install python3-venv python3-pip python3-dev
```

#### На CentOS/RHEL:
```bash
sudo yum install python3-venv python3-pip python3-devel
```

#### На Windows:
Установите Python с [python.org](https://python.org) с включенной опцией "Add to PATH"

### Ошибки установки torch/transformers

Если установка `torch` и `transformers` не удается:

1. Используйте демо-версию: `python demo.py`
2. Или закомментируйте импорты в `ai_model.py` (уже сделано)
3. Или установите только CPU версию:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers
```

### Ошибки базы данных

Если возникают проблемы с SQLite:
```bash
# Удалите файл базы данных для пересоздания
rm odann_bot.db

# Запустите снова
python demo.py
```

## 📱 Настройка для продакшена

### Systemd сервис (Linux)

1. Создайте файл сервиса:
```bash
sudo nano /etc/systemd/system/odann-bot.service
```

2. Добавьте содержимое:
```ini
[Unit]
Description=Odann Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/telegram-odann-bot
Environment=PATH=/path/to/telegram-odann-bot/venv/bin
ExecStart=/path/to/telegram-odann-bot/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Активируйте сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable odann-bot
sudo systemctl start odann-bot
```

### Docker (опционально)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "bot.py"]
```

### Переменные окружения для продакшена

Создайте `.env.production`:
```bash
BOT_TOKEN=your_production_token
DATABASE_PATH=/data/odann_bot.db
DEBUG=false
```

## 🧪 Тестирование

### Проверка модулей
```bash
python3 -c "
from database import db
from ai_model import ai
from config import *
print('✅ Все модули загружены успешно')
"
```

### Тест AI ответов
```bash
python3 -c "
from ai_model import ai
print('🌸 Оданн:', ai.generate_response('привет', [], None))
"
```

## 📞 Поддержка

Если ничего не помогает:

1. Проверьте логи ошибок
2. Убедитесь в правильности токена
3. Попробуйте демо-версию: `python demo.py`
4. Создайте Issue в репозитории с полным описанием ошибки

## 📊 Требования к системе

- **Минимальные**: Python 3.8, 100 МБ свободного места
- **Для полной версии**: Python 3.8+, 3 ГБ свободного места, 2 ГБ RAM
- **Рекомендуемые**: Python 3.10+, 5 ГБ свободного места, 4 ГБ RAM