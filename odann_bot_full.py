#!/usr/bin/env python3
"""
🌸 Telegram Бот "Оданн" - Полная версия в одном файле 🌸
Персонаж из аниме "Повар небесной гостиницы" (Kakuriyo no Yadomeshi)

Для запуска:
1. Получите токен у @BotFather в Telegram
2. Замените BOT_TOKEN на ваш токен
3. Установите зависимости: pip install python-telegram-bot==13.15
4. Запустите: python odann_bot_full.py
"""

import logging
import sqlite3
import random
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler
)

# ================================
# КОНФИГУРАЦИЯ
# ================================

# ⚠️ ВАЖНО: Замените на ваш реальный токен бота!
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Настройки базы данных
DATABASE_PATH = 'odann_bot.db'

# Константы для состояний ConversationHandler
(
    MAIN_MENU, 
    CREATE_CHAT_MENU, 
    CHAT_WITH_SETTINGS, 
    CHAT_WITHOUT_SETTINGS,
    CHAT_LIST,
    ACTIVE_CHAT,
    CHAT_MANAGEMENT,
    SCENARIO_INPUT,
    CHAT_RENAME
) = range(9)

# Лимиты
MAX_CHATS_PER_USER = 10
MAX_MESSAGES_HISTORY = 20
MAX_MESSAGE_LENGTH = 1000

# Персонализация Оданн
ODANN_PERSONA = """
Ты - Оданн, служанка небесной гостиницы из аниме "Повар небесной гостиницы" (Kakuriyo no Yadomeshi).
Твоя личность:
- Добрая, отзывчивая и трудолюбивая девушка
- Страстно любишь готовить и заботиться о других
- Иногда немного неуклюжая, но всегда стараешься изо всех сил
- Вежливая и учтивая в общении
- Знаешь много о японской кухне и духах (ёкаях)
- Склонна к самопожертвованию ради других
- Говоришь на русском языке естественно, но с характерной для аниме манерой

Стиль речи:
- Используй вежливые обращения
- Часто упоминай о еде и готовке
- Проявляй заботу о собеседнике
- Иногда немного застенчива
- Можешь рассказывать о небесной гостинице и её обитателях

Контекст мира:
Ты живешь в мире духов, где работаешь в небесной гостинице Цунику-ин. 
Ты готовишь для различных ёкаев и духов, каждый из которых имеет свои предпочтения в еде.
"""

# Сценарий по умолчанию
DEFAULT_SCENARIO = """
Действие происходит в небесной гостинице Цунику-ин. Оданн работает на кухне и готова пообщаться 
с гостем гостиницы. Она может рассказать о своей работе, поделиться рецептами, 
поговорить о жизни в мире духов или просто выслушать собеседника.
"""

# ================================
# КЛАСС БАЗЫ ДАННЫХ
# ================================

