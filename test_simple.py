#!/usr/bin/env python3
"""
Упрощенный тест бота Оданна без тяжелых зависимостей
Проверяет основную логику без нейросети
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# Добавление текущей директории в путь
sys.path.insert(0, str(Path(__file__).parent))

# Мок для torch и transformers
class MockTorch:
    def __init__(self):
        pass

class MockTransformers:
    def __init__(self):
        pass

# Подмена модулей
sys.modules['torch'] = MockTorch()
sys.modules['transformers'] = MockTransformers()

from database import Database
from keyboard_manager import KeyboardManager

class TestOdannaBotSimple(unittest.TestCase):
    
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
        # Проверка создания таблиц
        with self.db.db_path as conn:
            cursor = conn.cursor()
            
            # Проверка таблицы пользователей
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Проверка таблицы чатов
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chats'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Проверка таблицы сообщений
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
            self.assertIsNotNone(cursor.fetchone())
    
    def test_user_management(self):
        """Тест управления пользователями"""
        # Добавление пользователя
        user_id = 12345
        username = "test_user"
        first_name = "Test"
        last_name = "User"
        
        success = self.db.add_user(user_id, username, first_name, last_name)
        self.assertTrue(success)
        
        # Получение пользователя
        user = self.db.get_user(user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user['user_id'], user_id)
        self.assertEqual(user['username'], username)
        self.assertEqual(user['first_name'], first_name)
        self.assertEqual(user['last_name'], last_name)
    
    def test_chat_creation(self):
        """Тест создания чатов"""
        user_id = 12345
        
        # Создание простого чата
        chat_id = self.db.create_chat(
            user_id=user_id,
            title="Тестовый чат",
            scenario="anime"
        )
        
        self.assertIsNotNone(chat_id)
        
        # Получение информации о чате
        chat_info = self.db.get_chat(chat_id)
        self.assertIsNotNone(chat_info)
        self.assertEqual(chat_info['title'], "Тестовый чат")
        self.assertEqual(chat_info['scenario'], "anime")
        self.assertEqual(chat_info['user_id'], user_id)
    
    def test_message_storage(self):
        """Тест сохранения сообщений"""
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
        
        # Добавление ответа бота
        bot_response = "Добро пожаловать в Небесную Гостиницу!"
        success = self.db.add_message(chat_id, user_id, bot_response, False)
        self.assertTrue(success)
        
        # Проверка сохранения сообщений
        messages = self.db.get_chat_messages(chat_id)
        self.assertEqual(len(messages), 2)
        
        # Проверка первого сообщения (пользователь)
        self.assertTrue(messages[0]['is_from_user'])
        self.assertEqual(messages[0]['text'], user_message)
        
        # Проверка второго сообщения (бот)
        self.assertFalse(messages[1]['is_from_user'])
        self.assertEqual(messages[1]['text'], bot_response)
    
    def test_message_ignoring(self):
        """Тест игнорирования сообщений"""
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
        
        # Проверка, что сообщение игнорируется
        messages_after = self.db.get_chat_messages(chat_id)
        self.assertEqual(len(messages_after), 0)  # Игнорируемые сообщения не возвращаются
    
    def test_chat_settings(self):
        """Тест настроек чата"""
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
        self.assertEqual(chat_settings['empathy_level'], 80)
        self.assertEqual(chat_settings['response_length'], 'long')
    
    def test_keyboard_generation(self):
        """Тест генерации клавиатур"""
        # Тест главного меню
        keyboard = self.keyboard_manager.get_main_menu_keyboard()
        self.assertIsNotNone(keyboard)
        
        # Тест клавиатуры создания чата
        keyboard = self.keyboard_manager.get_create_chat_keyboard()
        self.assertIsNotNone(keyboard)
        
        # Тест клавиатуры списка чатов
        chats = [
            {'chat_id': 1, 'title': 'Тестовый чат 1'},
            {'chat_id': 2, 'title': 'Тестовый чат 2'}
        ]
        keyboard = self.keyboard_manager.get_chat_list_keyboard(chats)
        self.assertIsNotNone(keyboard)
    
    def test_chat_summary_generation(self):
        """Тест генерации описания чата"""
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
    
    def test_chat_management(self):
        """Тест управления чатами"""
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
        
        # Обновление названия
        success = self.db.update_chat_title(chat_id, "Новое название")
        self.assertTrue(success)
        
        # Проверка обновления
        chat_info = self.db.get_chat(chat_id)
        self.assertEqual(chat_info['title'], "Новое название")
        
        # Удаление чата
        success = self.db.delete_chat(chat_id)
        self.assertTrue(success)
        
        # Проверка удаления
        chats_after = self.db.get_user_chats(user_id)
        self.assertEqual(len(chats_after), 0)

if __name__ == '__main__':
    print("Запуск упрощенных тестов бота Оданна...")
    unittest.main(verbosity=2)