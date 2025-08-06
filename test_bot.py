import unittest
import tempfile
import os
from unittest.mock import Mock, patch
from database import Database
from ai_model import AIModel
from chat_manager import ChatManager
from keyboard_manager import KeyboardManager

class TestOdannaBot(unittest.TestCase):
    
    def setUp(self):
        """Настройка тестов"""
        # Создание временной базы данных
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Инициализация компонентов
        self.db = Database(self.temp_db.name)
        self.ai_model = AIModel()
        self.chat_manager = ChatManager(self.db, self.ai_model)
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
        chat_id = self.chat_manager.create_chat(
            user_id=user_id,
            title="Тестовый чат",
            scenario="anime"
        )
        
        self.assertIsNotNone(chat_id)
        
        # Получение информации о чате
        chat_info = self.chat_manager.get_chat_info(chat_id)
        self.assertIsNotNone(chat_info)
        self.assertEqual(chat_info['title'], "Тестовый чат")
        self.assertEqual(chat_info['scenario'], "anime")
        self.assertEqual(chat_info['user_id'], user_id)
    
    def test_message_processing(self):
        """Тест обработки сообщений"""
        user_id = 12345
        
        # Создание чата
        chat_id = self.chat_manager.create_chat(
            user_id=user_id,
            title="Тестовый чат",
            scenario="anime"
        )
        
        # Отправка сообщения пользователя
        user_message = "Привет, Оданна!"
        response = self.chat_manager.process_message(chat_id, user_id, user_message, "male")
        
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        
        # Проверка сохранения сообщений
        messages = self.chat_manager.get_chat_messages(chat_id)
        self.assertEqual(len(messages), 2)  # Сообщение пользователя + ответ бота
        
        # Проверка первого сообщения (пользователь)
        self.assertTrue(messages[0]['is_from_user'])
        self.assertEqual(messages[0]['text'], user_message)
        
        # Проверка второго сообщения (бот)
        self.assertFalse(messages[1]['is_from_user'])
        self.assertEqual(messages[1]['text'], response)
    
    def test_forget_command(self):
        """Тест команды забыть сообщение"""
        user_id = 12345
        
        # Создание чата
        chat_id = self.chat_manager.create_chat(
            user_id=user_id,
            title="Тестовый чат",
            scenario="anime"
        )
        
        # Отправка сообщения
        self.chat_manager.process_message(chat_id, user_id, "Это важное сообщение", "male")
        
        # Команда забыть
        forget_response = self.chat_manager.process_message(chat_id, user_id, "забудь важное", "male")
        
        self.assertIn("забыл", forget_response.lower())
    
    def test_ai_model_analysis(self):
        """Тест анализа сообщений AI моделью"""
        # Тест анализа позитивного сообщения
        analysis = self.ai_model.analyze_message("Спасибо, все отлично!", "female")
        self.assertEqual(analysis['emotion'], 'positive')
        self.assertGreater(analysis['empathy_level'], 50)
        
        # Тест анализа негативного сообщения
        analysis = self.ai_model.analyze_message("Мне плохо, помоги", "male")
        self.assertEqual(analysis['emotion'], 'negative')
        self.assertGreater(analysis['empathy_level'], 50)
        
        # Тест анализа срочного сообщения
        analysis = self.ai_model.analyze_message("Срочно нужна помощь!", "female")
        self.assertEqual(analysis['urgency'], 'high')
        self.assertGreater(analysis['empathy_level'], 50)
    
    def test_fallback_response_generation(self):
        """Тест генерации fallback ответов"""
        messages = []
        
        # Тест приветствия
        response = self.ai_model._generate_fallback_response(messages, "female", 70)
        self.assertIn("Добро пожаловать", response)
        
        # Тест с сообщением пользователя
        messages = [{'text': 'Привет', 'is_from_user': True}]
        response = self.ai_model._generate_fallback_response(messages, "male", 50)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
    
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
        chat_id = self.chat_manager.create_chat(
            user_id=user_id,
            title="Тестовый чат",
            scenario="anime"
        )
        
        # Добавление сообщений
        self.chat_manager.process_message(chat_id, user_id, "Я люблю аниме", "male")
        self.chat_manager.process_message(chat_id, user_id, "Расскажи про аниме", "male")
        
        # Получение описания
        summary = self.chat_manager.get_chat_summary(chat_id)
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)
    
    def test_chat_settings(self):
        """Тест настроек чата"""
        user_id = 12345
        
        # Создание чата с настройками
        settings = {
            'empathy_level': 80,
            'response_length': 'long',
            'personality_traits': ['kind', 'wise']
        }
        
        chat_id = self.chat_manager.create_chat(
            user_id=user_id,
            title="Чат с настройками",
            scenario="anime",
            settings=settings
        )
        
        # Проверка настроек
        chat_settings = self.chat_manager.get_chat_info(chat_id)['settings']
        self.assertEqual(chat_settings['empathy_level'], 80)
        self.assertEqual(chat_settings['response_length'], 'long')
    
    def test_message_ignoring(self):
        """Тест игнорирования сообщений"""
        user_id = 12345
        
        # Создание чата
        chat_id = self.chat_manager.create_chat(
            user_id=user_id,
            title="Тестовый чат",
            scenario="anime"
        )
        
        # Добавление сообщения
        self.chat_manager.process_message(chat_id, user_id, "Это сообщение", "male")
        
        # Игнорирование сообщения
        messages = self.db.get_all_chat_messages(chat_id)
        message_id = messages[0]['message_id']
        
        success = self.db.mark_message_ignored(message_id)
        self.assertTrue(success)
        
        # Проверка, что сообщение игнорируется
        messages_after = self.db.get_chat_messages(chat_id)
        self.assertEqual(len(messages_after), 1)  # Только ответ бота
    
    def test_scenario_handling(self):
        """Тест обработки сценариев"""
        # Тест сценария потери работы
        response = self.chat_manager.handle_scenario("lost_job", "Я потерял работу")
        self.assertIsNotNone(response)
        self.assertIn("потеря работы", response.lower())
        
        # Тест сценария проблем в отношениях
        response = self.chat_manager.handle_scenario("relationship_problems", "Мы расстались")
        self.assertIsNotNone(response)
        self.assertIn("отношения", response.lower())
        
        # Тест несуществующего сценария
        response = self.chat_manager.handle_scenario("unknown", "Обычное сообщение")
        self.assertIsNone(response)

if __name__ == '__main__':
    unittest.main()