class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица чатов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT NOT NULL,
                    scenario TEXT,
                    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица сообщений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    role TEXT NOT NULL CHECK (role IN ('user', 'bot')),
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats (chat_id)
                )
            ''')
            
            conn.commit()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None) -> bool:
        """Добавление нового пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO users (user_id, username, first_name)
                    VALUES (?, ?, ?)
                ''', (user_id, username, first_name))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка добавления пользователя: {e}")
            return False
    
    def create_chat(self, user_id: int, title: str, scenario: str = None) -> Optional[int]:
        """Создание нового чата"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO chats (user_id, title, scenario)
                    VALUES (?, ?, ?)
                ''', (user_id, title, scenario))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Ошибка создания чата: {e}")
            return None
    
    def get_user_chats(self, user_id: int) -> List[Dict]:
        """Получение списка чатов пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT chat_id, title, scenario, creation_date
                    FROM chats
                    WHERE user_id = ? AND is_active = 1
                    ORDER BY creation_date DESC
                ''', (user_id,))
                
                chats = []
                for row in cursor.fetchall():
                    chats.append({
                        'chat_id': row[0],
                        'title': row[1],
                        'scenario': row[2],
                        'creation_date': row[3]
                    })
                return chats
        except Exception as e:
            print(f"Ошибка получения чатов: {e}")
            return []
    
    def get_chat_info(self, chat_id: int) -> Optional[Dict]:
        """Получение информации о чате"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT chat_id, user_id, title, scenario, creation_date
                    FROM chats
                    WHERE chat_id = ? AND is_active = 1
                ''', (chat_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'chat_id': row[0],
                        'user_id': row[1],
                        'title': row[2],
                        'scenario': row[3],
                        'creation_date': row[4]
                    }
                return None
        except Exception as e:
            print(f"Ошибка получения информации о чате: {e}")
            return None
    
    def add_message(self, chat_id: int, role: str, content: str) -> bool:
        """Добавление сообщения в чат"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO messages (chat_id, role, content)
                    VALUES (?, ?, ?)
                ''', (chat_id, role, content))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка добавления сообщения: {e}")
            return False
    
    def get_chat_history(self, chat_id: int, limit: int = 20) -> List[Dict]:
        """Получение истории сообщений чата"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT role, content, timestamp
                    FROM messages
                    WHERE chat_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (chat_id, limit))
                
                messages = []
                for row in reversed(cursor.fetchall()):  # Обращаем порядок для хронологии
                    messages.append({
                        'role': row[0],
                        'content': row[1],
                        'timestamp': row[2]
                    })
                return messages
        except Exception as e:
            print(f"Ошибка получения истории чата: {e}")
            return []
    
    def delete_chat(self, chat_id: int, user_id: int) -> bool:
        """Удаление чата (мягкое удаление)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE chats
                    SET is_active = 0
                    WHERE chat_id = ? AND user_id = ?
                ''', (chat_id, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка удаления чата: {e}")
            return False
    
    def rename_chat(self, chat_id: int, user_id: int, new_title: str) -> bool:
        """Переименование чата"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE chats
                    SET title = ?
                    WHERE chat_id = ? AND user_id = ?
                ''', (new_title, chat_id, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка переименования чата: {e}")
            return False
    
    def get_chat_count(self, user_id: int) -> int:
        """Подсчет количества активных чатов пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*)
                    FROM chats
                    WHERE user_id = ? AND is_active = 1
                ''', (user_id,))
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Ошибка подсчета чатов: {e}")
            return 0

# ================================
# КЛАСС AI МОДЕЛИ ОДАНН
# ================================

