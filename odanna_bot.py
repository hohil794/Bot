import logging
import os
from telegram import Update, ParseMode
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, CallbackQueryHandler,
    Filters, ConversationHandler, PicklePersistence
)
from typing import Dict, Any

from config import BOT_TOKEN, ADMIN_ID, LOGGING_CONFIG
from database import Database
from ai_model import AIModel
from chat_manager import ChatManager
from keyboard_manager import KeyboardManager

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG["level"]),
    format=LOGGING_CONFIG["format"],
    filename=LOGGING_CONFIG["filename"]
)
logger = logging.getLogger(__name__)

# Состояния разговора
(
    MAIN_MENU, CREATE_CHAT, CHAT_LIST, CHAT_DETAIL, CHAT_INTERFACE,
    CREATE_WITH_SETTINGS, SCENARIO_SELECTION, EMPATHY_SELECTION,
    LENGTH_SELECTION, PERSONALITY_SELECTION, CHAT_SETTINGS,
    RENAME_CHAT, ADMIN_PANEL
) = range(13)

class OdannaBot:
    def __init__(self):
        self.db = Database()
        self.ai_model = AIModel()
        self.chat_manager = ChatManager(self.db, self.ai_model)
        self.keyboard_manager = KeyboardManager()
        
        # Загрузка модели
        self.ai_model.load_model()
        
        # Хранение состояния пользователей
        self.user_states = {}
        
        # Инициализация бота
        self.updater = Updater(BOT_TOKEN, use_context=True)
        self.dp = self.updater.dispatcher
        
        # Настройка обработчиков
        self.setup_handlers()
        
        logger.info("Бот Оданна инициализирован")
    
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        
        # Обработчик команды /start
        start_handler = CommandHandler('start', self.start_command)
        self.dp.add_handler(start_handler)
        
        # Обработчик команды /help
        help_handler = CommandHandler('help', self.help_command)
        self.dp.add_handler(help_handler)
        
        # Обработчик команды /admin
        admin_handler = CommandHandler('admin', self.admin_command)
        self.dp.add_handler(admin_handler)
        
        # Обработчик callback запросов
        callback_handler = CallbackQueryHandler(self.handle_callback)
        self.dp.add_handler(callback_handler)
        
        # Обработчик текстовых сообщений
        message_handler = MessageHandler(Filters.text & ~Filters.command, self.handle_message)
        self.dp.add_handler(message_handler)
        
        # Обработчик ошибок
        self.dp.add_error_handler(self.error_handler)
    
    def start_command(self, update: Update, context):
        """Обработка команды /start"""
        user = update.effective_user
        user_id = user.id
        
        # Регистрация пользователя
        self.db.add_user(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Определение пола пользователя
        user_gender = "female" if user.first_name and user.first_name.endswith(('а', 'я')) else "male"
        
        welcome_text = (
            f"🏨 Добро пожаловать в **Небесную Гостиницу**, уважаемый гость.\n\n"
            f"Я — **Оданна**, хозяин этого заведения. Здесь вы можете найти покой "
            f"и уединение, а также пообщаться со мной в непринужденной обстановке.\n\n"
            f"Чем могу быть полезен?"
        )
        
        if user_gender == "female":
            welcome_text = welcome_text.replace("уважаемый гость", "уважаемая гостья")
        
        keyboard = self.keyboard_manager.get_main_menu_keyboard()
        
        update.message.reply_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return MAIN_MENU
    
    def help_command(self, update: Update, context):
        """Обработка команды /help"""
        help_text = (
            "🏨 **Помощь по использованию бота Оданна**\n\n"
            "**Основные команды:**\n"
            "• /start - Главное меню\n"
            "• /help - Эта справка\n"
            "• /admin - Панель администратора\n\n"
            "**Возможности:**\n"
            "• Создание чатов с настройками\n"
            "• Выбор сценариев и уровня эмпатии\n"
            "• Полная история всех сообщений\n"
            "• Команда 'забудь [текст]' для игнорирования\n"
            "• Автоматическая суммаризация чатов\n\n"
            "**Особенности Оданны:**\n"
            "• Вежливый, но властный тон\n"
            "• Сарказм и ирония\n"
            "• Защита 'своих' и гостей\n"
            "• Теплое отношение к женщинам\n\n"
            "Наслаждайтесь общением в Небесной Гостинице! 🏨"
        )
        
        keyboard = self.keyboard_manager.get_help_keyboard()
        
        update.message.reply_text(
            help_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return MAIN_MENU
    
    def admin_command(self, update: Update, context):
        """Обработка команды /admin"""
        user_id = update.effective_user.id
        
        if user_id != ADMIN_ID:
            update.message.reply_text("❌ У вас нет доступа к панели администратора.")
            return MAIN_MENU
        
        admin_text = (
            "👑 **Панель администратора**\n\n"
            "Добро пожаловать, администратор. Выберите действие:"
        )
        
        keyboard = self.keyboard_manager.get_admin_keyboard()
        
        update.message.reply_text(
            admin_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ADMIN_PANEL
    
    def handle_callback(self, update: Update, context):
        """Обработка callback запросов"""
        query = update.callback_query
        data = query.data
        user_id = query.from_user.id
        
        try:
            if data == "main_menu":
                return self.show_main_menu(update, context)
            
            elif data == "create_chat":
                return self.show_create_chat_menu(update, context)
            
            elif data == "chat_list":
                return self.show_chat_list(update, context)
            
            elif data.startswith("create_"):
                return self.handle_create_chat(update, context, data)
            
            elif data.startswith("scenario_"):
                return self.handle_scenario_selection(update, context, data)
            
            elif data.startswith("empathy_"):
                return self.handle_empathy_selection(update, context, data)
            
            elif data.startswith("length_"):
                return self.handle_length_selection(update, context, data)
            
            elif data.startswith("trait_"):
                return self.handle_personality_selection(update, context, data)
            
            elif data.startswith("chat_"):
                return self.handle_chat_selection(update, context, data)
            
            elif data.startswith("open_chat_"):
                return self.open_chat(update, context, data)
            
            elif data.startswith("delete_chat_"):
                return self.handle_delete_chat(update, context, data)
            
            elif data.startswith("confirm_"):
                return self.handle_confirmation(update, context, data)
            
            elif data.startswith("cancel_"):
                return self.handle_cancellation(update, context, data)
            
            elif data.startswith("admin_"):
                return self.handle_admin_action(update, context, data)
            
            else:
                query.answer("Неизвестное действие")
                return MAIN_MENU
                
        except Exception as e:
            logger.error(f"Ошибка обработки callback: {e}")
            query.answer("Произошла ошибка")
            return MAIN_MENU
    
    def handle_message(self, update: Update, context):
        """Обработка текстовых сообщений"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Проверка активного чата
        if user_id in self.user_states and 'active_chat_id' in self.user_states[user_id]:
            chat_id = self.user_states[user_id]['active_chat_id']
            
            # Определение пола пользователя
            user_gender = "female" if update.effective_user.first_name and update.effective_user.first_name.endswith(('а', 'я')) else "male"
            
            # Обработка сообщения
            response = self.chat_manager.process_message(chat_id, user_id, text, user_gender)
            
            if response:
                keyboard = self.keyboard_manager.get_chat_interface_keyboard(chat_id)
                update.message.reply_text(response, reply_markup=keyboard)
            else:
                update.message.reply_text("Извините, произошла ошибка при обработке сообщения.")
            
            return CHAT_INTERFACE
        else:
            # Если нет активного чата, показываем главное меню
            update.message.reply_text(
                "Пожалуйста, выберите чат для общения или создайте новый.",
                reply_markup=self.keyboard_manager.get_main_menu_keyboard()
            )
            return MAIN_MENU
    
    def show_main_menu(self, update: Update, context):
        """Показать главное меню"""
        text = "🏨 **Главное меню**\n\nВыберите действие:"
        keyboard = self.keyboard_manager.get_main_menu_keyboard()
        
        if update.callback_query:
            update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        else:
            update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        
        return MAIN_MENU
    
    def show_create_chat_menu(self, update: Update, context):
        """Показать меню создания чата"""
        text = "🎭 **Создание чата**\n\nВыберите тип создания:"
        keyboard = self.keyboard_manager.get_create_chat_keyboard()
        
        update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        return CREATE_CHAT
    
    def show_chat_list(self, update: Update, context):
        """Показать список чатов"""
        user_id = update.callback_query.from_user.id
        chats = self.chat_manager.get_user_chats(user_id)
        
        if not chats:
            text = "📝 У вас пока нет чатов. Создайте первый!"
        else:
            text = f"💬 **Ваши чаты** ({len(chats)}):\n\n"
            for i, chat in enumerate(chats[:5], 1):
                text += f"{i}. **{chat['title']}**\n"
                text += f"   📅 {chat['created_at'][:10]}\n"
                text += f"   📝 {chat['summary']}\n\n"
        
        keyboard = self.keyboard_manager.get_chat_list_keyboard(chats)
        update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        return CHAT_LIST
    
    def handle_create_chat(self, update: Update, context, data):
        """Обработка создания чата"""
        user_id = update.callback_query.from_user.id
        
        if data == "create_simple":
            # Создание простого чата
            chat_id = self.chat_manager.create_chat(
                user_id=user_id,
                title="Новый чат",
                scenario="anime"
            )
            
            if chat_id:
                # Установка активного чата
                if user_id not in self.user_states:
                    self.user_states[user_id] = {}
                self.user_states[user_id]['active_chat_id'] = chat_id
                
                text = (
                    "✅ **Чат создан!**\n\n"
                    "Теперь вы можете общаться с Оданной. "
                    "Просто напишите сообщение, и я отвечу вам в своем стиле."
                )
                
                keyboard = self.keyboard_manager.get_chat_interface_keyboard(chat_id)
                update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
                return CHAT_INTERFACE
            else:
                update.callback_query.answer("Ошибка создания чата")
                return self.show_create_chat_menu(update, context)
        
        elif data == "create_with_settings":
            # Показать выбор сценария
            text = "🎭 **Выберите сценарий:**\n\nКаждый сценарий определяет стиль общения Оданны."
            keyboard = self.keyboard_manager.get_scenario_keyboard()
            update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
            return CREATE_WITH_SETTINGS
        
        return MAIN_MENU
    
    def handle_scenario_selection(self, update: Update, context, data):
        """Обработка выбора сценария"""
        scenario = data.split("_")[1]
        
        # Сохранение выбранного сценария
        user_id = update.callback_query.from_user.id
        if user_id not in self.user_states:
            self.user_states[user_id] = {}
        self.user_states[user_id]['temp_scenario'] = scenario
        
        text = "💝 **Выберите уровень эмпатии:**\n\nЭто определит, насколько тепло Оданна будет общаться с вами."
        keyboard = self.keyboard_manager.get_empathy_keyboard()
        update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        return EMPATHY_SELECTION
    
    def handle_empathy_selection(self, update: Update, context, data):
        """Обработка выбора уровня эмпатии"""
        empathy_level = int(data.split("_")[1])
        
        # Сохранение уровня эмпатии
        user_id = update.callback_query.from_user.id
        self.user_states[user_id]['temp_empathy'] = empathy_level
        
        text = "📏 **Выберите длину ответов:**\n\nЭто определит, насколько подробно Оданна будет отвечать."
        keyboard = self.keyboard_manager.get_response_length_keyboard()
        update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        return LENGTH_SELECTION
    
    def handle_length_selection(self, update: Update, context, data):
        """Обработка выбора длины ответа"""
        length = data.split("_")[1]
        
        # Сохранение длины ответа
        user_id = update.callback_query.from_user.id
        self.user_states[user_id]['temp_length'] = length
        
        text = "🎭 **Выберите личностные черты:**\n\nЭто добавит особые характеристики к поведению Оданны."
        keyboard = self.keyboard_manager.get_personality_traits_keyboard()
        update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        return PERSONALITY_SELECTION
    
    def handle_personality_selection(self, update: Update, context, data):
        """Обработка выбора личностных черт"""
        trait = data.split("_")[1]
        
        user_id = update.callback_query.from_user.id
        user_state = self.user_states.get(user_id, {})
        
        # Создание чата с настройками
        settings = {
            'empathy_level': user_state.get('temp_empathy', 50),
            'response_length': user_state.get('temp_length', 'medium'),
            'personality_traits': [trait]
        }
        
        chat_id = self.chat_manager.create_chat(
            user_id=user_id,
            title="Новый чат с настройками",
            scenario=user_state.get('temp_scenario', 'anime'),
            settings=settings
        )
        
        if chat_id:
            # Установка активного чата
            self.user_states[user_id]['active_chat_id'] = chat_id
            
            # Очистка временных данных
            for key in ['temp_scenario', 'temp_empathy', 'temp_length']:
                if key in self.user_states[user_id]:
                    del self.user_states[user_id][key]
            
            text = (
                "✅ **Чат создан с настройками!**\n\n"
                f"• Сценарий: {user_state.get('temp_scenario', 'anime')}\n"
                f"• Эмпатия: {user_state.get('temp_empathy', 50)}%\n"
                f"• Длина: {user_state.get('temp_length', 'medium')}\n"
                f"• Черта: {trait}\n\n"
                "Теперь вы можете общаться с Оданной!"
            )
            
            keyboard = self.keyboard_manager.get_chat_interface_keyboard(chat_id)
            update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
            return CHAT_INTERFACE
        else:
            update.callback_query.answer("Ошибка создания чата")
            return self.show_create_chat_menu(update, context)
    
    def handle_chat_selection(self, update: Update, context, data):
        """Обработка выбора чата"""
        chat_id = int(data.split("_")[1])
        user_id = update.callback_query.from_user.id
        
        chat_info = self.chat_manager.get_chat_info(chat_id)
        if not chat_info:
            update.callback_query.answer("Чат не найден")
            return self.show_chat_list(update, context)
        
        text = (
            f"💬 **{chat_info['title']}**\n\n"
            f"📅 Создан: {chat_info['created_at'][:10]}\n"
            f"📝 Описание: {chat_info['summary']}\n"
            f"🎭 Сценарий: {chat_info['scenario']}\n\n"
            "Выберите действие:"
        )
        
        keyboard = self.keyboard_manager.get_chat_detail_keyboard(chat_id)
        update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        return CHAT_DETAIL
    
    def open_chat(self, update: Update, context, data):
        """Открыть чат для общения"""
        chat_id = int(data.split("_")[1])
        user_id = update.callback_query.from_user.id
        
        # Установка активного чата
        if user_id not in self.user_states:
            self.user_states[user_id] = {}
        self.user_states[user_id]['active_chat_id'] = chat_id
        
        chat_info = self.chat_manager.get_chat_info(chat_id)
        
        text = (
            f"💬 **{chat_info['title']}**\n\n"
            "Теперь вы можете общаться с Оданной. Просто напишите сообщение!"
        )
        
        keyboard = self.keyboard_manager.get_chat_interface_keyboard(chat_id)
        update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        return CHAT_INTERFACE
    
    def handle_delete_chat(self, update: Update, context, data):
        """Обработка удаления чата"""
        chat_id = int(data.split("_")[1])
        
        text = "🗑️ **Удаление чата**\n\nВы уверены, что хотите удалить этот чат? Это действие нельзя отменить."
        keyboard = self.keyboard_manager.get_confirm_keyboard("delete", chat_id)
        update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        return CHAT_DETAIL
    
    def handle_confirmation(self, update: Update, context, data):
        """Обработка подтверждения действия"""
        parts = data.split("_")
        action = parts[1]
        chat_id = int(parts[2])
        
        if action == "delete":
            success = self.chat_manager.delete_chat(chat_id)
            if success:
                text = "✅ Чат успешно удален!"
            else:
                text = "❌ Ошибка удаления чата"
            
            keyboard = self.keyboard_manager.get_main_menu_keyboard()
            update.callback_query.edit_message_text(text, reply_markup=keyboard)
            return MAIN_MENU
        
        return MAIN_MENU
    
    def handle_cancellation(self, update: Update, context, data):
        """Обработка отмены действия"""
        update.callback_query.answer("Действие отменено")
        return self.show_main_menu(update, context)
    
    def handle_admin_action(self, update: Update, context, data):
        """Обработка действий администратора"""
        action = data.split("_")[1]
        
        if action == "stats":
            # Статистика
            total_users = len(self.db.get_all_users())
            total_chats = len(self.db.get_all_chats())
            total_messages = len(self.db.get_all_messages())
            
            text = (
                "📊 **Статистика бота**\n\n"
                f"👥 Пользователей: {total_users}\n"
                f"💬 Чатов: {total_chats}\n"
                f"📝 Сообщений: {total_messages}\n"
            )
        else:
            text = "🔧 Эта функция находится в разработке"
        
        keyboard = self.keyboard_manager.get_admin_keyboard()
        update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        return ADMIN_PANEL
    
    def error_handler(self, update: Update, context):
        """Обработчик ошибок"""
        logger.error(f"Ошибка: {context.error}")
        
        if update and update.effective_message:
            update.effective_message.reply_text(
                "❌ Произошла ошибка. Попробуйте еще раз или обратитесь к администратору."
            )
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск бота Оданна...")
        self.updater.start_polling()
        self.updater.idle()

def main():
    """Главная функция"""
    bot = OdannaBot()
    bot.run()

if __name__ == '__main__':
    main()