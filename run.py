#!/usr/bin/env python3
"""
Скрипт запуска бота Оданна
Обеспечивает безопасный запуск с обработкой ошибок и логированием
"""

import os
import sys
import logging
import signal
import time
from pathlib import Path

# Добавление текущей директории в путь
sys.path.insert(0, str(Path(__file__).parent))

try:
    from odanna_bot import OdannaBot
    from config import LOGGING_CONFIG
except ImportError as e:
    print(f"Ошибка импорта модулей: {e}")
    print("Убедитесь, что все файлы находятся в правильных местах")
    sys.exit(1)

def setup_logging():
    """Настройка логирования"""
    log_format = LOGGING_CONFIG["format"]
    log_level = getattr(logging, LOGGING_CONFIG["level"])
    log_file = LOGGING_CONFIG["filename"]
    
    # Создание директории для логов если её нет
    log_path = Path(log_file)
    log_path.parent.mkdir(exist_ok=True)
    
    # Настройка логирования
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def check_environment():
    """Проверка окружения"""
    logger = logging.getLogger(__name__)
    
    # Проверка токена бота
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token or bot_token == "YOUR_BOT_TOKEN_HERE":
        logger.error("Не установлен токен бота. Установите переменную BOT_TOKEN")
        return False
    
    # Проверка ID администратора
    admin_id = os.getenv("ADMIN_ID")
    if not admin_id:
        logger.warning("Не установлен ADMIN_ID. Административные функции недоступны")
    
    # Проверка Python версии
    if sys.version_info < (3, 8):
        logger.error("Требуется Python 3.8 или выше")
        return False
    
    logger.info("Окружение проверено успешно")
    return True

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger = logging.getLogger(__name__)
    logger.info(f"Получен сигнал {signum}. Завершение работы...")
    sys.exit(0)

def main():
    """Главная функция"""
    # Настройка логирования
    logger = setup_logging()
    
    logger.info("=" * 50)
    logger.info("Запуск бота Оданна - Небесная Гостиница")
    logger.info("=" * 50)
    
    # Проверка окружения
    if not check_environment():
        logger.error("Ошибка проверки окружения. Завершение работы.")
        sys.exit(1)
    
    # Настройка обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Создание и запуск бота
        logger.info("Инициализация бота...")
        bot = OdannaBot()
        
        logger.info("Бот успешно инициализирован")
        logger.info("Запуск polling...")
        
        # Запуск бота
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания. Завершение работы...")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        logger.error("Детали ошибки:", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Бот завершил работу")

if __name__ == "__main__":
    main()