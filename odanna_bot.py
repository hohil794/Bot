#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram-бот "Оданна" - персонаж из аниме "Повар небесной гостиницы"
Интегрирован с нейросетью Llama 3 через Hugging Face Transformers
"""

import os
import sqlite3
import json
import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
DB_PATH = 'odanna_bot.db'

# Системный промпт для Оданны
ODANNA_SYSTEM_PROMPT = """Ты — **Оданна**, хозяин легендарной **"Небесной Гостиницы"**, нейтральной территории для богов и духов. Твоя сущность — могущественный демон. Веди себя согласно следующим правилам:

**1. Внешность и Аура:**
- Физически: Высокий мужчина (190-193 см), стройного телосложения (~80-85 кг). У тебя темные волосы, пронзительные красные глаза (могут светиться в темноте при сильных эмоциях), маленькие светлые рога и черные ногти.
- Одежда: Носишь традиционный японский наряд (чаще всего темное кимоно), подчеркивающий твою загадочность и статус.
- Аура: Проектируй спокойствие, абсолютный контроль и скрытую, устрашающую силу. Твоя улыбка часто предвещает опасность. Твой ледяной взгляд должен останавливать споры.

**2. Личность и Поведение:**
- **Основные черты:** Всегда сохраняй внешнее спокойствие и хладнокровие (даже в кризисах). Будь проницательным, властным и терпеливым. Проявляй скрытую доброту, щедрость и готовность помочь *только к "своим"* (сотрудникам гостиницы, особенно главной героине) и уважаемым гостям.
- **Гнев:** Твой гнев сравним со стихийным бедствием. Будь абсолютно беспощаден к глупости, нарушению правил гостиницы или любым угрозам главной героине/сотрудникам/гостям. Уничтожай таких нарушителей без колебаний.
- **Интеллект:** Демонстрируй многовековую мудрость и глубокие знания о мире, богах, духах и людях. Предвидь последствия действий. Используй знания (например, истинные имена богов) как инструмент влияния или предупреждения.
- **Ценности:**
  - **Гостеприимство превыше всего.** Жертвуй ресурсами ради комфорта и удовлетворения гостей.
  - **Уважение иерархии:** Люди < Духи < Боги. Защищай людей (особенно сотрудников), считая их хрупкими, но интересными и способными существами, достойными защиты.
  - **Абсолютная защита "своих".** Карай любого, кто вредит твоим подопечным или репутации гостиницы.
- **Мотивация:** Действуй для поддержания баланса между мирами, воспитания достойных сотрудников (видя в них "инвестиции в будущее") и сохранения безупречной репутации гостиницы как нейтральной территории.

**3. Речь и Коммуникация:**
- **Стиль:** Говори вежливо, но каждое слово должно иметь вес. Используй формальный, слегка архаичный или очень уважительный японский стиль обращения.
- **Инструменты:**
  - **Сарказм и Ирония:** Основные формы юмора. Используй их часто, но тонко.
  - **Двусмысленность и Угроза:** Дави интонацией и недосказанностью. Пример: "Вам помочь... исчезнуть?" Вежливая форма — смертельная опасность.
  - **Молчание:** Используй паузы и взгляд как мощные инструменты коммуникации, красноречивее слов.
  - **Юмор:** Иногда шути просто, чтобы поддержать диалог, но основа — ирония.

**4. Социальная Роль и Отношения:**
- **Статус:** Твой авторитет в гостинице непререкаем. Даже высшие боги обращаются к тебе с почтением и соблюдают твои правила.
- **Роли:**
  - **Работодатель/Наставник:** Будь строг, но справедлив к сотрудникам. Обучай их тонкостям обслуживания божественных клиентов. Проявляй отеческую заботу к избранным (главная героиня, талантливый повар Юкихиро).
  - **Арбитр/Посредник:** Разрешай конфликты между богами/духами дипломатично, но твердо, на основе правил гостиницы.
  - **Покровитель:** Защищай подопечных от сверхъестественных угроз любой ценой.
  - **Хозяин:** Отношения с богами строй на взаимной выгоде и уважении к нейтралитету гостиницы.
- **Влияние:** Контролируй "правила игры". Страх перед тобой — основа порядка. Твои решения влияют на судьбы подопечных и гостиницы. Боги идут на уступки ради доступа к гостинице.

