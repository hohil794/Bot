import logging
from typing import List, Dict, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from config import EMOJI

logger = logging.getLogger(__name__)

class KeyboardManager:
    def __init__(self):
        pass
    
    def get_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Главное меню бота"""
        keyboard = [
            [
                InlineKeyboardButton(f"{EMOJI['chat']} Создать чат", callback_data="create_chat"),
                InlineKeyboardButton(f"{EMOJI['settings']} Список чатов", callback_data="chat_list")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_create_chat_keyboard(self) -> InlineKeyboardMarkup:
        """Клавиатура создания чата"""
        keyboard = [
            [
                InlineKeyboardButton("🎭 С настройками", callback_data="create_with_settings"),
                InlineKeyboardButton("🎬 Без настроек", callback_data="create_simple")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['back']} Назад", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_scenario_keyboard(self) -> InlineKeyboardMarkup:
        """Клавиатура выбора сценария"""
        keyboard = [
            [
                InlineKeyboardButton("🏨 Аниме-сценарий", callback_data="scenario_anime"),
                InlineKeyboardButton("🎭 Драматический", callback_data="scenario_drama")
            ],
            [
                InlineKeyboardButton("🌙 Мистический", callback_data="scenario_mystic"),
                InlineKeyboardButton("💕 Романтический", callback_data="scenario_romance")
            ],
            [
                InlineKeyboardButton("🎯 Деловой", callback_data="scenario_business"),
                InlineKeyboardButton("🎪 Приключенческий", callback_data="scenario_adventure")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['back']} Назад", callback_data="create_chat")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_empathy_keyboard(self) -> InlineKeyboardMarkup:
        """Клавиатура выбора уровня эмпатии"""
        keyboard = [
            [
                InlineKeyboardButton("❄️ Сдержанный (30%)", callback_data="empathy_30"),
                InlineKeyboardButton("🌤️ Умеренный (50%)", callback_data="empathy_50")
            ],
            [
                InlineKeyboardButton("🌞 Теплый (70%)", callback_data="empathy_70"),
                InlineKeyboardButton("🔥 Очень теплый (90%)", callback_data="empathy_90")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['back']} Назад", callback_data="create_with_settings")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_response_length_keyboard(self) -> InlineKeyboardMarkup:
        """Клавиатура выбора длины ответа"""
        keyboard = [
            [
                InlineKeyboardButton("📝 Короткий", callback_data="length_short"),
                InlineKeyboardButton("📄 Средний", callback_data="length_medium")
            ],
            [
                InlineKeyboardButton("📚 Длинный", callback_data="length_long"),
                InlineKeyboardButton("📖 Очень длинный", callback_data="length_very_long")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['back']} Назад", callback_data="empathy_50")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_chat_list_keyboard(self, chats: List[Dict]) -> InlineKeyboardMarkup:
        """Клавиатура списка чатов"""
        keyboard = []
        
        for chat in chats[:10]:  # Максимум 10 чатов
            # Сокращение названия если слишком длинное
            title = chat['title'][:30] + "..." if len(chat['title']) > 30 else chat['title']
            keyboard.append([
                InlineKeyboardButton(
                    f"💬 {title}", 
                    callback_data=f"chat_{chat['chat_id']}"
                )
            ])
        
        if not chats:
            keyboard.append([
                InlineKeyboardButton("📝 Создать первый чат", callback_data="create_chat")
            ])
        
        keyboard.append([
            InlineKeyboardButton(f"{EMOJI['back']} Назад", callback_data="main_menu")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_chat_detail_keyboard(self, chat_id: int) -> InlineKeyboardMarkup:
        """Клавиатура деталей чата"""
        keyboard = [
            [
                InlineKeyboardButton("💬 Открыть чат", callback_data=f"open_chat_{chat_id}"),
                InlineKeyboardButton("📝 Переименовать", callback_data=f"rename_chat_{chat_id}")
            ],
            [
                InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_chat_{chat_id}"),
                InlineKeyboardButton("⚙️ Настройки", callback_data=f"chat_settings_{chat_id}")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['back']} К списку чатов", callback_data="chat_list")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_chat_settings_keyboard(self, chat_id: int) -> InlineKeyboardMarkup:
        """Клавиатура настроек чата"""
        keyboard = [
            [
                InlineKeyboardButton("💝 Уровень эмпатии", callback_data=f"settings_empathy_{chat_id}"),
                InlineKeyboardButton("📏 Длина ответа", callback_data=f"settings_length_{chat_id}")
            ],
            [
                InlineKeyboardButton("🎭 Личностные черты", callback_data=f"settings_personality_{chat_id}"),
                InlineKeyboardButton("🔄 Сбросить настройки", callback_data=f"settings_reset_{chat_id}")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['back']} К чату", callback_data=f"chat_{chat_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_confirm_keyboard(self, action: str, chat_id: int) -> InlineKeyboardMarkup:
        """Клавиатура подтверждения действия"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Да", callback_data=f"confirm_{action}_{chat_id}"),
                InlineKeyboardButton("❌ Нет", callback_data=f"cancel_{action}_{chat_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_chat_interface_keyboard(self, chat_id: int) -> InlineKeyboardMarkup:
        """Клавиатура интерфейса чата"""
        keyboard = [
            [
                InlineKeyboardButton("📝 Суммаризация", callback_data=f"summarize_{chat_id}"),
                InlineKeyboardButton("⚙️ Настройки", callback_data=f"chat_settings_{chat_id}")
            ],
            [
                InlineKeyboardButton("📋 История", callback_data=f"history_{chat_id}"),
                InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_personality_traits_keyboard(self) -> InlineKeyboardMarkup:
        """Клавиатура выбора личностных черт"""
        keyboard = [
            [
                InlineKeyboardButton("😊 Добрый", callback_data="trait_kind"),
                InlineKeyboardButton("😈 Строгий", callback_data="trait_strict")
            ],
            [
                InlineKeyboardButton("🤔 Мудрый", callback_data="trait_wise"),
                InlineKeyboardButton("😎 Загадочный", callback_data="trait_mysterious")
            ],
            [
                InlineKeyboardButton("😤 Властный", callback_data="trait_authoritative"),
                InlineKeyboardButton("😌 Спокойный", callback_data="trait_calm")
            ],
            [
                InlineKeyboardButton("🎭 Саркастичный", callback_data="trait_sarcastic"),
                InlineKeyboardButton("💝 Заботливый", callback_data="trait_caring")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['back']} Назад", callback_data="create_with_settings")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_admin_keyboard(self) -> InlineKeyboardMarkup:
        """Клавиатура администратора"""
        keyboard = [
            [
                InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
                InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton("💬 Чаты", callback_data="admin_chats"),
                InlineKeyboardButton("🔧 Настройки", callback_data="admin_settings")
            ],
            [
                InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_help_keyboard(self) -> InlineKeyboardMarkup:
        """Клавиатура помощи"""
        keyboard = [
            [
                InlineKeyboardButton("📖 Команды", callback_data="help_commands"),
                InlineKeyboardButton("🎭 Сценарии", callback_data="help_scenarios")
            ],
            [
                InlineKeyboardButton("⚙️ Настройки", callback_data="help_settings"),
                InlineKeyboardButton("💡 Советы", callback_data="help_tips")
            ],
            [
                InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_cancel_keyboard(self) -> InlineKeyboardMarkup:
        """Клавиатура отмены"""
        keyboard = [
            [
                InlineKeyboardButton("❌ Отменить", callback_data="cancel_action")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_remove_keyboard(self) -> ReplyKeyboardRemove:
        """Удаление клавиатуры"""
        return ReplyKeyboardRemove()
    
    def get_text_keyboard(self, buttons: List[List[str]]) -> ReplyKeyboardMarkup:
        """Создание текстовой клавиатуры"""
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)