#!/usr/bin/env python3
"""
Демо-версия бота Оданн для демонстрации функциональности
без необходимости настройки Telegram API
"""

import os
import sys
from datetime import datetime

# Добавляем текущую директорию в путь для импорта модулей
sys.path.append('.')

from database import db
from ai_model import ai

class OdannDemo:
    def __init__(self):
        """Инициализация демо-версии"""
        self.current_chat_id = None
        self.user_id = 12345  # Демо пользователь
        self.setup_demo_user()
    
    def setup_demo_user(self):
        """Настройка демо-пользователя"""
        db.add_user(self.user_id, "demo_user", "Demo User")
        print("🌸 Добро пожаловать в демо-версию бота Оданн! 🌸")
        print()
        print("Я Оданн, служанка и повар небесной гостиницы Цунику-ин!")
        print("Это демонстрация функциональности бота.")
        print()
    
    def show_menu(self):
        """Показ главного меню"""
        print("=" * 50)
        print("📋 ГЛАВНОЕ МЕНЮ")
        print("=" * 50)
        print("1. 💬 Создать новый чат")
        print("2. 📚 Список существующих чатов")
        print("3. 🔍 Демонстрация AI ответов")
        print("4. 📊 Статистика базы данных") 
        print("0. 🚪 Выход")
        print("=" * 50)
    
    def create_chat_menu(self):
        """Меню создания чата"""
        print("\n✨ СОЗДАНИЕ НОВОГО ЧАТА ✨")
        print("1. ⚙️  С пользовательским сценарием")
        print("2. 🎬 Без настроек (стандартный сценарий)")
        print("0. 🔙 Назад")
        
        choice = input("\nВыберите опцию: ").strip()
        
        if choice == '1':
            return self.create_custom_chat()
        elif choice == '2':
            return self.create_default_chat()
        elif choice == '0':
            return True
        else:
            print("❌ Неверный выбор!")
            return True
    
    def create_custom_chat(self):
        """Создание чата с пользовательским сценарием"""
        print("\n📝 Создание чата с настройками")
        print("Опишите сценарий для общения с Оданн:")
        print("• Где происходит действие?")
        print("• Какая ситуация?")
        print("• Какую роль играете вы?")
        print()
        
        scenario = input("Введите сценарий: ").strip()
        if not scenario:
            print("❌ Сценарий не может быть пустым!")
            return True
        
        title = f"Чат: {scenario[:30]}..." if len(scenario) > 30 else f"Чат: {scenario}"
        chat_id = db.create_chat(self.user_id, title, scenario)
        
        if chat_id:
            self.current_chat_id = chat_id
            print(f"\n✅ Чат '{title}' создан!")
            
            # Приветствие от Оданн
            greeting = ai.generate_response("привет", [], scenario)
            db.add_message(chat_id, 'bot', greeting)
            
            print(f"🌸 Оданн: {greeting}")
            return self.chat_loop()
        else:
            print("❌ Ошибка создания чата!")
            return True
    
    def create_default_chat(self):
        """Создание чата со стандартным сценарием"""
        from config import DEFAULT_SCENARIO
        
        title = f"Чат с Оданн #{datetime.now().strftime('%d.%m %H:%M')}"
        chat_id = db.create_chat(self.user_id, title, DEFAULT_SCENARIO)
        
        if chat_id:
            self.current_chat_id = chat_id
            print(f"\n✅ Чат '{title}' создан!")
            print(f"📖 Сценарий: {DEFAULT_SCENARIO}")
            
            # Приветствие от Оданн
            greeting = ai.generate_response("привет", [], DEFAULT_SCENARIO)
            db.add_message(chat_id, 'bot', greeting)
            
            print(f"🌸 Оданн: {greeting}")
            return self.chat_loop()
        else:
            print("❌ Ошибка создания чата!")
            return True
    
    def show_chat_list(self):
        """Показ списка чатов"""
        chats = db.get_user_chats(self.user_id)
        
        if not chats:
            print("\n📚 У вас пока нет чатов")
            print("Создайте первый чат с Оданн!")
            input("\nНажмите Enter для продолжения...")
            return True
        
        print(f"\n📚 Ваши чаты с Оданн ({len(chats)}):")
        print("=" * 50)
        
        for i, chat in enumerate(chats, 1):
            creation_date = datetime.fromisoformat(chat['creation_date']).strftime('%d.%m.%Y %H:%M')
            print(f"{i}. {chat['title']}")
            print(f"   📅 Создан: {creation_date}")
            
            # Показываем количество сообщений
            history = db.get_chat_history(chat['chat_id'], 1)
            if history:
                last_msg = history[-1]
                role = "Оданн" if last_msg['role'] == 'bot' else "Вы"
                preview = last_msg['content'][:50] + "..." if len(last_msg['content']) > 50 else last_msg['content']
                print(f"   💬 Последнее: {role}: {preview}")
            print()
        
        print("0. 🔙 Назад")
        
        try:
            choice = int(input("Выберите чат для открытия: "))
            if choice == 0:
                return True
            elif 1 <= choice <= len(chats):
                selected_chat = chats[choice - 1]
                self.current_chat_id = selected_chat['chat_id']
                return self.open_chat(selected_chat)
            else:
                print("❌ Неверный номер чата!")
        except ValueError:
            print("❌ Введите число!")
        
        return True
    
    def open_chat(self, chat_info):
        """Открытие существующего чата"""
        print(f"\n💬 Открытие чата: {chat_info['title']}")
        
        # Показываем историю
        history = db.get_chat_history(self.current_chat_id, 10)
        if history:
            print("\n📜 История чата:")
            print("-" * 40)
            for msg in history[-5:]:  # Показываем последние 5 сообщений
                role_emoji = "👤" if msg['role'] == 'user' else "🌸"
                name = "Вы" if msg['role'] == 'user' else "Оданн"
                print(f"{role_emoji} {name}: {msg['content']}")
            print("-" * 40)
        
        return self.chat_loop()
    
    def chat_loop(self):
        """Основной цикл общения в чате"""
        print("\n💬 Начинайте общение! (введите 'exit' для выхода, 'menu' для меню чата)")
        
        while True:
            try:
                user_input = input("\n👤 Вы: ").strip()
                
                if user_input.lower() == 'exit':
                    return True
                elif user_input.lower() == 'menu':
                    return self.chat_menu()
                elif not user_input:
                    continue
                
                # Сохраняем сообщение пользователя
                db.add_message(self.current_chat_id, 'user', user_input)
                
                # Получаем информацию о чате и историю
                chat_info = db.get_chat_info(self.current_chat_id)
                history = db.get_chat_history(self.current_chat_id, 10)
                
                # Генерируем ответ от Оданн
                response = ai.generate_response(user_input, history, chat_info['scenario'])
                db.add_message(self.current_chat_id, 'bot', response)
                
                print(f"🌸 Оданн: {response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 До свидания!")
                return False
            except Exception as e:
                print(f"❌ Ошибка: {e}")
    
    def chat_menu(self):
        """Меню управления чатом"""
        chat_info = db.get_chat_info(self.current_chat_id)
        
        print(f"\n⚙️ Управление чатом: {chat_info['title']}")
        print("1. ✏️  Переименовать чат")
        print("2. 🗑️  Удалить чат")
        print("3. 📜 Показать историю сообщений")
        print("4. 🔙 Вернуться к чату")
        print("0. 🚪 Выйти в главное меню")
        
        choice = input("Выберите действие: ").strip()
        
        if choice == '1':
            return self.rename_chat()
        elif choice == '2':
            return self.delete_chat()
        elif choice == '3':
            return self.show_chat_history()
        elif choice == '4':
            return self.chat_loop()
        elif choice == '0':
            return True
        else:
            print("❌ Неверный выбор!")
            return self.chat_menu()
    
    def rename_chat(self):
        """Переименование чата"""
        new_title = input("Введите новое название чата: ").strip()
        if not new_title:
            print("❌ Название не может быть пустым!")
            return self.chat_menu()
        
        if db.rename_chat(self.current_chat_id, self.user_id, new_title):
            print(f"✅ Чат переименован в '{new_title}'")
        else:
            print("❌ Ошибка переименования!")
        
        return self.chat_menu()
    
    def delete_chat(self):
        """Удаление чата"""
        chat_info = db.get_chat_info(self.current_chat_id)
        confirm = input(f"Вы уверены, что хотите удалить чат '{chat_info['title']}'? (да/нет): ").strip().lower()
        
        if confirm in ['да', 'yes', 'y']:
            if db.delete_chat(self.current_chat_id, self.user_id):
                print("✅ Чат успешно удален!")
                self.current_chat_id = None
                return True
            else:
                print("❌ Ошибка удаления чата!")
        else:
            print("❌ Удаление отменено")
        
        return self.chat_menu()
    
    def show_chat_history(self):
        """Показ полной истории чата"""
        history = db.get_chat_history(self.current_chat_id, 50)
        
        print(f"\n📜 Полная история чата ({len(history)} сообщений):")
        print("=" * 60)
        
        for msg in history:
            timestamp = datetime.fromisoformat(msg['timestamp']).strftime('%d.%m %H:%M')
            role_emoji = "👤" if msg['role'] == 'user' else "🌸"
            name = "Вы" if msg['role'] == 'user' else "Оданн"
            print(f"[{timestamp}] {role_emoji} {name}: {msg['content']}")
        
        print("=" * 60)
        input("Нажмите Enter для продолжения...")
        return self.chat_menu()
    
    def demo_ai_responses(self):
        """Демонстрация AI ответов"""
        print("\n🤖 ДЕМОНСТРАЦИЯ AI ОТВЕТОВ")
        print("=" * 50)
        
        test_scenarios = [
            {
                "scenario": None,
                "name": "Стандартные ответы",
                "messages": ["привет", "как дела?", "расскажи о себе", "что ты готовишь?"]
            },
            {
                "scenario": "Вы впервые пришли в небесную гостиницу и очень голодны",
                "name": "Сценарий: голодный гость",
                "messages": ["я очень голоден", "что у вас есть поесть?", "можете что-то посоветовать?"]
            },
            {
                "scenario": "Вы грустите и нуждаетесь в утешении",
                "name": "Сценарий: утешение",
                "messages": ["мне грустно", "у меня проблемы", "не знаю что делать"]
            }
        ]
        
        for scenario_data in test_scenarios:
            print(f"\n📖 {scenario_data['name']}")
            if scenario_data['scenario']:
                print(f"Сценарий: {scenario_data['scenario']}")
            print("-" * 40)
            
            for msg in scenario_data['messages']:
                response = ai.generate_response(msg, [], scenario_data['scenario'])
                print(f"👤 Пользователь: {msg}")
                print(f"🌸 Оданн: {response}")
                print()
        
        input("Нажмите Enter для продолжения...")
        return True
    
    def show_database_stats(self):
        """Показ статистики базы данных"""
        print("\n📊 СТАТИСТИКА БАЗЫ ДАННЫХ")
        print("=" * 50)
        
        # Статистика пользователей
        total_chats = db.get_chat_count(self.user_id)
        print(f"👤 Пользователей: 1 (демо)")
        print(f"💬 Всего чатов: {total_chats}")
        
        # Статистика сообщений
        chats = db.get_user_chats(self.user_id)
        total_messages = 0
        
        for chat in chats:
            history = db.get_chat_history(chat['chat_id'], 1000)
            total_messages += len(history)
        
        print(f"📝 Всего сообщений: {total_messages}")
        
        # Детали по чатам
        if chats:
            print(f"\n📋 Детали по чатам:")
            for chat in chats:
                history = db.get_chat_history(chat['chat_id'], 1000)
                user_msgs = len([m for m in history if m['role'] == 'user'])
                bot_msgs = len([m for m in history if m['role'] == 'bot'])
                creation_date = datetime.fromisoformat(chat['creation_date']).strftime('%d.%m.%Y')
                
                print(f"  • {chat['title']}")
                print(f"    Создан: {creation_date}")
                print(f"    Сообщений: {user_msgs} от пользователя, {bot_msgs} от Оданн")
        
        input("\nНажмите Enter для продолжения...")
        return True
    
    def run(self):
        """Главный цикл демо-программы"""
        while True:
            try:
                self.show_menu()
                choice = input("\nВыберите действие: ").strip()
                
                if choice == '1':
                    if not self.create_chat_menu():
                        break
                elif choice == '2':
                    if not self.show_chat_list():
                        break
                elif choice == '3':
                    if not self.demo_ai_responses():
                        break
                elif choice == '4':
                    if not self.show_database_stats():
                        break
                elif choice == '0':
                    print("👋 До свидания! Спасибо за использование демо-версии бота Оданн!")
                    break
                else:
                    print("❌ Неверный выбор! Попробуйте снова.")
                    input("Нажмите Enter для продолжения...")
                
            except KeyboardInterrupt:
                print("\n\n👋 До свидания!")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                input("Нажмите Enter для продолжения...")

def main():
    """Запуск демо-версии"""
    print("🌸" * 25)
    print("  ДЕМО-ВЕРСИЯ БОТА ОДАНН")
    print("🌸" * 25)
    print()
    
    try:
        demo = OdannDemo()
        demo.run()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("Проверьте установку зависимостей и целостность файлов.")

if __name__ == '__main__':
    main()