#!/usr/bin/env python3
"""
Launcher для Telegram бота Оданн
"""

import os
import sys

def check_requirements():
    """Проверка наличия необходимых файлов и настроек"""
    
    # Проверяем наличие .env файла с токеном
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("📝 Создайте файл .env и укажите в нем токен бота:")
        print("   BOT_TOKEN=ваш_токен_бота")
        return False
    
    # Проверяем наличие токена в .env
    with open('.env', 'r') as f:
        content = f.read()
        if 'YOUR_BOT_TOKEN_HERE' in content:
            print("❌ Необходимо заменить YOUR_BOT_TOKEN_HERE на реальный токен бота!")
            print("📝 Получите токен у @BotFather в Telegram")
            return False
    
    return True

def main():
    """Главная функция запуска"""
    print("🌸 Запуск Telegram бота Оданн...")
    
    # Проверяем требования
    if not check_requirements():
        print("❌ Проверьте настройки и попробуйте снова")
        sys.exit(1)
    
    # Запускаем бота
    try:
        from bot import main as bot_main
        bot_main()
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("📦 Установите зависимости: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")

if __name__ == '__main__':
    main()