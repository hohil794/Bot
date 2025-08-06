import logging
from typing import List, Dict, Optional, Any
from database import Database
from ai_model import AIModel
from config import CHAT_SETTINGS

logger = logging.getLogger(__name__)

class ChatManager:
    def __init__(self, database: Database, ai_model: AIModel):
        self.db = database
        self.ai_model = ai_model
        self.active_chats = {}  # Кэш активных чатов
    
    def create_chat(self, user_id: int, title: str, scenario: str = 'anime', settings: Dict = None) -> Optional[int]:
        """Создание нового чата"""
        try:
            chat_id = self.db.create_chat(user_id, title, scenario, settings)
            if chat_id:
                # Добавление в кэш
                self.active_chats[chat_id] = {
                    'user_id': user_id,
                    'title': title,
                    'scenario': scenario,
                    'settings': settings or {},
                    'message_count': 0
                }
                logger.info(f"Создан новый чат {chat_id} для пользователя {user_id}")
            return chat_id
        except Exception as e:
            logger.error(f"Ошибка создания чата: {e}")
            return None
    
    def get_user_chats(self, user_id: int) -> List[Dict]:
        """Получение всех чатов пользователя"""
        try:
            chats = self.db.get_user_chats(user_id)
            # Добавление описания для каждого чата
            for chat in chats:
                chat['summary'] = self.db.get_chat_summary(chat['chat_id'])
            return chats
        except Exception as e:
            logger.error(f"Ошибка получения чатов пользователя: {e}")
            return []
    
    def get_chat_messages(self, chat_id: int, limit: int = 20) -> List[Dict]:
        """Получение сообщений чата"""
        try:
            return self.db.get_chat_messages(chat_id, limit)
        except Exception as e:
            logger.error(f"Ошибка получения сообщений чата: {e}")
            return []
    
    def process_message(self, chat_id: int, user_id: int, text: str, user_gender: str = "unknown") -> Optional[str]:
        """Обработка сообщения пользователя и генерация ответа"""
        try:
            # Проверка на команду "забудь"
            if text.lower().startswith("забудь"):
                return self._handle_forget_command(chat_id, text)
            
            # Проверка на повторное сообщение
            if self.db.unmark_message_ignored(text, chat_id):
                return "Ах, вы повторили это сообщение. Хорошо, я его запомнил."
            
            # Сохранение сообщения пользователя
            if not self.db.add_message(chat_id, user_id, text, True):
                return "Извините, произошла ошибка при сохранении сообщения."
            
            # Получение истории сообщений
            messages = self.db.get_all_chat_messages(chat_id)
            
            # Получение настроек чата
            settings = self.db.get_chat_settings(chat_id)
            empathy_level = settings.get('empathy_level', 50) if settings else 50
            
            # Анализ сообщения
            analysis = self.ai_model.analyze_message(text, user_gender)
            
            # Генерация ответа
            response = self.ai_model.generate_response(messages, user_gender, empathy_level)
            
            # Сохранение ответа бота
            if not self.db.add_message(chat_id, user_id, response, False):
                logger.error("Ошибка сохранения ответа бота")
            
            # Автоматическая суммаризация при достижении лимита
            if len(messages) >= CHAT_SETTINGS['auto_summarize_interval']:
                self._auto_summarize_chat(chat_id)
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            return "Извините, произошла ошибка. Попробуйте еще раз."
    
    def _handle_forget_command(self, chat_id: int, text: str) -> str:
        """Обработка команды забыть сообщение"""
        try:
            # Извлечение текста для забывания
            forget_text = text[7:].strip()  # Убираем "забудь "
            
            if not forget_text:
                return "Что именно вы хотите, чтобы я забыл?"
            
            # Поиск сообщения в истории
            messages = self.db.get_all_chat_messages(chat_id)
            for msg in messages:
                if msg['is_from_user'] and forget_text.lower() in msg['text'].lower():
                    # Пометка сообщения как игнорируемого
                    self.db.mark_message_ignored(msg['message_id'])
                    return f"Хорошо, я забыл ваше сообщение: '{msg['text'][:50]}...'"
            
            return "Не нашел такого сообщения в нашей беседе."
            
        except Exception as e:
            logger.error(f"Ошибка обработки команды забыть: {e}")
            return "Извините, произошла ошибка при обработке команды."
    
    def _auto_summarize_chat(self, chat_id: int):
        """Автоматическая суммаризация чата"""
        try:
            messages = self.db.get_all_chat_messages(chat_id)
            summary = self.ai_model.summarize_chat(messages)
            
            # Сохранение суммаризации (можно добавить в отдельную таблицу)
            logger.info(f"Автоматическая суммаризация чата {chat_id}: {summary}")
            
        except Exception as e:
            logger.error(f"Ошибка автоматической суммаризации: {e}")
    
    def update_chat_title(self, chat_id: int, new_title: str) -> bool:
        """Обновление названия чата"""
        try:
            success = self.db.update_chat_title(chat_id, new_title)
            if success and chat_id in self.active_chats:
                self.active_chats[chat_id]['title'] = new_title
            return success
        except Exception as e:
            logger.error(f"Ошибка обновления названия чата: {e}")
            return False
    
    def delete_chat(self, chat_id: int) -> bool:
        """Удаление чата"""
        try:
            success = self.db.delete_chat(chat_id)
            if success and chat_id in self.active_chats:
                del self.active_chats[chat_id]
            return success
        except Exception as e:
            logger.error(f"Ошибка удаления чата: {e}")
            return False
    
    def get_chat_info(self, chat_id: int) -> Optional[Dict]:
        """Получение информации о чате"""
        try:
            chat = self.db.get_chat(chat_id)
            if chat:
                chat['summary'] = self.db.get_chat_summary(chat_id)
                chat['settings'] = self.db.get_chat_settings(chat_id)
            return chat
        except Exception as e:
            logger.error(f"Ошибка получения информации о чате: {e}")
            return None
    
    def update_chat_settings(self, chat_id: int, settings: Dict) -> bool:
        """Обновление настроек чата"""
        try:
            return self.db.update_chat_settings(chat_id, settings)
        except Exception as e:
            logger.error(f"Ошибка обновления настроек чата: {e}")
            return False
    
    def get_chat_summary(self, chat_id: int) -> str:
        """Получение описания чата"""
        try:
            return self.db.get_chat_summary(chat_id)
        except Exception as e:
            logger.error(f"Ошибка получения описания чата: {e}")
            return "Ошибка генерации описания"
    
    def handle_scenario(self, scenario: str, user_message: str) -> str:
        """Обработка специальных сценариев"""
        scenarios = {
            "lost_job": {
                "keywords": ["потерял работу", "уволили", "без работы", "безработный"],
                "response": "Понимаю вашу ситуацию, уважаемый гость. Потеря работы — серьезное испытание. Позвольте мне предложить несколько вариантов помощи..."
            },
            "relationship_problems": {
                "keywords": ["расстались", "развод", "проблемы в отношениях", "одинока"],
                "response": "Отношения — сложная сфера жизни. Иногда нужно время, чтобы разобраться в чувствах. Может быть, стоит поговорить об этом подробнее?"
            },
            "health_issues": {
                "keywords": ["болею", "плохо себя чувствую", "здоровье", "врач"],
                "response": "Здоровье — самое важное. Надеюсь, вы обратились к специалистам? В нашей гостинице мы заботимся о благополучии гостей."
            }
        }
        
        for scenario_name, scenario_data in scenarios.items():
            if any(keyword in user_message.lower() for keyword in scenario_data["keywords"]):
                return scenario_data["response"]
        
        return None  # Сценарий не найден