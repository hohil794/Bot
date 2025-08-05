import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import DATABASE_PATH

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
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

# Создаем глобальный экземпляр базы данных
db = Database()