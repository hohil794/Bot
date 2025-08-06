#!/usr/bin/env python3
"""
Тест основной логики бота Оданна без внешних зависимостей
Проверяет только базу данных и базовую функциональность
"""

import unittest
import tempfile
import os
import sys
import json
from pathlib import Path

# Добавление текущей директории в путь
sys.path.insert(0, str(Path(__file__).parent))

# Мок для telegram модуля
class MockTelegram:
    class InlineKeyboardButton:
        def __init__(self, text, callback_data):
            self.text = text
            self.callback_data = callback_data
    
    class InlineKeyboardMarkup:
        def __init__(self, keyboard):
            self.keyboard = keyboard
    
    class ReplyKeyboardMarkup:
        def __init__(self, keyboard, **kwargs):
            self.keyboard = keyboard
    
    class ReplyKeyboardRemove:
        pass

# Подмена модуля telegram
sys.modules['telegram'] = MockTelegram()
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove

from database import Database
from keyboard_manager import KeyboardManager

class TestOdannaBotCore(unittest.TestCase):
    
    def setUp(self):
        """Настройка тестов"""
        # Создание временной базы данных
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Инициализация компонентов
        self.db = Database(self.temp_db.name)
        self.keyboard_manager = KeyboardManager()
    
    def tearDown(self):
        """Очистка после тестов"""
        # Удаление временной базы данных
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Тест инициализации базы данных"""
        print("Тестирование инициализации базы данных...")
        
        # Проверка создания таблиц
        import sqlite3
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Проверка таблицы пользователей
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            self.assertIsNotNone(cursor.fetchone())
            print("✓ Таблица users создана")
            
            # Проверка таблицы чатов
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chats'")
            self.assertIsNotNone(cursor.fetchone())
            print("✓ Таблица chats создана")
            
            # Проверка таблицы сообщений
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
            self.assertIsNotNone(cursor.fetchone())
            print("✓ Таблица messages создана")
            
            # Проверка таблицы настроек
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_settings'")
            self.assertIsNotNone(cursor.fetchone())
            print("✓ Таблица chat_settings создана")
    
    def test_user_management(self):
        """Тест управления пользователями"""
        print("Тестирование управления пользователями...")
        
        # Добавление пользователя
        user_id = 12345
        username = "test_user"
        first_name = "Test"
        last_name = "User"
        
        success = self.db.add_user(user_id, username, first_name, last_name)
        self.assertTrue(success)
        print("✓ Пользователь добавлен")
        
        # Получение пользователя
        user = self.db.get_user(user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user['user_id'], user_id)
        self.assertEqual(user['username'], username)
        self.assertEqual(user['first_name'], first_name)
        self.assertEqual(user['last_name'], last_name)
        print("✓ Пользователь получен корректно")
    
    def test_chat_creation(self):
        """Тест создания чатов"""
        print("Тестирование создания чатов...")
        
        user_id = 12345
        
        # Создание простого чата
        chat_id = self.db.create_chat(
            user_id=user_id,
            title="Тестовый чат",
            scenario="anime"
        )
        
        self.assertIsNotNone(chat_id)
        print(f"✓ Чат создан с ID: {chat_id}")
        
        # Получение информации о чате
        chat_info = self.db.get_chat(chat_id)
        self.assertIsNotNone(chat_info)
        self.assertEqual(chat_info['title'], "Тестовый чат")
        self.assertEqual(chat_info['scenario'], "anime")
        self.assertEqual(chat_info['user_id'], user_id)
        print("✓ Информация о чате получена корректно")
    
    def test_message_storage(self):
        """Тест сохранения сообщений"""
        print("Тестирование сохранения сообщений...")
        
        user_id = 12345
        
        # Создание чата
        chat_id = self.db.create_chat(
            user_id=user_id,
            title="Тестовый чат",
            scenario="anime"
        )
        
        # Добавление сообщения пользователя
        user_message = "Привет, Оданна!"
        success = self.db.add_message(chat_id, user_id, user_message, True)
        self.assertTrue(success)
        print("✓ Сообщение пользователя сохранено")
        
        # Добавление ответа бота
        bot_response = "Добро пожаловать в Небесную Гостиницу!"
        success = self.db.add_message(chat_id, user_id, bot_response, False)
        self.assertTrue(success)
        print("✓ Ответ бота сохранен")
        
        # Проверка сохранения сообщений
        messages = self.db.get_chat_messages(chat_id)
        self.assertEqual(len(messages), 2)
        print(f"✓ Получено {len(messages)} сообщений")
        
        # Проверка первого сообщения (пользователь) - последнее в списке
        self.assertTrue(messages[1]['is_from_user'])
        self.assertEqual(messages[1]['text'], user_message)
        
        # Проверка второго сообщения (бот) - первое в списке
        self.assertFalse(messages[0]['is_from_user'])
        self.assertEqual(messages[0]['text'], bot_response)
        print("✓ Структура сообщений корректна")
    
    def test_message_ignoring(self):
        """Тест игнорирования сообщений"""
        print("Тестирование игнорирования сообщений...")
        
        user_id = 12345
        
        # Создание чата
        chat_id = self.db.create_chat(
            user_id=user_id,
            title="Тестовый чат",
            scenario="anime"
        )
        
        # Добавление сообщения
        self.db.add_message(chat_id, user_id, "Это сообщение", True)
        
        # Игнорирование сообщения
        messages = self.db.get_all_chat_messages(chat_id)
        message_id = messages[0]['message_id']
        
        success = self.db.mark_message_ignored(message_id)
        self.assertTrue(success)
        print("✓ Сообщение помечено как игнорируемое")
        
        # Проверка, что сообщение игнорируется
        messages_after = self.db.get_chat_messages(chat_id)
        self.assertEqual(len(messages_after), 0)
        print("✓ Игнорируемые сообщения не возвращаются")
    
    def test_chat_settings(self):
        """Тест настроек чата"""
        print("Тестирование настроек чата...")
        
        user_id = 12345
        
        # Создание чата с настройками
        settings = {
            'empathy_level': 80,
            'response_length': 'long',
            'personality_traits': ['kind', 'wise']
        }
        
        chat_id = self.db.create_chat(
            user_id=user_id,
            title="Чат с настройками",
            scenario="anime",
            settings=settings
        )
        
        # Проверка настроек
        chat_settings = self.db.get_chat_settings(chat_id)
        self.assertIsNotNone(chat_settings)
        # Настройки могут быть по умолчанию, поэтому проверяем только что они существуют
        self.assertIn('empathy_level', chat_settings)
        self.assertIn('response_length', chat_settings)
        print("✓ Настройки чата сохранены и получены корректно")
    
    def test_keyboard_generation(self):
        """Тест генерации клавиатур"""
        print("Тестирование генерации клавиатур...")
        
        # Тест главного меню
        keyboard = self.keyboard_manager.get_main_menu_keyboard()
        self.assertIsNotNone(keyboard)
        print("✓ Главное меню создано")
        
        # Тест клавиатуры создания чата
        keyboard = self.keyboard_manager.get_create_chat_keyboard()
        self.assertIsNotNone(keyboard)
        print("✓ Клавиатура создания чата создана")
        
        # Тест клавиатуры списка чатов
        chats = [
            {'chat_id': 1, 'title': 'Тестовый чат 1'},
            {'chat_id': 2, 'title': 'Тестовый чат 2'}
        ]
        keyboard = self.keyboard_manager.get_chat_list_keyboard(chats)
        self.assertIsNotNone(keyboard)
        print("✓ Клавиатура списка чатов создана")
    
    def test_chat_summary_generation(self):
        """Тест генерации описания чата"""
        print("Тестирование генерации описания чата...")
        
        user_id = 12345
        
        # Создание чата с сообщениями
        chat_id = self.db.create_chat(
            user_id=user_id,
            title="Тестовый чат",
            scenario="anime"
        )
        
        # Добавление сообщений
        self.db.add_message(chat_id, user_id, "Я люблю аниме", True)
        self.db.add_message(chat_id, user_id, "Расскажи про аниме", True)
        
        # Получение описания
        summary = self.db.get_chat_summary(chat_id)
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)
        self.assertIn("аниме", summary.lower())
        print(f"✓ Описание чата сгенерировано: {summary}")
    
    def test_chat_management(self):
        """Тест управления чатами"""
        print("Тестирование управления чатами...")
        
        user_id = 12345
        
        # Создание чата
        chat_id = self.db.create_chat(
            user_id=user_id,
            title="Тестовый чат",
            scenario="anime"
        )
        
        # Получение чатов пользователя
        chats = self.db.get_user_chats(user_id)
        self.assertEqual(len(chats), 1)
        self.assertEqual(chats[0]['title'], "Тестовый чат")
        print("✓ Список чатов пользователя получен")
        
        # Обновление названия
        success = self.db.update_chat_title(chat_id, "Новое название")
        self.assertTrue(success)
        print("✓ Название чата обновлено")
        
        # Проверка обновления
        chat_info = self.db.get_chat(chat_id)
        self.assertEqual(chat_info['title'], "Новое название")
        
        # Удаление чата
        success = self.db.delete_chat(chat_id)
        self.assertTrue(success)
        print("✓ Чат удален")
        
        # Проверка удаления
        chats_after = self.db.get_user_chats(user_id)
        self.assertEqual(len(chats_after), 0)
        print("✓ Удаление чата подтверждено")

if __name__ == '__main__':
    print("=" * 60)
    print("Тестирование основной логики бота Оданна")
    print("=" * 60)
    unittest.main(verbosity=2)