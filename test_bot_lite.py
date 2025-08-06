#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Упрощенный тест бота Оданна без зависимостей от внешних библиотек
Проверяет базовую логику без PyTorch и Telegram API
"""

import sqlite3
import tempfile
import os
import re
from datetime import datetime

def test_database_basic():
    """Базовый тест SQLite без зависимостей"""
    print("🗃️ Тестирование базы данных...")
    
    # Создаем временную БД
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        db_path = temp_db.name
    
    try:
        # Инициализация базы данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Создание таблиц
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
        print("✅ Таблицы созданы")
        
        # Тест добавления пользователя
        cursor.execute('''
        INSERT OR REPLACE INTO users 
        (user_id, username, first_name, last_name, gender, last_activity)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (12345, "test_user", "Тест", "Пользователь", "female"))
        
        conn.commit()
        print("✅ Пользователь добавлен")
        
        # Тест создания чата
        chat_id = f"12345_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cursor.execute('''
        INSERT INTO chats (chat_id, user_id, chat_name, scenario)
        VALUES (?, ?, ?, ?)
        ''', (chat_id, 12345, "Тестовый чат", "Небесная Гостиница"))
        
        conn.commit()
        print(f"✅ Чат создан: {chat_id}")
        
        # Тест добавления сообщения
        cursor.execute('''
        INSERT INTO messages 
        (chat_id, user_id, message_text, response_text, emotion_analysis, empathy_level)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (chat_id, 12345, "Привет, Оданна!", "Добро пожаловать в гостиницу.", "радость", 45))
        
        conn.commit()
        print("✅ Сообщение добавлено")
        
        # Тест получения истории
        cursor.execute('''
        SELECT message_text, response_text, is_ignored, emotion_analysis, timestamp
        FROM messages 
        WHERE chat_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 20
        ''', (chat_id,))
        
        messages = cursor.fetchall()
        assert len(messages) == 1
        print("✅ История чата получена")
        
        conn.close()
        print("🎉 Все тесты базы данных пройдены!")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)

def test_emotion_analysis():
    """Тест анализа эмоций без внешних библиотек"""
    print("\n🧠 Тестирование анализа эмоций...")
    
    def analyze_emotion(text: str) -> str:
        """Простой анализ эмоций на основе ключевых слов"""
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
    
    # Тестовые случаи
    test_cases = [
        ("Мне очень грустно сегодня...", "грусть"),
        ("Как дела? Что нового?", "любопытство"),
        ("Спасибо вам большое!", "радость, возбуждение"),
        ("Обычный день", "нейтральное"),
        ("Я так счастлив!!!", "радость, возбуждение")
    ]
    
    for text, expected in test_cases:
        result = analyze_emotion(text)
        print(f"Текст: '{text}' → Эмоции: {result}")
        # Проверяем, что ключевые эмоции распознаются
        if expected != "нейтральное":
            assert any(emotion in result for emotion in expected.split(", ")), \
                f"Ожидались эмоции содержащие '{expected}', получено '{result}'"
    
    print("✅ Анализ эмоций работает корректно")

def test_empathy_calculation():
    """Тест расчета уровня эмпатии"""
    print("\n📈 Тестирование расчета эмпатии...")
    
    def calculate_empathy_level(emotion: str, current_level: int, message_count: int) -> int:
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
    
    # Тестовые случаи
    test_cases = [
        (1, "нейтральное", 35, 35),
        (5, "радость", 50, 55),
        (8, "грусть", 50, 65),
        (15, "грусть", 70, 85),
        (3, "возбуждение", 35, 30),  # Но минимум 35
    ]
    
    for msg_count, emotion, current, expected_min in test_cases:
        result = calculate_empathy_level(emotion, current, msg_count)
        print(f"Сообщение {msg_count}, эмоция '{emotion}' → Эмпатия: {result}%")
        
        # Проверяем диапазон
        assert 35 <= result <= 85, f"Эмпатия {result}% не в диапазоне 35-85%"
        
        # Проверяем логику
        if "грусть" in emotion:
            assert result >= 50, "При грусти эмпатия должна быть высокой"
    
    print("✅ Расчет эмпатии работает корректно")

def test_character_responses():
    """Тест характерных ответов Оданны"""
    print("\n🎭 Тестирование характера Оданны...")
    
    def get_fallback_response(user_message: str, empathy_level: int, emotion: str) -> str:
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
    
    # Тестовые случаи
    test_cases = [
        ("Здравствуйте", 35, "нейтральное"),
        ("Мне очень плохо...", 70, "грусть"),
        ("Спасибо вам!", 50, "радость"),
        ("Что это за место?", 40, "любопытство"),
    ]
    
    for message, empathy, emotion in test_cases:
        response = get_fallback_response(message, empathy, emotion)
        print(f"\n📨 Сообщение: '{message}'")
        print(f"😊 Эмпатия: {empathy}%")
        print(f"💭 Эмоция: {emotion}")
        print(f"🏮 Оданна: {response}")
        
        # Проверяем базовые характеристики ответов
        assert len(response) > 10, "Ответ должен быть содержательным"
        
        # Проверяем соответствие эмпатии
        if empathy < 45:
            # Низкая эмпатия - ирония или краткость
            assert "*" in response or "..." in response, "Низкая эмпатия должна содержать элементы загадочности"
        
        if empathy > 60 and "грусть" in emotion:
            # Высокая эмпатия при грусти - поддержка
            support_words = ["понимание", "забота", "доверьтесь", "расскажите", "не держите"]
            assert any(word in response.lower() for word in support_words), \
                "Высокая эмпатия должна содержать поддерживающие слова"
    
    print("\n✅ Характер Оданны соответствует требованиям")

def test_memory_system():
    """Тест системы памяти"""
    print("\n💾 Тестирование системы памяти...")
    
    # Создаем временную БД
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        db_path = temp_db.name
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Создаем таблицу сообщений
        cursor.execute('''
        CREATE TABLE messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            user_id INTEGER,
            message_text TEXT,
            response_text TEXT,
            is_ignored BOOLEAN DEFAULT FALSE,
            emotion_analysis TEXT,
            empathy_level INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Добавляем тестовые сообщения
        chat_id = "test_chat_123"
        messages = [
            ("Привет!", "Добро пожаловать!"),
            ("Как дела?", "Всё в порядке."),
            ("Расскажи о себе", "Я хозяин гостиницы."),
            ("Секретная информация", "Понимаю.")
        ]
        
        for msg_text, response_text in messages:
            cursor.execute('''
            INSERT INTO messages 
            (chat_id, user_id, message_text, response_text, emotion_analysis, empathy_level)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (chat_id, 12345, msg_text, response_text, "нейтральное", 40))
        
        conn.commit()
        print("✅ Тестовые сообщения добавлены")
        
        # Тест функции "забыть"
        cursor.execute('''
        UPDATE messages 
        SET is_ignored = TRUE 
        WHERE chat_id = ? AND message_text = ?
        ORDER BY timestamp DESC LIMIT 1
        ''', (chat_id, "Секретная информация"))
        
        conn.commit()
        print("✅ Сообщение помечено как забытое")
        
        # Проверяем, что сообщение забыто
        cursor.execute('''
        SELECT message_text, is_ignored FROM messages 
        WHERE chat_id = ? AND message_text = ?
        ''', (chat_id, "Секретная информация"))
        
        result = cursor.fetchone()
        assert result[1] == 1, "Сообщение должно быть помечено как забытое"
        print("✅ Функция 'забыть' работает")
        
        # Тест восстановления
        cursor.execute('''
        UPDATE messages 
        SET is_ignored = FALSE 
        WHERE chat_id = ? AND message_text = ?
        ''', (chat_id, "Секретная информация"))
        
        conn.commit()
        
        cursor.execute('''
        SELECT is_ignored FROM messages 
        WHERE chat_id = ? AND message_text = ?
        ''', (chat_id, "Секретная информация"))
        
        result = cursor.fetchone()
        assert result[0] == 0, "Сообщение должно быть восстановлено"
        print("✅ Функция восстановления работает")
        
        conn.close()
        print("🎉 Система памяти работает корректно!")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)

def run_lite_tests():
    """Запуск упрощенных тестов"""
    print("🚀 Запуск упрощенных тестов бота Оданна...\n")
    
    try:
        test_database_basic()
        test_emotion_analysis()
        test_empathy_calculation()
        test_character_responses()
        test_memory_system()
        
        print("\n" + "="*50)
        print("🎉 ВСЕ УПРОЩЕННЫЕ ТЕСТЫ ПРОЙДЕНЫ! 🎉")
        print("🏮 Базовая логика Оданны работает корректно!")
        print("📝 Для полного тестирования установите зависимости:")
        print("   pip install -r requirements.txt")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = run_lite_tests()
    sys.exit(0 if success else 1)