from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

class BotKeyboards:
    
    @staticmethod
    def get_main_menu():
        """Главное меню бота"""
        keyboard = [
            [InlineKeyboardButton("✨ Создать чат", callback_data="create_chat")],
            [InlineKeyboardButton("📋 Список чатов", callback_data="chat_list")],
            [InlineKeyboardButton("ℹ️ Справка", callback_data="help")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_create_chat_menu():
        """Меню создания чата"""
        keyboard = [
            [InlineKeyboardButton("⚙️ С настройками", callback_data="create_with_settings")],
            [InlineKeyboardButton("🎭 Без настроек (стандартный сценарий)", callback_data="create_default")],
            [InlineKeyboardButton("⬅️ Назад в меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_chat_list_keyboard(chats):
        """Клавиатура списка чатов"""
        keyboard = []
        
        for chat_id, title, scenario, creation_date in chats:
            # Ограничиваем длину названия для кнопки
            display_title = title[:30] + "..." if len(title) > 30 else title
            keyboard.append([InlineKeyboardButton(f"💬 {display_title}", 
                                                callback_data=f"open_chat_{chat_id}")])
        
        if not keyboard:
            keyboard.append([InlineKeyboardButton("📝 Создать первый чат", callback_data="create_chat")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад в меню", callback_data="main_menu")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_chat_management_keyboard(chat_id):
        """Клавиатура управления чатом"""
        keyboard = [
            [InlineKeyboardButton("✏️ Переименовать", callback_data=f"rename_chat_{chat_id}")],
            [InlineKeyboardButton("🗑️ Удалить чат", callback_data=f"delete_chat_{chat_id}")],
            [InlineKeyboardButton("📋 К списку чатов", callback_data="chat_list")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_confirm_delete_keyboard(chat_id):
        """Клавиатура подтверждения удаления"""
        keyboard = [
            [InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{chat_id}")],
            [InlineKeyboardButton("❌ Отмена", callback_data=f"open_chat_{chat_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_cancel_keyboard():
        """Клавиатура отмены действия"""
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_back_to_chat_keyboard(chat_id):
        """Клавиатура возврата в чат"""
        keyboard = [
            [InlineKeyboardButton("⬅️ Вернуться в чат", callback_data=f"open_chat_{chat_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)