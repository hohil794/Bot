import logging
from datetime import datetime
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler
)

from config import (
    BOT_TOKEN, 
    MAIN_MENU, CREATE_CHAT_MENU, CHAT_WITH_SETTINGS, CHAT_WITHOUT_SETTINGS,
    CHAT_LIST, ACTIVE_CHAT, CHAT_MANAGEMENT, SCENARIO_INPUT, CHAT_RENAME,
    DEFAULT_SCENARIO, MAX_CHATS_PER_USER, MAX_MESSAGE_LENGTH
)
from database import db
from ai_model import ai

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class OdannBot:
    def __init__(self):
        """Инициализация бота Оданн"""
        self.updater = Updater(BOT_TOKEN, use_context=True)
        self.dp = self.updater.dispatcher
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        
        # Основной ConversationHandler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start_command)],
            states={
                MAIN_MENU: [
                    CallbackQueryHandler(self.create_chat_menu, pattern='^create_chat$'),
                    CallbackQueryHandler(self.show_chat_list, pattern='^chat_list$'),
                ],
                CREATE_CHAT_MENU: [
                    CallbackQueryHandler(self.chat_with_settings, pattern='^with_settings$'),
                    CallbackQueryHandler(self.chat_without_settings, pattern='^without_settings$'),
                    CallbackQueryHandler(self.back_to_main, pattern='^back_to_main$'),
                ],
                SCENARIO_INPUT: [
                    MessageHandler(Filters.text & ~Filters.command, self.process_scenario),
                ],
                CHAT_LIST: [
                    CallbackQueryHandler(self.open_chat, pattern='^open_chat_'),
                    CallbackQueryHandler(self.back_to_main, pattern='^back_to_main$'),
                ],
                ACTIVE_CHAT: [
                    MessageHandler(Filters.text & ~Filters.command, self.process_message),
                    CallbackQueryHandler(self.chat_management, pattern='^manage_chat$'),
                    CallbackQueryHandler(self.back_to_main, pattern='^exit_chat$'),
                ],
                CHAT_MANAGEMENT: [
                    CallbackQueryHandler(self.delete_chat, pattern='^delete_chat$'),
                    CallbackQueryHandler(self.rename_chat_start, pattern='^rename_chat$'),
                    CallbackQueryHandler(self.back_to_chat, pattern='^back_to_chat$'),
                ],
                CHAT_RENAME: [
                    MessageHandler(Filters.text & ~Filters.command, self.process_rename),
                ]
            },
            fallbacks=[CommandHandler('start', self.start_command)],
            allow_reentry=True
        )
        
        self.dp.add_handler(conv_handler)
        self.dp.add_error_handler(self.error_handler)
    
    def start_command(self, update: Update, context: CallbackContext) -> int:
        """Обработка команды /start - главное меню"""
        user = update.effective_user
        
        # Добавляем пользователя в базу данных
        db.add_user(user.id, user.username, user.first_name)
        
        # Очищаем контекст пользователя
        context.user_data.clear()
        
        welcome_text = (
            "🌸 Добро пожаловать в мир небесной гостиницы! 🌸\n\n"
            "Я Оданн, служанка и повар небесной гостиницы Цунику-ин! "
            "Буду рада пообщаться с вами и поделиться историями о мире духов~\n\n"
            "Выберите действие:"
        )
        
        keyboard = [
            [InlineKeyboardButton("💬 Создать чат", callback_data='create_chat')],
            [InlineKeyboardButton("📚 Список чатов", callback_data='chat_list')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            update.message.reply_text(welcome_text, reply_markup=reply_markup)
        else:
            update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)
        
        return MAIN_MENU
    
    def create_chat_menu(self, update: Update, context: CallbackContext) -> int:
        """Меню создания чата"""
        query = update.callback_query
        query.answer()
        
        user_id = update.effective_user.id
        chat_count = db.get_chat_count(user_id)
        
        if chat_count >= MAX_CHATS_PER_USER:
            query.edit_message_text(
                f"❌ Достигнут лимит чатов ({MAX_CHATS_PER_USER})\n"
                "Удалите старые чаты, чтобы создать новые.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')
                ]])
            )
            return CREATE_CHAT_MENU
        
        text = (
            "✨ Создание нового чата с Оданн ✨\n\n"
            "Выберите тип чата:"
        )
        
        keyboard = [
            [InlineKeyboardButton("⚙️ С настройками", callback_data='with_settings')],
            [InlineKeyboardButton("🎬 Без настроек (сценарий аниме)", callback_data='without_settings')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(text, reply_markup=reply_markup)
        return CREATE_CHAT_MENU
    
    def chat_with_settings(self, update: Update, context: CallbackContext) -> int:
        """Создание чата с пользовательскими настройками"""
        query = update.callback_query
        query.answer()
        
        text = (
            "📝 Создание чата с настройками\n\n"
            "Опишите сценарий для общения с Оданн:\n"
            "• Где происходит действие?\n"
            "• Какая ситуация?\n"
            "• Какую роль играете вы?\n\n"
            "Пример: 'Я гость небесной гостиницы, который впервые попробовал блюдо Оданн и хочет узнать рецепт'"
        )
        
        query.edit_message_text(text)
        context.user_data['chat_type'] = 'with_settings'
        return SCENARIO_INPUT
    
    def chat_without_settings(self, update: Update, context: CallbackContext) -> int:
        """Создание чата со стандартным сценарием"""
        query = update.callback_query
        query.answer()
        
        user_id = update.effective_user.id
        chat_title = f"Чат с Оданн #{datetime.now().strftime('%d.%m %H:%M')}"
        
        # Создаем чат с дефолтным сценарием
        chat_id = db.create_chat(user_id, chat_title, DEFAULT_SCENARIO)
        
        if chat_id:
            context.user_data['current_chat_id'] = chat_id
            
            # Приветствие от Оданн
            greeting = ai.generate_response("привет", [], DEFAULT_SCENARIO)
            db.add_message(chat_id, 'bot', greeting)
            
            text = (
                f"✨ Чат '{chat_title}' создан!\n\n"
                f"📖 Сценарий:\n{DEFAULT_SCENARIO}\n\n"
                f"🌸 Оданн: {greeting}\n\n"
                "Начинайте общение! Просто напишите сообщение."
            )
            
            keyboard = [
                [InlineKeyboardButton("⚙️ Управление чатом", callback_data='manage_chat')],
                [InlineKeyboardButton("🚪 Выйти в меню", callback_data='exit_chat')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query.edit_message_text(text, reply_markup=reply_markup)
            return ACTIVE_CHAT
        else:
            query.edit_message_text(
                "❌ Ошибка создания чата. Попробуйте снова.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')
                ]])
            )
            return CREATE_CHAT_MENU
    
    def process_scenario(self, update: Update, context: CallbackContext) -> int:
        """Обработка пользовательского сценария"""
        scenario = update.message.text.strip()
        
        if len(scenario) > 500:
            update.message.reply_text(
                "❌ Сценарий слишком длинный (максимум 500 символов).\n"
                "Попробуйте сократить описание."
            )
            return SCENARIO_INPUT
        
        user_id = update.effective_user.id
        chat_title = f"Чат: {scenario[:30]}..." if len(scenario) > 30 else f"Чат: {scenario}"
        
        # Создаем чат с пользовательским сценарием
        chat_id = db.create_chat(user_id, chat_title, scenario)
        
        if chat_id:
            context.user_data['current_chat_id'] = chat_id
            
            # Приветствие от Оданн с учетом сценария
            greeting = ai.generate_response("привет", [], scenario)
            db.add_message(chat_id, 'bot', greeting)
            
            text = (
                f"✨ Чат создан!\n\n"
                f"📖 Ваш сценарий:\n{scenario}\n\n"
                f"🌸 Оданн: {greeting}\n\n"
                "Начинайте общение! Просто напишите сообщение."
            )
            
            keyboard = [
                [InlineKeyboardButton("⚙️ Управление чатом", callback_data='manage_chat')],
                [InlineKeyboardButton("🚪 Выйти в меню", callback_data='exit_chat')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(text, reply_markup=reply_markup)
            return ACTIVE_CHAT
        else:
            update.message.reply_text(
                "❌ Ошибка создания чата. Попробуйте снова.",
                reply_markup=ReplyKeyboardMarkup([['🔙 Вернуться в меню']], resize_keyboard=True)
            )
            return self.start_command(update, context)
    
    def show_chat_list(self, update: Update, context: CallbackContext) -> int:
        """Показ списка чатов пользователя"""
        query = update.callback_query
        query.answer()
        
        user_id = update.effective_user.id
        chats = db.get_user_chats(user_id)
        
        if not chats:
            text = (
                "📚 У вас пока нет чатов\n\n"
                "Создайте первый чат с Оданн!"
            )
            keyboard = [
                [InlineKeyboardButton("💬 Создать чат", callback_data='create_chat')],
                [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
            ]
        else:
            text = "📚 Ваши чаты с Оданн:\n\n"
            keyboard = []
            
            for chat in chats:
                creation_date = datetime.fromisoformat(chat['creation_date']).strftime('%d.%m %H:%M')
                chat_button_text = f"💬 {chat['title']} ({creation_date})"
                keyboard.append([InlineKeyboardButton(
                    chat_button_text, 
                    callback_data=f'open_chat_{chat["chat_id"]}'
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text, reply_markup=reply_markup)
        return CHAT_LIST
    
    def open_chat(self, update: Update, context: CallbackContext) -> int:
        """Открытие существующего чата"""
        query = update.callback_query
        query.answer()
        
        chat_id = int(query.data.split('_')[2])
        user_id = update.effective_user.id
        
        # Проверяем, принадлежит ли чат пользователю
        chat_info = db.get_chat_info(chat_id)
        if not chat_info or chat_info['user_id'] != user_id:
            query.edit_message_text(
                "❌ Чат не найден",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')
                ]])
            )
            return CHAT_LIST
        
        context.user_data['current_chat_id'] = chat_id
        
        # Получаем историю чата
        history = db.get_chat_history(chat_id, 20)
        
        # Формируем контекст для отображения
        chat_context = ai.format_chat_context(history, chat_info['scenario'])
        
        text = (
            f"💬 Чат: {chat_info['title']}\n\n"
            f"{chat_context}\n"
            "Продолжайте общение! Просто напишите сообщение."
        )
        
        keyboard = [
            [InlineKeyboardButton("⚙️ Управление чатом", callback_data='manage_chat')],
            [InlineKeyboardButton("🚪 Выйти в меню", callback_data='exit_chat')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(text, reply_markup=reply_markup)
        return ACTIVE_CHAT
    
    def process_message(self, update: Update, context: CallbackContext) -> int:
        """Обработка сообщения пользователя в активном чате"""
        user_message = update.message.text.strip()
        chat_id = context.user_data.get('current_chat_id')
        
        if not chat_id:
            update.message.reply_text("❌ Ошибка: чат не найден")
            return self.start_command(update, context)
        
        if len(user_message) > MAX_MESSAGE_LENGTH:
            update.message.reply_text(
                f"❌ Сообщение слишком длинное (максимум {MAX_MESSAGE_LENGTH} символов)"
            )
            return ACTIVE_CHAT
        
        # Сохраняем сообщение пользователя
        db.add_message(chat_id, 'user', user_message)
        
        # Получаем информацию о чате и историю
        chat_info = db.get_chat_info(chat_id)
        history = db.get_chat_history(chat_id, 10)  # Последние 10 сообщений для контекста
        
        # Генерируем ответ от Оданн
        try:
            bot_response = ai.generate_response(user_message, history, chat_info['scenario'])
            db.add_message(chat_id, 'bot', bot_response)
            
            update.message.reply_text(f"🌸 Оданн: {bot_response}")
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            update.message.reply_text(
                "😅 Оданн: Ой, извините, я немного растерялась... Не могли бы вы повторить?"
            )
        
        return ACTIVE_CHAT
    
    def chat_management(self, update: Update, context: CallbackContext) -> int:
        """Меню управления чатом"""
        query = update.callback_query
        query.answer()
        
        chat_id = context.user_data.get('current_chat_id')
        chat_info = db.get_chat_info(chat_id)
        
        text = (
            f"⚙️ Управление чатом\n\n"
            f"📝 Название: {chat_info['title']}\n"
            f"📅 Создан: {datetime.fromisoformat(chat_info['creation_date']).strftime('%d.%m.%Y %H:%M')}\n\n"
            "Выберите действие:"
        )
        
        keyboard = [
            [InlineKeyboardButton("✏️ Переименовать", callback_data='rename_chat')],
            [InlineKeyboardButton("🗑️ Удалить чат", callback_data='delete_chat')],
            [InlineKeyboardButton("🔙 Вернуться к чату", callback_data='back_to_chat')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(text, reply_markup=reply_markup)
        return CHAT_MANAGEMENT
    
    def delete_chat(self, update: Update, context: CallbackContext) -> int:
        """Удаление чата"""
        query = update.callback_query
        query.answer()
        
        chat_id = context.user_data.get('current_chat_id')
        user_id = update.effective_user.id
        
        if db.delete_chat(chat_id, user_id):
            query.edit_message_text(
                "✅ Чат успешно удален",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 В главное меню", callback_data='back_to_main')
                ]])
            )
            context.user_data.pop('current_chat_id', None)
            return MAIN_MENU
        else:
            query.edit_message_text(
                "❌ Ошибка удаления чата",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data='back_to_chat')
                ]])
            )
            return CHAT_MANAGEMENT
    
    def rename_chat_start(self, update: Update, context: CallbackContext) -> int:
        """Начало переименования чата"""
        query = update.callback_query
        query.answer()
        
        query.edit_message_text(
            "✏️ Введите новое название для чата:\n"
            "(максимум 50 символов)"
        )
        return CHAT_RENAME
    
    def process_rename(self, update: Update, context: CallbackContext) -> int:
        """Обработка нового названия чата"""
        new_title = update.message.text.strip()
        
        if len(new_title) > 50:
            update.message.reply_text(
                "❌ Название слишком длинное (максимум 50 символов).\n"
                "Попробуйте еще раз:"
            )
            return CHAT_RENAME
        
        chat_id = context.user_data.get('current_chat_id')
        user_id = update.effective_user.id
        
        if db.rename_chat(chat_id, user_id, new_title):
            update.message.reply_text(
                f"✅ Чат переименован в '{new_title}'",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Вернуться к чату", callback_data='back_to_chat')
                ]])
            )
            return CHAT_MANAGEMENT
        else:
            update.message.reply_text(
                "❌ Ошибка переименования чата",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data='back_to_chat')
                ]])
            )
            return CHAT_MANAGEMENT
    
    def back_to_main(self, update: Update, context: CallbackContext) -> int:
        """Возврат в главное меню"""
        context.user_data.clear()
        return self.start_command(update, context)
    
    def back_to_chat(self, update: Update, context: CallbackContext) -> int:
        """Возврат к активному чату"""
        query = update.callback_query
        query.answer()
        
        chat_id = context.user_data.get('current_chat_id')
        chat_info = db.get_chat_info(chat_id)
        history = db.get_chat_history(chat_id, 5)  # Показываем последние 5 сообщений
        
        chat_context = ai.format_chat_context(history, chat_info['scenario'])
        
        text = (
            f"💬 Чат: {chat_info['title']}\n\n"
            f"{chat_context}\n"
            "Продолжайте общение!"
        )
        
        keyboard = [
            [InlineKeyboardButton("⚙️ Управление чатом", callback_data='manage_chat')],
            [InlineKeyboardButton("🚪 Выйти в меню", callback_data='exit_chat')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(text, reply_markup=reply_markup)
        return ACTIVE_CHAT
    
    def error_handler(self, update: Update, context: CallbackContext):
        """Обработка ошибок"""
        logger.error(f'Update {update} caused error {context.error}')
        
        if update.effective_message:
            update.effective_message.reply_text(
                "😅 Ой, что-то пошло не так... Попробуйте начать сначала с команды /start"
            )
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск бота Оданн...")
        self.updater.start_polling()
        self.updater.idle()

def main():
    """Главная функция"""
    bot = OdannBot()
    bot.run()

if __name__ == '__main__':
    main()