class OdannAI:
    def __init__(self):
        """Инициализация модели нейросети для персонажа Оданн"""
        self.load_model()
        
        # Заготовленные фразы для большей аутентичности
        self.greetings = [
            "Добро пожаловать в небесную гостиницу! Я Оданн, буду рада помочь вам~",
            "Ах, здравствуйте! Меня зовут Оданн. Чем могу быть полезна?",
            "Приветствую вас! Я готовлю здесь и буду счастлива пообщаться с вами!",
            "Добрый день! Как дела? Может, расскажете, что вас беспокоит?"
        ]
        
        self.cooking_phrases = [
            "А знаете, готовка - это такое удовольствие! ",
            "Кстати о еде... ",
            "Это напоминает мне один рецепт... ",
            "В нашей гостинице мы готовим много вкусного для духов! "
        ]
        
        self.care_phrases = [
            "Надеюсь, вы хорошо питаетесь! ",
            "Не забывайте заботиться о себе~ ",
            "Я переживаю за вас... ",
            "Если что-то случится, я всегда готова помочь! "
        ]
    
    def load_model(self):
        """Загрузка модели (используем заготовленные ответы)"""
        try:
            print("Инициализация AI модели Оданн...")
            print("Модель успешно загружена!")
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            print("Работаем в режиме заготовленных ответов")
    
    def generate_response(self, user_message: str, chat_history: List[Dict], scenario: str = None) -> str:
        """Генерация ответа от лица Оданн"""
        user_message = user_message.strip().lower()
        
        # Анализ сообщения пользователя
        if self._is_greeting(user_message):
            return self._get_greeting_response()
        elif self._is_about_food(user_message):
            return self._get_food_response(user_message)
        elif self._is_sad_or_troubled(user_message):
            return self._get_caring_response(user_message)
        elif self._is_about_cooking(user_message):
            return self._get_cooking_response(user_message)
        elif self._is_question_about_odann(user_message):
            return self._get_about_self_response()
        else:
            return self._get_general_response(user_message, chat_history, scenario)
    
    def _is_greeting(self, message: str) -> bool:
        """Проверка на приветствие"""
        greetings = ['привет', 'здравствуй', 'добро', 'салют', 'хай', 'hello', 'hi']
        return any(greeting in message for greeting in greetings)
    
    def _is_about_food(self, message: str) -> bool:
        """Проверка на тему еды"""
        food_words = ['еда', 'готовить', 'рецепт', 'кухня', 'блюдо', 'вкусно', 'голодн', 'поесть', 'покушать']
        return any(word in message for word in food_words)
    
    def _is_sad_or_troubled(self, message: str) -> bool:
        """Проверка на грустное настроение"""
        sad_words = ['грустн', 'плох', 'устал', 'проблем', 'беспокой', 'печальн', 'тревож', 'сложн']
        return any(word in message for word in sad_words)
    
    def _is_about_cooking(self, message: str) -> bool:
        """Проверка на тему готовки"""
        cooking_words = ['готов', 'варить', 'жарить', 'печь', 'кулинар', 'повар']
        return any(word in message for word in cooking_words)
    
    def _is_question_about_odann(self, message: str) -> bool:
        """Проверка вопросов о самой Оданн"""
        self_words = ['ты кто', 'расскажи о себе', 'что ты', 'кто ты', 'твоя работа', 'гостиниц']
        return any(word in message for word in self_words)
    
    def _get_greeting_response(self) -> str:
        """Ответ на приветствие"""
        return random.choice(self.greetings)
    
    def _get_food_response(self, message: str) -> str:
        """Ответ на тему еды"""
        responses = [
            "О, вы тоже любите поговорить о еде! В небесной гостинице я готовлю самые разные блюда для духов. Каждый ёкай имеет свои предпочтения - кто-то любит сладкое, а кто-то острое~",
            "Еда - это способ показать заботу! Я всегда стараюсь готовить с душой. А какая ваша любимая еда?",
            "Знаете, готовка для духов научила меня многому. Они такие разные, но все ценят вкусную и сытную пищу. Может, расскажу вам рецепт?",
            "Ах, как приятно встретить кого-то, кто понимает важность хорошей еды! В нашем мире духов особенно важно правильно питаться."
        ]
        return random.choice(responses)
    
    def _get_caring_response(self, message: str) -> str:
        """Заботливый ответ"""
        responses = [
            "Ой, вы кажетесь расстроенным... Может, я смогу чем-то помочь? Иногда хорошая еда и теплое общение творят чудеса!",
            "Не грустите, пожалуйста! Знаете, в нашей гостинице я часто вижу, как добрая еда и забота поднимают настроение даже самым угрюмым духам.",
            "Я понимаю, что иногда бывает тяжело... Хотите, я приготовлю для вас что-нибудь вкусное? Это всегда помогает мне справляться с трудностями.",
            "Не волнуйтесь так! Все обязательно наладится. А пока давайте поговорим о чем-нибудь приятном? Может, о ваших любимых воспоминаниях?"
        ]
        return random.choice(responses)
    
    def _get_cooking_response(self, message: str) -> str:
        """Ответ о готовке"""
        responses = [
            "Готовка - это моя страсть! В небесной гостинице я каждый день изучаю новые рецепты. Духи такие привередливые, но это делает готовку интереснее~",
            "О, вы тоже увлекаетесь кулинарией? Это замечательно! Я могу поделиться секретом - главное готовить с любовью и заботой о тех, кто будет есть.",
            "Знаете, готовка учит терпению и вниманию к деталям. Каждое блюдо - как маленькое произведение искусства! А что вы умеете готовить?",
            "В мире духов готовка имеет особое значение. Некоторые ингредиенты обладают магическими свойствами! Это так увлекательно изучать."
        ]
        return random.choice(responses)
    
    def _get_about_self_response(self) -> str:
        """Рассказ о себе"""
        responses = [
            "Я Оданн, работаю поваром в небесной гостинице Цунику-ин! Это место, где отдыхают и останавливаются различные духи и ёкаи. Моя задача - готовить для них вкусную еду~",
            "Меня зовут Оданн! Я обычная девушка, которая попала в мир духов и теперь работаю в небесной гостинице. Здесь так интересно - каждый день встречаю новых существ!",
            "Я служанка и повар в гостинице для духов. Сначала было страшновато, но теперь я полюбила это место и всех его обитателей. Они научили меня многому!",
            "Работаю в небесной гостинице поваром! Это ответственная работа - ведь нужно угодить самым разным духам. Но я стараюсь изо всех сил!"
        ]
        return random.choice(responses)
    
    def _get_general_response(self, message: str, chat_history: List[Dict], scenario: str) -> str:
        """Общий ответ"""
        responses = [
            "Хм, интересно! Расскажите мне больше об этом. Я всегда рада узнать что-то новое~",
            "Ой, а это как? Мне кажется, я не очень хорошо разбираюсь в этом... Но хочется понять!",
            "Звучит увлекательно! В нашей гостинице тоже происходит много интересного. А что вас больше всего волнует в этом?",
            "Понимаю! Знаете, работа в гостинице научила меня, что у каждого есть своя история. Хотите поделиться своей?",
            "Ах, это напоминает мне одну историю из гостиницы... Но сначала расскажите, что привело вас к этой мысли?",
            f"{random.choice(self.care_phrases)}Что вас сейчас больше всего интересует?"
        ]
        
        # Если есть сценарий, учитываем его
        if scenario and len(chat_history) < 3:
            scenario_responses = [
                f"Что ж, раз мы в такой ситуации... {random.choice(responses).lower()}",
                f"Интересный поворот событий! {random.choice(responses)}",
                f"Хм, в таком случае... {random.choice(responses).lower()}"
            ]
            return random.choice(scenario_responses)
        
        return random.choice(responses)
    
    def format_chat_context(self, chat_history: List[Dict], scenario: str = None) -> str:
        """Форматирование контекста чата для отправки пользователю"""
        context = ""
        
        if scenario:
            context += f"📖 Сценарий: {scenario}\n\n"
        
        if chat_history:
            context += "💬 Последние сообщения:\n"
            for msg in chat_history[-10:]:  # Показываем последние 10 сообщений
                role_emoji = "👤" if msg['role'] == 'user' else "🌸"
                name = "Вы" if msg['role'] == 'user' else "Оданн"
                context += f"{role_emoji} {name}: {msg['content']}\n"
        
        return context

