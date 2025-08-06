import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from config import DATABASE_PATH

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица пользователей
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                # Таблица чатов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chats (
                        chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        title TEXT,
                        scenario TEXT DEFAULT 'anime',
                        settings TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                # Таблица сообщений
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER,
                        user_id INTEGER,
                        text TEXT,
                        is_from_user BOOLEAN,
                        is_ignored BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (chat_id) REFERENCES chats (chat_id),
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                # Таблица настроек чатов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chat_settings (
                        chat_id INTEGER PRIMARY KEY,
                        empathy_level INTEGER DEFAULT 50,
                        response_length TEXT DEFAULT 'medium',
                        personality_traits TEXT DEFAULT '{}',
                        FOREIGN KEY (chat_id) REFERENCES chats (chat_id)
                    )
                ''')
                
                conn.commit()
                logger.info("База данных инициализирована успешно")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        """Добавление нового пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, username, first_name, last_name))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение информации о пользователе"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, username, first_name, last_name, created_at, is_active
                    FROM users WHERE user_id = ?
                ''', (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'user_id': row[0],
                        'username': row[1],
                        'first_name': row[2],
                        'last_name': row[3],
                        'created_at': row[4],
                        'is_active': bool(row[5])
                    }
                return None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None
    
    def create_chat(self, user_id: int, title: str, scenario: str = 'anime', settings: Dict = None) -> Optional[int]:
        """Создание нового чата"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                settings_json = json.dumps(settings or {})
                
                cursor.execute('''
                    INSERT INTO chats (user_id, title, scenario, settings)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, title, scenario, settings_json))
                
                chat_id = cursor.lastrowid
                
                # Создание настроек чата
                cursor.execute('''
                    INSERT INTO chat_settings (chat_id, empathy_level, response_length, personality_traits)
                    VALUES (?, ?, ?, ?)
                ''', (chat_id, 50, 'medium', '{}'))
                
                conn.commit()
                return chat_id
        except Exception as e:
            logger.error(f"Ошибка создания чата: {e}")
            return None
    
    def get_user_chats(self, user_id: int) -> List[Dict]:
        """Получение всех чатов пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT chat_id, title, scenario, created_at, updated_at, is_active
                    FROM chats WHERE user_id = ? AND is_active = TRUE
                    ORDER BY updated_at DESC
                ''', (user_id,))
                
                chats = []
                for row in cursor.fetchall():
                    chats.append({
                        'chat_id': row[0],
                        'title': row[1],
                        'scenario': row[2],
                        'created_at': row[3],
                        'updated_at': row[4],
                        'is_active': bool(row[5])
                    })
                return chats
        except Exception as e:
            logger.error(f"Ошибка получения чатов пользователя: {e}")
            return []
    
    def get_chat(self, chat_id: int) -> Optional[Dict]:
        """Получение информации о чате"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT chat_id, user_id, title, scenario, settings, created_at, updated_at, is_active
                    FROM chats WHERE chat_id = ?
                ''', (chat_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'chat_id': row[0],
                        'user_id': row[1],
                        'title': row[2],
                        'scenario': row[3],
                        'settings': json.loads(row[4]),
                        'created_at': row[5],
                        'updated_at': row[6],
                        'is_active': bool(row[7])
                    }
                return None
        except Exception as e:
            logger.error(f"Ошибка получения чата: {e}")
            return None
    
    def add_message(self, chat_id: int, user_id: int, text: str, is_from_user: bool) -> bool:
        """Добавление сообщения в чат"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO messages (chat_id, user_id, text, is_from_user)
                    VALUES (?, ?, ?, ?)
                ''', (chat_id, user_id, text, is_from_user))
                
                # Обновление времени последнего сообщения в чате
                cursor.execute('''
                    UPDATE chats SET updated_at = CURRENT_TIMESTAMP
                    WHERE chat_id = ?
                ''', (chat_id,))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления сообщения: {e}")
            return False
    
    def get_chat_messages(self, chat_id: int, limit: int = 20, offset: int = 0) -> List[Dict]:
        """Получение сообщений чата"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT message_id, user_id, text, is_from_user, is_ignored, created_at
                    FROM messages 
                    WHERE chat_id = ? AND is_ignored = FALSE
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (chat_id, limit, offset))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append({
                        'message_id': row[0],
                        'user_id': row[1],
                        'text': row[2],
                        'is_from_user': bool(row[3]),
                        'is_ignored': bool(row[4]),
                        'created_at': row[5]
                    })
                return messages[::-1]  # Возвращаем в хронологическом порядке
        except Exception as e:
            logger.error(f"Ошибка получения сообщений чата: {e}")
            return []
    
    def get_all_chat_messages(self, chat_id: int) -> List[Dict]:
        """Получение всех сообщений чата для контекста"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT message_id, user_id, text, is_from_user, is_ignored, created_at
                    FROM messages 
                    WHERE chat_id = ? AND is_ignored = FALSE
                    ORDER BY created_at ASC
                ''', (chat_id,))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append({
                        'message_id': row[0],
                        'user_id': row[1],
                        'text': row[2],
                        'is_from_user': bool(row[3]),
                        'is_ignored': bool(row[4]),
                        'created_at': row[5]
                    })
                return messages
        except Exception as e:
            logger.error(f"Ошибка получения всех сообщений чата: {e}")
            return []
    
    def mark_message_ignored(self, message_id: int) -> bool:
        """Пометка сообщения как игнорируемого"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE messages SET is_ignored = TRUE
                    WHERE message_id = ?
                ''', (message_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка пометки сообщения как игнорируемого: {e}")
            return False
    
    def unmark_message_ignored(self, text: str, chat_id: int) -> bool:
        """Снятие пометки игнорирования с сообщения при повторной отправке"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE messages SET is_ignored = FALSE
                    WHERE text = ? AND chat_id = ? AND is_ignored = TRUE
                ''', (text, chat_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка снятия пометки игнорирования: {e}")
            return False
    
    def update_chat_title(self, chat_id: int, new_title: str) -> bool:
        """Обновление названия чата"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE chats SET title = ?
                    WHERE chat_id = ?
                ''', (new_title, chat_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка обновления названия чата: {e}")
            return False
    
    def delete_chat(self, chat_id: int) -> bool:
        """Удаление чата (мягкое удаление)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE chats SET is_active = FALSE
                    WHERE chat_id = ?
                ''', (chat_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка удаления чата: {e}")
            return False
    
    def get_chat_settings(self, chat_id: int) -> Optional[Dict]:
        """Получение настроек чата"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT empathy_level, response_length, personality_traits
                    FROM chat_settings WHERE chat_id = ?
                ''', (chat_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'empathy_level': row[0],
                        'response_length': row[1],
                        'personality_traits': json.loads(row[2])
                    }
                return None
        except Exception as e:
            logger.error(f"Ошибка получения настроек чата: {e}")
            return None
    
    def update_chat_settings(self, chat_id: int, settings: Dict) -> bool:
        """Обновление настроек чата"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE chat_settings 
                    SET empathy_level = ?, response_length = ?, personality_traits = ?
                    WHERE chat_id = ?
                ''', (
                    settings.get('empathy_level', 50),
                    settings.get('response_length', 'medium'),
                    json.dumps(settings.get('personality_traits', {})),
                    chat_id
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка обновления настроек чата: {e}")
            return False
    
    def get_chat_summary(self, chat_id: int) -> str:
        """Генерация краткого описания чата"""
        try:
            messages = self.get_all_chat_messages(chat_id)
            if not messages:
                return "Пустой чат"
            
            # Анализ ключевых тем и событий
            user_messages = [msg['text'] for msg in messages if msg['is_from_user']]
            bot_messages = [msg['text'] for msg in messages if not msg['is_from_user']]
            
            # Простая суммаризация на основе частоты слов
            all_text = ' '.join(user_messages).lower()
            words = all_text.split()
            
            # Подсчет частоты слов (исключая стоп-слова)
            stop_words = {'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'у', 'о', 'об', 'а', 'но', 'или', 'что', 'как', 'где', 'когда', 'почему', 'зачем'}
            word_freq = {}
            for word in words:
                if len(word) > 3 and word not in stop_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Топ-5 самых частых слов
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            
            summary = f"Чат с {len(messages)} сообщениями"
            if top_words:
                summary += f". Ключевые темы: {', '.join([word for word, _ in top_words])}"
            
            return summary
            
        except Exception as e:
            logger.error(f"Ошибка генерации описания чата: {e}")
            return "Ошибка генерации описания"
    
    def get_all_users(self) -> List[Dict]:
        """Получение всех пользователей"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, username, first_name, last_name, created_at, is_active
                    FROM users WHERE is_active = TRUE
                    ORDER BY created_at DESC
                ''')
                
                users = []
                for row in cursor.fetchall():
                    users.append({
                        'user_id': row[0],
                        'username': row[1],
                        'first_name': row[2],
                        'last_name': row[3],
                        'created_at': row[4],
                        'is_active': bool(row[5])
                    })
                return users
        except Exception as e:
            logger.error(f"Ошибка получения всех пользователей: {e}")
            return []
    
    def get_all_chats(self) -> List[Dict]:
        """Получение всех чатов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT chat_id, user_id, title, scenario, created_at, updated_at, is_active
                    FROM chats WHERE is_active = TRUE
                    ORDER BY updated_at DESC
                ''')
                
                chats = []
                for row in cursor.fetchall():
                    chats.append({
                        'chat_id': row[0],
                        'user_id': row[1],
                        'title': row[2],
                        'scenario': row[3],
                        'created_at': row[4],
                        'updated_at': row[5],
                        'is_active': bool(row[6])
                    })
                return chats
        except Exception as e:
            logger.error(f"Ошибка получения всех чатов: {e}")
            return []
    
    def get_all_messages(self) -> List[Dict]:
        """Получение всех сообщений"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT message_id, chat_id, user_id, text, is_from_user, is_ignored, created_at
                    FROM messages WHERE is_ignored = FALSE
                    ORDER BY created_at DESC
                ''')
                
                messages = []
                for row in cursor.fetchall():
                    messages.append({
                        'message_id': row[0],
                        'chat_id': row[1],
                        'user_id': row[2],
                        'text': row[3],
                        'is_from_user': bool(row[4]),
                        'is_ignored': bool(row[5]),
                        'created_at': row[6]
                    })
                return messages
        except Exception as e:
            logger.error(f"Ошибка получения всех сообщений: {e}")
            return []