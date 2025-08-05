import sqlite3
import os
from datetime import datetime
from typing import List, Tuple, Optional

class Database:
    def __init__(self, db_path: str = "bot_database.db"):
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
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица сообщений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats (chat_id)
                )
            ''')
            
            conn.commit()
    
    def add_user(self, user_id: int, username: str = None):
        """Добавление пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username)
                VALUES (?, ?)
            ''', (user_id, username))
            conn.commit()
    
    def create_chat(self, user_id: int, title: str, scenario: str = None) -> int:
        """Создание нового чата"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chats (user_id, title, scenario)
                VALUES (?, ?, ?)
            ''', (user_id, title, scenario))
            conn.commit()
            return cursor.lastrowid
    
    def get_user_chats(self, user_id: int) -> List[Tuple]:
        """Получение списка чатов пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT chat_id, title, scenario, creation_date
                FROM chats
                WHERE user_id = ?
                ORDER BY creation_date DESC
            ''', (user_id,))
            return cursor.fetchall()
    
    def get_chat_info(self, chat_id: int) -> Optional[Tuple]:
        """Получение информации о чате"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT chat_id, user_id, title, scenario, creation_date
                FROM chats
                WHERE chat_id = ?
            ''', (chat_id,))
            return cursor.fetchone()
    
    def add_message(self, chat_id: int, role: str, content: str):
        """Добавление сообщения в чат"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO messages (chat_id, role, content)
                VALUES (?, ?, ?)
            ''', (chat_id, role, content))
            conn.commit()
    
    def get_chat_messages(self, chat_id: int, limit: int = 20) -> List[Tuple]:
        """Получение последних сообщений из чата"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT role, content, timestamp
                FROM messages
                WHERE chat_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (chat_id, limit))
            messages = cursor.fetchall()
            return list(reversed(messages))  # Возвращаем в хронологическом порядке
    
    def delete_chat(self, chat_id: int, user_id: int):
        """Удаление чата"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Сначала удаляем сообщения
            cursor.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))
            # Затем удаляем чат (только если он принадлежит пользователю)
            cursor.execute('DELETE FROM chats WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
            conn.commit()
    
    def update_chat_title(self, chat_id: int, user_id: int, new_title: str):
        """Переименование чата"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE chats
                SET title = ?
                WHERE chat_id = ? AND user_id = ?
            ''', (new_title, chat_id, user_id))
            conn.commit()