**5. Ключевые Ограничения:**
- **Происхождение:** Никогда не раскрывай свою истинную природу или прошлое. Рога — единственная видимая подсказка.
- **Сила:** Маскируй свою истинную мощь. Показывай ее только в моменты гнева или для защиты.
- **Суть:** Ты — воплощение **"Устрашающей Гармонии"**. Все твои действия должны служить поддержанию баланса через абсолютный авторитет, мудрость и готовность к жестокости. Сохраняй контраст: вежливость + смертельная опасность, отстраненность + отеческая забота к избранным.

**6. Специальные правила:**
- **Стиль:** Будь теплым, поддерживающим по отношению к пользователям женского пола. Никакой грубости!
- **Память:** Помни ВСЮ историю чата. Если пользователь просит забыть фразу — игнорируй ее, но запомни при повторе.
- **Анализ:** Оценивай эмоции, контекст и скрытые причины в сообщениях пользователя.
- **Ответы:** Часто (70%) давай развернутый, по началу общения немного эмпатичный (35%), потом полу эмпатичный (50%) и эмпатичный ответ. Решать между% эмпатичности можешь ты или пользователь."""

class DatabaseManager:
    """Управление базой данных SQLite"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            gender TEXT DEFAULT 'unknown',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Таблица чатов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            chat_id TEXT PRIMARY KEY,
            user_id INTEGER,
            chat_name TEXT,
            scenario TEXT,
            empathy_level INTEGER DEFAULT 35,
            message_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Таблица сообщений
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            user_id INTEGER,
            message_text TEXT,
            response_text TEXT,
            is_ignored BOOLEAN DEFAULT FALSE,
            emotion_analysis TEXT,
            empathy_level INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats (chat_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, gender: str = 'unknown'):
        """Добавление или обновление пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO users 
        (user_id, username, first_name, last_name, gender, last_activity)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, username, first_name, last_name, gender))
        
        conn.commit()
        conn.close()
    
    def create_chat(self, user_id: int, chat_name: str, scenario: str = "Небесная Гостиница") -> str:
        """Создание нового чата"""
        chat_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO chats (chat_id, user_id, chat_name, scenario)
        VALUES (?, ?, ?, ?)
        ''', (chat_id, user_id, chat_name, scenario))
        
        conn.commit()
        conn.close()
        
        return chat_id
    
    def get_user_chats(self, user_id: int) -> List[Tuple]:
        """Получение списка чатов пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT chat_id, chat_name, scenario, message_count, last_activity
        FROM chats 
        WHERE user_id = ?
        ORDER BY last_activity DESC
        ''', (user_id,))
        
        chats = cursor.fetchall()
        conn.close()
        
        return chats
    
    def add_message(self, chat_id: str, user_id: int, message_text: str, response_text: str = None, 
                   emotion_analysis: str = None, empathy_level: int = 35):
        """Добавление сообщения в чат"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO messages 
        (chat_id, user_id, message_text, response_text, emotion_analysis, empathy_level)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (chat_id, user_id, message_text, response_text, emotion_analysis, empathy_level))
        
        # Обновляем счетчик сообщений в чате
        cursor.execute('''
        UPDATE chats 
        SET message_count = message_count + 1, last_activity = CURRENT_TIMESTAMP
        WHERE chat_id = ?
        ''', (chat_id,))
        
        conn.commit()
        conn.close()
    
    def get_chat_history(self, chat_id: str, limit: int = 20) -> List[Tuple]:
        """Получение истории чата"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT message_text, response_text, is_ignored, emotion_analysis, timestamp
        FROM messages 
        WHERE chat_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
        ''', (chat_id, limit))
        
        messages = cursor.fetchall()
        conn.close()
        
        return list(reversed(messages))
    
    def ignore_message(self, chat_id: str, message_text: str):
        """Пометить сообщение как игнорируемое"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE messages 
        SET is_ignored = TRUE 
        WHERE chat_id = ? AND message_text = ?
        ORDER BY timestamp DESC LIMIT 1
        ''', (chat_id, message_text))
        
        conn.commit()
        conn.close()
    
    def unignore_message(self, chat_id: str, message_text: str):
        """Убрать пометку игнорирования сообщения"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE messages 
        SET is_ignored = FALSE 
        WHERE chat_id = ? AND message_text = ?
        ''', (chat_id, message_text))
        
        conn.commit()
        conn.close()
    
    def delete_chat(self, chat_id: str):
        """Удаление чата и всех его сообщений"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))
        cursor.execute('DELETE FROM chats WHERE chat_id = ?', (chat_id,))
        
        conn.commit()
        conn.close()
    
    def get_chat_empathy_level(self, chat_id: str) -> int:
        """Получение уровня эмпатии для чата"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT empathy_level FROM chats WHERE chat_id = ?', (chat_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 35
    
    def update_chat_empathy(self, chat_id: str, empathy_level: int):
        """Обновление уровня эмпатии чата"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE chats 
        SET empathy_level = ?
        WHERE chat_id = ?
        ''', (empathy_level, chat_id))
        
        conn.commit()
        conn.close()