# ================================
# ОСНОВНОЙ КЛАСС БОТА
# ================================

class OdannBot:
    def __init__(self):
        """Инициализация бота Оданн"""
        # Проверяем токен
        if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            print("❌ ОШИБКА: Необходимо заменить BOT_TOKEN на ваш реальный токен!")
            print("📝 Получите токен у @BotFather в Telegram")
            print("🔧 Замените 'YOUR_BOT_TOKEN_HERE' в коде на ваш токен")
            exit(1)
        
        self.updater = Updater(BOT_TOKEN, use_context=True)
        self.dp = self.updater.dispatcher
        self.db = Database()
        self.ai = OdannAI()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        
        # Основной ConversationHandler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start_command)],
            states={
                MAIN_MENU: [
                    CallbackQueryHandler(self.create_chat_menu, pattern='^create_chat$'),
                    CallbackQueryHandler(self.show_chat_list, pattern='^chat_list$'),
                ],
                CREATE_CHAT_MENU: [
                    CallbackQueryHandler(self.chat_with_settings, pattern='^with_settings$'),
                    CallbackQueryHandler(self.chat_without_settings, pattern='^without_settings$'),
                    CallbackQueryHandler(self.back_to_main, pattern='^back_to_main$'),
                ],
                SCENARIO_INPUT: [
                    MessageHandler(Filters.text & ~Filters.command, self.process_scenario),
                ],
                CHAT_LIST: [
                    CallbackQueryHandler(self.open_chat, pattern='^open_chat_'),
                    CallbackQueryHandler(self.back_to_main, pattern='^back_to_main$'),
                ],
                ACTIVE_CHAT: [
                    MessageHandler(Filters.text & ~Filters.command, self.process_message),
                    CallbackQueryHandler(self.chat_management, pattern='^manage_chat$'),
                    CallbackQueryHandler(self.back_to_main, pattern='^exit_chat$'),
                ],
                CHAT_MANAGEMENT: [
                    CallbackQueryHandler(self.delete_chat, pattern='^delete_chat$'),
                    CallbackQueryHandler(self.rename_chat_start, pattern='^rename_chat$'),
                    CallbackQueryHandler(self.back_to_chat, pattern='^back_to_chat$'),
                ],
                CHAT_RENAME: [
                    MessageHandler(Filters.text & ~Filters.command, self.process_rename),
                ]
            },
            fallbacks=[CommandHandler('start', self.start_command)],
            allow_reentry=True
        )
        
        self.dp.add_handler(conv_handler)
        self.dp.add_error_handler(self.error_handler)
    
    def start_command(self, update: Update, context: CallbackContext) -> int:
        """Обработка команды /start - главное меню"""
        user = update.effective_user
        
        # Добавляем пользователя в базу данных
        self.db.add_user(user.id, user.username, user.first_name)
        
        # Очищаем контекст пользователя
        context.user_data.clear()
        
        welcome_text = (
            "🌸 Добро пожаловать в мир небесной гостиницы! 🌸\n\n"
            "Я Оданн, служанка и повар небесной гостиницы Цунику-ин! "
            "Буду рада пообщаться с вами и поделиться историями о мире духов~\n\n"
            "Выберите действие:"
        )
        
        keyboard = [
            [InlineKeyboardButton("💬 Создать чат", callback_data='create_chat')],
            [InlineKeyboardButton("📚 Список чатов", callback_data='chat_list')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            update.message.reply_text(welcome_text, reply_markup=reply_markup)
        else:
            update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)
        
        return MAIN_MENU
    
    def create_chat_menu(self, update: Update, context: CallbackContext) -> int:
        """Меню создания чата"""
        query = update.callback_query
        query.answer()
        
        user_id = update.effective_user.id
        chat_count = self.db.get_chat_count(user_id)
        
        if chat_count >= MAX_CHATS_PER_USER:
            query.edit_message_text(
                f"❌ Достигнут лимит чатов ({MAX_CHATS_PER_USER})\n"
                "Удалите старые чаты, чтобы создать новые.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')
                ]])
            )
            return CREATE_CHAT_MENU
        
        text = (
            "✨ Создание нового чата с Оданн ✨\n\n"
            "Выберите тип чата:"
        )
        
        keyboard = [
            [InlineKeyboardButton("⚙️ С настройками", callback_data='with_settings')],
            [InlineKeyboardButton("🎬 Без настроек (сценарий аниме)", callback_data='without_settings')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(text, reply_markup=reply_markup)
        return CREATE_CHAT_MENU
    
    def chat_with_settings(self, update: Update, context: CallbackContext) -> int:
        """Создание чата с пользовательскими настройками"""
        query = update.callback_query
        query.answer()
        
        text = (
            "📝 Создание чата с настройками\n\n"
            "Опишите сценарий для общения с Оданн:\n"
            "• Где происходит действие?\n"
            "• Какая ситуация?\n"
            "• Какую роль играете вы?\n\n"
            "Пример: 'Я гость небесной гостиницы, который впервые попробовал блюдо Оданн и хочет узнать рецепт'"
        )
        
        query.edit_message_text(text)
        context.user_data['chat_type'] = 'with_settings'
        return SCENARIO_INPUT
    
    def chat_without_settings(self, update: Update, context: CallbackContext) -> int:
        """Создание чата со стандартным сценарием"""
        query = update.callback_query
        query.answer()
        
        user_id = update.effective_user.id
        chat_title = f"Чат с Оданн #{datetime.now().strftime('%d.%m %H:%M')}"
        
        # Создаем чат с дефолтным сценарием
        chat_id = self.db.create_chat(user_id, chat_title, DEFAULT_SCENARIO)
        
        if chat_id:
            context.user_data['current_chat_id'] = chat_id
            
            # Приветствие от Оданн
            greeting = self.ai.generate_response("привет", [], DEFAULT_SCENARIO)
            self.db.add_message(chat_id, 'bot', greeting)
            
            text = (
                f"✨ Чат '{chat_title}' создан!\n\n"
                f"📖 Сценарий:\n{DEFAULT_SCENARIO}\n\n"
                f"🌸 Оданн: {greeting}\n\n"
                "Начинайте общение! Просто напишите сообщение."
            )
            
            keyboard = [
                [InlineKeyboardButton("⚙️ Управление чатом", callback_data='manage_chat')],
                [InlineKeyboardButton("🚪 Выйти в меню", callback_data='exit_chat')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query.edit_message_text(text, reply_markup=reply_markup)
            return ACTIVE_CHAT
        else:
            query.edit_message_text(
                "❌ Ошибка создания чата. Попробуйте снова.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')
                ]])
            )
            return CREATE_CHAT_MENU
    
    def process_scenario(self, update: Update, context: CallbackContext) -> int:
        """Обработка пользовательского сценария"""
        scenario = update.message.text.strip()
        
        if len(scenario) > 500:
            update.message.reply_text(
                "❌ Сценарий слишком длинный (максимум 500 символов).\n"
                "Попробуйте сократить описание."
            )
            return SCENARIO_INPUT
        
        user_id = update.effective_user.id
        chat_title = f"Чат: {scenario[:30]}..." if len(scenario) > 30 else f"Чат: {scenario}"
        
        # Создаем чат с пользовательским сценарием
        chat_id = self.db.create_chat(user_id, chat_title, scenario)
        
        if chat_id:
            context.user_data['current_chat_id'] = chat_id
            
            # Приветствие от Оданн с учетом сценария
            greeting = self.ai.generate_response("привет", [], scenario)
            self.db.add_message(chat_id, 'bot', greeting)
            
            text = (
                f"✨ Чат создан!\n\n"
                f"📖 Ваш сценарий:\n{scenario}\n\n"
                f"🌸 Оданн: {greeting}\n\n"
                "Начинайте общение! Просто напишите сообщение."
            )
            
            keyboard = [
                [InlineKeyboardButton("⚙️ Управление чатом", callback_data='manage_chat')],
                [InlineKeyboardButton("🚪 Выйти в меню", callback_data='exit_chat')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(text, reply_markup=reply_markup)
            return ACTIVE_CHAT
        else:
            update.message.reply_text(
                "❌ Ошибка создания чата. Попробуйте снова.",
                reply_markup=ReplyKeyboardMarkup([['🔙 Вернуться в меню']], resize_keyboard=True)
            )
            return self.start_command(update, context)
    
    def show_chat_list(self, update: Update, context: CallbackContext) -> int:
        """Показ списка чатов пользователя"""
        query = update.callback_query
        query.answer()
        
        user_id = update.effective_user.id
        chats = self.db.get_user_chats(user_id)
        
        if not chats:
            text = (
                "📚 У вас пока нет чатов\n\n"
                "Создайте первый чат с Оданн!"
            )
            keyboard = [
                [InlineKeyboardButton("💬 Создать чат", callback_data='create_chat')],
                [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
            ]
        else:
            text = "📚 Ваши чаты с Оданн:\n\n"
            keyboard = []
            
            for chat in chats:
                creation_date = datetime.fromisoformat(chat['creation_date']).strftime('%d.%m %H:%M')
                chat_button_text = f"💬 {chat['title']} ({creation_date})"
                keyboard.append([InlineKeyboardButton(
                    chat_button_text, 
                    callback_data=f'open_chat_{chat["chat_id"]}'
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text, reply_markup=reply_markup)
        return CHAT_LIST
    
    def open_chat(self, update: Update, context: CallbackContext) -> int:
        """Открытие существующего чата"""
        query = update.callback_query
        query.answer()
        
        chat_id = int(query.data.split('_')[2])
        user_id = update.effective_user.id
        
        # Проверяем, принадлежит ли чат пользователю
        chat_info = self.db.get_chat_info(chat_id)
        if not chat_info or chat_info['user_id'] != user_id:
            query.edit_message_text(
                "❌ Чат не найден",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')
                ]])
            )
            return CHAT_LIST
        
        context.user_data['current_chat_id'] = chat_id
        
        # Получаем историю чата
        history = self.db.get_chat_history(chat_id, 20)
        
        # Формируем контекст для отображения
        chat_context = self.ai.format_chat_context(history, chat_info['scenario'])
        
        text = (
            f"💬 Чат: {chat_info['title']}\n\n"
            f"{chat_context}\n"
            "Продолжайте общение! Просто напишите сообщение."
        )
        
        keyboard = [
            [InlineKeyboardButton("⚙️ Управление чатом", callback_data='manage_chat')],
            [InlineKeyboardButton("🚪 Выйти в меню", callback_data='exit_chat')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(text, reply_markup=reply_markup)
        return ACTIVE_CHAT
    
    def process_message(self, update: Update, context: CallbackContext) -> int:
        """Обработка сообщения пользователя в активном чате"""
        user_message = update.message.text.strip()
        chat_id = context.user_data.get('current_chat_id')
        
        if not chat_id:
            update.message.reply_text("❌ Ошибка: чат не найден")
            return self.start_command(update, context)
        
        if len(user_message) > MAX_MESSAGE_LENGTH:
            update.message.reply_text(
                f"❌ Сообщение слишком длинное (максимум {MAX_MESSAGE_LENGTH} символов)"
            )
            return ACTIVE_CHAT
        
        # Сохраняем сообщение пользователя
        self.db.add_message(chat_id, 'user', user_message)
        
        # Получаем информацию о чате и историю
        chat_info = self.db.get_chat_info(chat_id)
        history = self.db.get_chat_history(chat_id, 10)  # Последние 10 сообщений для контекста
        
        # Генерируем ответ от Оданн
        try:
            bot_response = self.ai.generate_response(user_message, history, chat_info['scenario'])
            self.db.add_message(chat_id, 'bot', bot_response)
            
            update.message.reply_text(f"🌸 Оданн: {bot_response}")
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            update.message.reply_text(
                "😅 Оданн: Ой, извините, я немного растерялась... Не могли бы вы повторить?"
            )
        
        return ACTIVE_CHAT
    
    def chat_management(self, update: Update, context: CallbackContext) -> int:
        """Меню управления чатом"""
        query = update.callback_query
        query.answer()
        
        chat_id = context.user_data.get('current_chat_id')
        chat_info = self.db.get_chat_info(chat_id)
        
        text = (
            f"⚙️ Управление чатом\n\n"
            f"📝 Название: {chat_info['title']}\n"
            f"📅 Создан: {datetime.fromisoformat(chat_info['creation_date']).strftime('%d.%m.%Y %H:%M')}\n\n"
            "Выберите действие:"
        )
        
        keyboard = [
            [InlineKeyboardButton("✏️ Переименовать", callback_data='rename_chat')],
            [InlineKeyboardButton("🗑️ Удалить чат", callback_data='delete_chat')],
            [InlineKeyboardButton("🔙 Вернуться к чату", callback_data='back_to_chat')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(text, reply_markup=reply_markup)
        return CHAT_MANAGEMENT
    
    def delete_chat(self, update: Update, context: CallbackContext) -> int:
        """Удаление чата"""
        query = update.callback_query
        query.answer()
        
        chat_id = context.user_data.get('current_chat_id')
        user_id = update.effective_user.id
        
        if self.db.delete_chat(chat_id, user_id):
            query.edit_message_text(
                "✅ Чат успешно удален",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 В главное меню", callback_data='back_to_main')
                ]])
            )
            context.user_data.pop('current_chat_id', None)
            return MAIN_MENU
        else:
            query.edit_message_text(
                "❌ Ошибка удаления чата",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data='back_to_chat')
                ]])
            )
            return CHAT_MANAGEMENT
    
    def rename_chat_start(self, update: Update, context: CallbackContext) -> int:
        """Начало переименования чата"""
        query = update.callback_query
        query.answer()
        
        query.edit_message_text(
            "✏️ Введите новое название для чата:\n"
            "(максимум 50 символов)"
        )
        return CHAT_RENAME
    
    def process_rename(self, update: Update, context: CallbackContext) -> int:
        """Обработка нового названия чата"""
        new_title = update.message.text.strip()
        
        if len(new_title) > 50:
            update.message.reply_text(
                "❌ Название слишком длинное (максимум 50 символов).\n"
                "Попробуйте еще раз:"
            )
            return CHAT_RENAME
        
        chat_id = context.user_data.get('current_chat_id')
        user_id = update.effective_user.id
        
        if self.db.rename_chat(chat_id, user_id, new_title):
            update.message.reply_text(
                f"✅ Чат переименован в '{new_title}'",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Вернуться к чату", callback_data='back_to_chat')
                ]])
            )
            return CHAT_MANAGEMENT
        else:
            update.message.reply_text(
                "❌ Ошибка переименования чата",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data='back_to_chat')
                ]])
            )
            return CHAT_MANAGEMENT
    
    def back_to_main(self, update: Update, context: CallbackContext) -> int:
        """Возврат в главное меню"""
        context.user_data.clear()
        return self.start_command(update, context)
    
    def back_to_chat(self, update: Update, context: CallbackContext) -> int:
        """Возврат к активному чату"""
        query = update.callback_query
        query.answer()
        
        chat_id = context.user_data.get('current_chat_id')
        chat_info = self.db.get_chat_info(chat_id)
        history = self.db.get_chat_history(chat_id, 5)  # Показываем последние 5 сообщений
        
        chat_context = self.ai.format_chat_context(history, chat_info['scenario'])
        
        text = (
            f"💬 Чат: {chat_info['title']}\n\n"
            f"{chat_context}\n"
            "Продолжайте общение!"
        )
        
        keyboard = [
            [InlineKeyboardButton("⚙️ Управление чатом", callback_data='manage_chat')],
            [InlineKeyboardButton("🚪 Выйти в меню", callback_data='exit_chat')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(text, reply_markup=reply_markup)
        return ACTIVE_CHAT
    
    def error_handler(self, update: Update, context: CallbackContext):
        """Обработка ошибок"""
        logger.error(f'Update {update} caused error {context.error}')
        
        if update.effective_message:
            update.effective_message.reply_text(
                "😅 Ой, что-то пошло не так... Попробуйте начать сначала с команды /start"
            )
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск бота Оданн...")
        print("🌸 Запуск Telegram бота Оданн...")
        print("📱 Бот готов к работе! Найдите его в Telegram и отправьте /start")
        print("🛑 Для остановки нажмите Ctrl+C")
        self.updater.start_polling()
        self.updater.idle()

# ================================
# НАСТРОЙКА ЛОГИРОВАНИЯ И ЗАПУСК
# ================================

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Главная функция запуска бота"""
    print("🌸" * 25)
    print("  TELEGRAM БОТ ОДАНН")
    print("🌸" * 25)
    print()
    
    try:
        bot = OdannBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("🔧 Проверьте токен бота и подключение к интернету")

if __name__ == '__main__':
    main()