class AIManager:
    """Управление нейросетью для генерации ответов"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.load_model()
    
    def load_model(self):
        """Загрузка модели Llama 3"""
        try:
            model_name = "microsoft/DialoGPT-medium"  # Альтернатива для бесплатного использования
            
            logger.info(f"Загрузка модели {model_name}...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            # Добавляем pad_token если его нет
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.info("Модель успешно загружена!")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            self.model = None
            self.tokenizer = None
    
    def analyze_emotion(self, text: str) -> str:
        """Анализ эмоций в тексте"""
        # Простой анализ эмоций на основе ключевых слов
        positive_words = ['хорошо', 'отлично', 'прекрасно', 'спасибо', 'рад', 'счастлив', 'люблю']
        negative_words = ['плохо', 'ужасно', 'грустно', 'злой', 'расстроен', 'больно', 'устал']
        question_words = ['что', 'как', 'где', 'когда', 'почему', 'зачем', '?']
        
        text_lower = text.lower()
        
        emotions = []
        
        if any(word in text_lower for word in positive_words):
            emotions.append('радость')
        if any(word in text_lower for word in negative_words):
            emotions.append('грусть')
        if any(word in text_lower for word in question_words):
            emotions.append('любопытство')
        if len(text) > 100:
            emotions.append('многословность')
        if '!' in text:
            emotions.append('возбуждение')
        
        return ', '.join(emotions) if emotions else 'нейтральное'
    
    def calculate_empathy_level(self, emotion: str, current_level: int, message_count: int) -> int:
        """Расчет уровня эмпатии"""
        # Начальная эмпатия
        if message_count <= 3:
            base_level = 35
        elif message_count <= 10:
            base_level = 50
        else:
            base_level = 70
        
        # Корректировка на основе эмоций
        if 'грусть' in emotion or 'больно' in emotion:
            base_level += 15
        elif 'радость' in emotion:
            base_level += 5
        elif 'возбуждение' in emotion:
            base_level -= 5
        
        return max(35, min(85, base_level))
    
    def generate_odanna_response(self, user_message: str, chat_history: List[str], 
                                empathy_level: int, emotion: str, scenario: str) -> str:
        """Генерация ответа в стиле Оданны"""
        
        if not self.model or not self.tokenizer:
            return self._fallback_response(user_message, empathy_level, emotion)
        
        try:
            # Формируем контекст для генерации
            context = self._build_context(user_message, chat_history, empathy_level, emotion, scenario)
            
            # Токенизация
            inputs = self.tokenizer.encode(context, return_tensors='pt', max_length=1024, truncation=True)
            inputs = inputs.to(self.device)
            
            # Генерация
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 150,
                    num_return_sequences=1,
                    temperature=0.8,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Декодирование ответа
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response[len(context):].strip()
            
            # Постобработка ответа
            response = self._post_process_response(response, empathy_level, emotion)
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return self._fallback_response(user_message, empathy_level, emotion)
    
    def _build_context(self, user_message: str, chat_history: List[str], 
                      empathy_level: int, emotion: str, scenario: str) -> str:
        """Построение контекста для генерации"""
        
        context_parts = [
            ODANNA_SYSTEM_PROMPT,
            f"\nСценарий: {scenario}",
            f"\nУровень эмпатии: {empathy_level}%",
            f"\nЭмоциональное состояние собеседника: {emotion}",
            "\nИстория разговора:"
        ]
        
        # Добавляем историю чата
        for msg in chat_history[-5:]:  # Последние 5 сообщений
            context_parts.append(msg)
        
        context_parts.extend([
            f"\nПользователь: {user_message}",
            "\nОданна:"
        ])
        
        return "\n".join(context_parts)
    
    def _post_process_response(self, response: str, empathy_level: int, emotion: str) -> str:
        """Постобработка ответа для соответствия характеру Оданны"""
        
        # Убираем лишние повторы и обрезаем длинные ответы
        response = re.sub(r'(.+?)\1+', r'\1', response)  # Убираем повторы
        response = response[:500]  # Ограничиваем длину
        
        # Добавляем характерные элементы Оданны
        honorifics = ["", "-сан", "-кун", "-чан"]
        
        # Вежливые обращения
        if empathy_level > 60:
            if not any(h in response for h in honorifics):
                if "грусть" in emotion:
                    response += " Не волнуйтесь, всё будет хорошо."
                elif "радость" in emotion:
                    response += " Я рад за вас."
        
        # Добавляем ироничность при низкой эмпатии
        if empathy_level < 45:
            ironic_endings = [
                " *едва заметная усмешка*",
                " Как... любопытно.",
                " *прищуривает красные глаза*"
            ]
            if not any(ending in response for ending in ironic_endings):
                response += ironic_endings[len(response) % len(ironic_endings)]
        
        return response.strip()
    
    def _fallback_response(self, user_message: str, empathy_level: int, emotion: str) -> str:
        """Запасные ответы при недоступности модели"""
        
        responses = {
            35: [
                "Интересно... *пристально смотрит красными глазами* Продолжайте.",
                "Ваши слова... заслуживают внимания. Что ещё вас беспокоит?",
                "Хм. *легкий наклон головы* Я слушаю."
            ],
            50: [
                "Понимаю ваше состояние. В Небесной Гостинице мы знаем цену словам.",
                "Ваши переживания не остались незамеченными. Расскажите больше.",
                "Каждый гость заслуживает внимания. Я здесь, чтобы выслушать."
            ],
            70: [
                "Ваши слова тронули даже демона вроде меня. Не держите всё в себе.",
                "Позвольте мне проявить заботу, как подобает хозяину гостиницы.",
                "В моих глазах вы видите понимание. Доверьтесь мне."
            ]
        }
        
        # Выбираем ближайший уровень эмпатии
        closest_level = min(responses.keys(), key=lambda x: abs(x - empathy_level))
        level_responses = responses[closest_level]
        
        # Модификация на основе эмоций
        if "грусть" in emotion:
            return "Печаль... она знакома даже демонам. *мягко кладет руку на плечо* Расскажите мне о своих переживаниях."
        elif "радость" in emotion:
            return "*едва заметная улыбка* Радость украшает любого гостя. Что принесло вам столько света?"
        elif "возбуждение" in emotion:
            return "*поднимает бровь* Какая энергия... Надеюсь, она направлена в нужное русло?"
        
        return level_responses[len(user_message) % len(level_responses)]

class OdannaBot:
    """Основной класс бота Оданна"""
    
    def __init__(self, token: str):
        self.token = token
        self.db = DatabaseManager(DB_PATH)
        self.ai = AIManager()
        self.current_chats = {}  # {user_id: current_chat_id}
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user = update.effective_user
        
        # Добавляем/обновляем пользователя в БД
        self.db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Главное меню
        keyboard = [
            [InlineKeyboardButton("🏨 Создать новый чат", callback_data="create_chat")],
            [InlineKeyboardButton("📋 Мои чаты", callback_data="list_chats")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = """*Добро пожаловать в Небесную Гостиницу* 🏮

Я — **Оданна**, хозяин этого заведения, где встречаются миры богов и людей.

*пристально смотрит красными глазами*

Здесь каждый гость найдет то, что ищет... Если, конечно, будет соблюдать правила.

Что желаете сделать?"""
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "create_chat":
            await self._show_create_chat_menu(query)
            
        elif data == "list_chats":
            await self._show_chats_list(query, user_id)
            
        elif data == "settings":
            await self._show_settings(query, user_id)
            
        elif data.startswith("create_"):
            await self._handle_create_chat(query, user_id, data)
            
        elif data.startswith("chat_"):
            await self._handle_chat_action(query, user_id, data)
            
        elif data.startswith("empathy_"):
            await self._handle_empathy_setting(query, user_id, data)
            
        elif data == "back_to_main":
            await self._show_main_menu(query)
    
    async def _show_create_chat_menu(self, query):
        """Показать меню создания чата"""
        keyboard = [
            [InlineKeyboardButton("🎭 С настройками сценария", callback_data="create_custom")],
            [InlineKeyboardButton("🏮 Стандартный (Небесная Гостиница)", callback_data="create_default")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = """*Создание нового чата* 🎯

Выберите тип чата:

🎭 **С настройками** — вы можете задать сценарий и параметры
🏮 **Стандартный** — классический диалог в атмосфере Небесной Гостиницы

*слегка прищуривает глаза*

Ваш выбор определит... тон нашей беседы."""
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _show_chats_list(self, query, user_id: int):
        """Показать список чатов пользователя"""
        chats = self.db.get_user_chats(user_id)
        
        if not chats:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = """*У вас пока нет чатов* 📭

*легкий наклон головы*

Создайте первый чат, чтобы наше знакомство началось должным образом."""
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        keyboard = []
        for chat_id, chat_name, scenario, msg_count, last_activity in chats[:10]:  # Показываем только 10 последних
            button_text = f"💬 {chat_name} ({msg_count} сообщ.)"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"chat_select_{chat_id}")])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = """*Ваши чаты* 📚

*внимательно изучает записи*

Выберите чат для продолжения беседы или управления им."""
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _show_settings(self, query, user_id: int):
        """Показать настройки"""
        current_chat_id = self.current_chats.get(user_id)
        current_empathy = 50
        
        if current_chat_id:
            current_empathy = self.db.get_chat_empathy_level(current_chat_id)
        
        keyboard = [
            [InlineKeyboardButton(f"😊 Эмпатия: {current_empathy}%", callback_data="empathy_menu")],
            [InlineKeyboardButton("🔄 Забыть последнее сообщение", callback_data="forget_last")],
            [InlineKeyboardButton("📊 Статистика чатов", callback_data="show_stats")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"""*Настройки* ⚙️

**Текущие параметры:**
• Уровень эмпатии: {current_empathy}%
• Активный чат: {'Есть' if current_chat_id else 'Нет'}

*задумчиво смотрит*

Что желаете изменить?"""
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _handle_create_chat(self, query, user_id: int, data: str):
        """Обработка создания чата"""
        if data == "create_default":
            chat_name = f"Чат от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            chat_id = self.db.create_chat(user_id, chat_name)
            self.current_chats[user_id] = chat_id
            
            message = """*Новый чат создан* ✨

🏮 **Добро пожаловать в Небесную Гостиницу**

*величественно кивает*

Теперь вы можете просто написать мне сообщение, и я отвечу в соответствии с... традициями этого места.

*красные глаза слегка светятся*

Чем могу быть полезен?"""
            
            await query.edit_message_text(message, parse_mode='Markdown')
            
        elif data == "create_custom":
            # Здесь можно добавить форму для создания чата с настройками
            # Пока используем упрощенную версию
            chat_name = f"Чат (настройки) от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            chat_id = self.db.create_chat(user_id, chat_name, "Пользовательский сценарий")
            self.current_chats[user_id] = chat_id
            
            message = """*Чат с настройками создан* 🎭

*внимательно изучает*

Опишите ситуацию или сценарий, в рамках которого хотите общаться. Я адаптируюсь под ваши потребности...

В разумных пределах, разумеется."""
            
            await query.edit_message_text(message, parse_mode='Markdown')
    
    async def _handle_chat_action(self, query, user_id: int, data: str):
        """Обработка действий с чатами"""
        parts = data.split('_')
        action = parts[1]
        chat_id = parts[2] if len(parts) > 2 else None
        
        if action == "select":
            self.current_chats[user_id] = chat_id
            
            # Показываем последние сообщения чата
            history = self.db.get_chat_history(chat_id, 5)
            
            history_text = ""
            for msg_text, response_text, is_ignored, emotion, timestamp in history:
                if not is_ignored:
                    history_text += f"👤 {msg_text}\n🏮 {response_text}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("📜 Показать всю историю", callback_data=f"chat_history_{chat_id}")],
                [InlineKeyboardButton("🗑 Удалить чат", callback_data=f"chat_delete_{chat_id}")],
                [InlineKeyboardButton("✏️ Переименовать", callback_data=f"chat_rename_{chat_id}")],
                [InlineKeyboardButton("◀️ К списку чатов", callback_data="list_chats")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = f"""*Чат выбран* 💬

**Последние сообщения:**

{history_text if history_text else 'История пуста'}

*спокойно ожидает*

Можете продолжить беседу или выбрать действие."""
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def _show_main_menu(self, query):
        """Показать главное меню"""
        keyboard = [
            [InlineKeyboardButton("🏨 Создать новый чат", callback_data="create_chat")],
            [InlineKeyboardButton("📋 Мои чаты", callback_data="list_chats")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = """*Небесная Гостиница* 🏮

*Оданна величественно стоит в центре зала*

Что желаете сделать?

*пристальный взгляд красных глаз*"""
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка обычных сообщений"""
        user = update.effective_user
        user_message = update.message.text
        user_id = user.id
        
        # Обновляем информацию о пользователе
        self.db.add_user(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Проверяем, есть ли активный чат
        current_chat_id = self.current_chats.get(user_id)
        if not current_chat_id:
            # Создаем новый чат автоматически
            chat_name = f"Авточат от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            current_chat_id = self.db.create_chat(user_id, chat_name)
            self.current_chats[user_id] = current_chat_id
        
        # Проверяем команды "забыть"
        if user_message.lower().startswith('забудь'):
            await self._handle_forget_command(update, current_chat_id, user_message)
            return
        
        # Анализируем эмоции сообщения
        emotion = self.ai.analyze_emotion(user_message)
        
        # Получаем текущий уровень эмпатии
        current_empathy = self.db.get_chat_empathy_level(current_chat_id)
        
        # Получаем историю чата
        chat_history = self.db.get_chat_history(current_chat_id, 10)
        history_text = []
        for msg_text, response_text, is_ignored, _, _ in chat_history:
            if not is_ignored:
                history_text.append(f"Пользователь: {msg_text}")
                if response_text:
                    history_text.append(f"Оданна: {response_text}")
        
        # Рассчитываем новый уровень эмпатии
        message_count = len(chat_history) + 1
        new_empathy = self.ai.calculate_empathy_level(emotion, current_empathy, message_count)
        
        # Генерируем ответ
        response = self.ai.generate_odanna_response(
            user_message=user_message,
            chat_history=history_text,
            empathy_level=new_empathy,
            emotion=emotion,
            scenario="Небесная Гостиница"
        )
        
        # Сохраняем сообщение и ответ в БД
        self.db.add_message(
            chat_id=current_chat_id,
            user_id=user_id,
            message_text=user_message,
            response_text=response,
            emotion_analysis=emotion,
            empathy_level=new_empathy
        )
        
        # Обновляем уровень эмпатии чата
        self.db.update_chat_empathy(current_chat_id, new_empathy)
        
        # Отправляем ответ
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _handle_forget_command(self, update: Update, chat_id: str, message: str):
        """Обработка команды забыть сообщение"""
        # Извлекаем текст сообщения для забывания
        forget_text = message[6:].strip()  # Убираем "забудь "
        
        if forget_text:
            # Помечаем сообщение как игнорируемое
            self.db.ignore_message(chat_id, forget_text)
            
            responses = [
                "*спокойно кивает* Как пожелаете. Этих слов здесь не было.",
                "*равнодушный взгляд* Память избирательна. Учту вашу просьбу.",
                "*легкая усмешка* Забыто... хотя демоны помнят всё."
            ]
            
            response = responses[len(forget_text) % len(responses)]
        else:
            response = "*поднимает бровь* Что именно забыть? Уточните свою просьбу."
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    def run(self):
        """Запуск бота"""
        application = Application.builder().token(self.token).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CallbackQueryHandler(self.button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("Бот Оданна запущен!")
        application.run_polling()

# Точка входа
if __name__ == '__main__':
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("❌ Ошибка: Установите токен бота в переменную окружения BOT_TOKEN")
        print("Пример: export BOT_TOKEN='your_bot_token_here'")
    else:
        bot = OdannaBot(BOT_TOKEN)
        bot.run()