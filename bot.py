import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

from database import Database
from ai_model import OdannaAI
from keyboards import BotKeyboards
from keep_alive import keep_alive

# Загружаем переменные окружения
load_dotenv()

# Настраиваем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_CHAT_TITLE, WAITING_SCENARIO, WAITING_RENAME = range(3)

class OdannaBot:
    def __init__(self):
        self.db = Database()
        self.ai = OdannaAI()
        self.keyboards = BotKeyboards()
        self.user_states = {}  # Хранение состояний пользователей
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        # Добавляем пользователя в БД
        self.db.add_user(user.id, user.username)
        
        welcome_text = """🌸 Добро пожаловать! 🌸

Привет! Меня зовут Оданн, и я ваш виртуальный друг из небесной гостиницы Тэндзин-я! 

Я могу:
✨ Общаться с вами в роли персонажа из аниме
💬 Создавать отдельные чаты с разными сценариями
📚 Развивать сюжет на основе ваших идей
🎭 Поддерживать атмосферу мира "Повар небесной гостиницы"

Выберите действие из меню ниже:"""
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=self.keyboards.get_main_menu()
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "main_menu":
            await self.show_main_menu(query)
        elif data == "create_chat":
            await self.show_create_chat_menu(query)
        elif data == "create_with_settings":
            await self.start_chat_creation_with_settings(query, context)
        elif data == "create_default":
            await self.create_default_chat(query, user_id)
        elif data == "chat_list":
            await self.show_chat_list(query, user_id)
        elif data.startswith("open_chat_"):
            chat_id = int(data.split("_")[2])
            await self.open_chat(query, user_id, chat_id)
        elif data.startswith("rename_chat_"):
            chat_id = int(data.split("_")[2])
            await self.start_rename_chat(query, context, chat_id)
        elif data.startswith("delete_chat_"):
            chat_id = int(data.split("_")[2])
            await self.confirm_delete_chat(query, chat_id)
        elif data.startswith("confirm_delete_"):
            chat_id = int(data.split("_")[2])
            await self.delete_chat(query, user_id, chat_id)
        elif data == "help":
            await self.show_help(query)
    
    async def show_main_menu(self, query):
        """Показать главное меню"""
        text = """🏮 Главное меню

Выберите действие:
✨ Создать новый чат с Оданн
📋 Открыть существующий чат
ℹ️ Получить справку"""
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.get_main_menu()
        )
    
    async def show_create_chat_menu(self, query):
        """Показать меню создания чата"""
        text = """✨ Создание нового чата

🎭 **Без настроек** - стандартный сценарий из аниме "Повар небесной гостиницы"

⚙️ **С настройками** - вы можете задать свой сценарий и название чата

Что выберете?"""
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.get_create_chat_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def start_chat_creation_with_settings(self, query, context):
        """Начать создание чата с настройками"""
        text = """⚙️ Создание чата с настройками

Сначала введите название для вашего чата:
(Например: "Приключение в гостинице", "Урок готовки с Оданн")"""
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.get_cancel_keyboard()
        )
        
        # Устанавливаем состояние ожидания названия
        self.user_states[query.from_user.id] = {'state': WAITING_CHAT_TITLE}
        return WAITING_CHAT_TITLE
    
    async def create_default_chat(self, query, user_id):
        """Создать чат со стандартным сценарием"""
        # Создаем чат в БД
        chat_id = self.db.create_chat(
            user_id=user_id,
            title="Общение с Оданн",
            scenario=None
        )
        
        # Создаем приветственное сообщение
        initial_message = self.ai.create_initial_message()
        self.db.add_message(chat_id, "bot", initial_message)
        
        text = f"""✅ Чат создан!

**Название:** Общение с Оданн
**Сценарий:** Стандартный (небесная гостиница)

{initial_message}

Теперь вы можете общаться с Оданн! Просто пишите сообщения, и она вам ответит."""
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.get_chat_management_keyboard(chat_id),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Устанавливаем активный чат
        self.user_states[user_id] = {'active_chat': chat_id}
    
    async def show_chat_list(self, query, user_id):
        """Показать список чатов пользователя"""
        chats = self.db.get_user_chats(user_id)
        
        if chats:
            text = f"📋 Ваши чаты ({len(chats)}):\n\nВыберите чат для продолжения общения:"
        else:
            text = "📋 У вас пока нет чатов\n\nСоздайте первый чат, чтобы начать общение с Оданн!"
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.get_chat_list_keyboard(chats)
        )
    
    async def open_chat(self, query, user_id, chat_id):
        """Открыть существующий чат"""
        chat_info = self.db.get_chat_info(chat_id)
        
        if not chat_info or chat_info[1] != user_id:
            await query.edit_message_text(
                "❌ Чат не найден или у вас нет доступа к нему.",
                reply_markup=self.keyboards.get_main_menu()
            )
            return
        
        _, _, title, scenario, creation_date = chat_info
        messages = self.db.get_chat_messages(chat_id, limit=20)
        
        # Формируем текст с историей
        text = f"💬 **{title}**\n\n"
        
        if scenario:
            text += f"📖 *Сценарий:* {scenario}\n\n"
        
        text += "📚 **Последние сообщения:**\n\n"
        
        if messages:
            for role, content, timestamp in messages[-5:]:  # Показываем последние 5 сообщений
                if role == "user":
                    text += f"👤 **Вы:** {content}\n\n"
                else:
                    text += f"🌸 **Оданн:** {content}\n\n"
        else:
            text += "*Пока нет сообщений*\n\n"
        
        text += "Напишите сообщение, чтобы продолжить общение!"
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboards.get_chat_management_keyboard(chat_id),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Устанавливаем активный чат
        self.user_states[user_id] = {'active_chat': chat_id}
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Проверяем состояние пользователя
        user_state = self.user_states.get(user_id, {})
        
        if user_state.get('state') == WAITING_CHAT_TITLE:
            await self.handle_chat_title_input(update, context, text)
        elif user_state.get('state') == WAITING_SCENARIO:
            await self.handle_scenario_input(update, context, text)
        elif user_state.get('state') == WAITING_RENAME:
            await self.handle_rename_input(update, context, text)
        elif 'active_chat' in user_state:
            await self.handle_chat_message(update, context, text, user_state['active_chat'])
        else:
            # Если нет активного чата, показываем меню
            await update.message.reply_text(
                "Выберите или создайте чат для общения с Оданн:",
                reply_markup=self.keyboards.get_main_menu()
            )
    
    async def handle_chat_title_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, title: str):
        """Обработка ввода названия чата"""
        user_id = update.effective_user.id
        
        # Сохраняем название и переходим к вводу сценария
        self.user_states[user_id] = {
            'state': WAITING_SCENARIO,
            'chat_title': title
        }
        
        text = f"""✅ Название сохранено: "{title}"

Теперь опишите сценарий для общения:
(Например: "Мы готовим вместе ужин для гостей", "Оданн показывает мне гостиницу", "Обычное дружеское общение")

Или напишите "стандартный" для использования базового сценария."""
        
        await update.message.reply_text(
            text,
            reply_markup=self.keyboards.get_cancel_keyboard()
        )
    
    async def handle_scenario_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, scenario: str):
        """Обработка ввода сценария"""
        user_id = update.effective_user.id
        user_state = self.user_states[user_id]
        title = user_state['chat_title']
        
        if scenario.lower() == "стандартный":
            scenario = None
        
        # Создаем чат в БД
        chat_id = self.db.create_chat(
            user_id=user_id,
            title=title,
            scenario=scenario
        )
        
        # Создаем приветственное сообщение
        initial_message = self.ai.create_initial_message(scenario)
        self.db.add_message(chat_id, "bot", initial_message)
        
        text = f"""✅ Чат "{title}" создан!

{initial_message}

Теперь вы можете общаться с Оданн! Просто пишите сообщения."""
        
        await update.message.reply_text(
            text,
            reply_markup=self.keyboards.get_chat_management_keyboard(chat_id)
        )
        
        # Обновляем состояние пользователя
        self.user_states[user_id] = {'active_chat': chat_id}
    
    async def handle_chat_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, chat_id: int):
        """Обработка сообщения в активном чате"""
        user_id = update.effective_user.id
        
        # Сохраняем сообщение пользователя в БД
        self.db.add_message(chat_id, "user", text)
        
        # Получаем информацию о чате
        chat_info = self.db.get_chat_info(chat_id)
        if not chat_info:
            await update.message.reply_text("❌ Чат не найден.")
            return
        
        scenario = chat_info[3]
        
        # Получаем историю сообщений
        messages = self.db.get_chat_messages(chat_id)
        message_history = [{'role': role, 'content': content} for role, content, _ in messages]
        
        # Отправляем "печатает" индикатор
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Генерируем ответ от Оданн
            response = self.ai.generate_response(message_history, scenario)
            
            # Сохраняем ответ в БД
            self.db.add_message(chat_id, "bot", response)
            
            # Отправляем ответ пользователю
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {e}")
            error_response = "Ой, простите! Что-то пошло не так... Может быть, попробуете ещё раз? 😅"
            await update.message.reply_text(error_response)
    
    async def show_help(self, query):
        """Показать справку"""
        help_text = """ℹ️ **Справка по боту**

**Как пользоваться:**
1. Создайте чат (с настройками или без)
2. Общайтесь с Оданн, просто отправляя текстовые сообщения
3. Используйте кнопки для управления чатами

**Возможности:**
• 💬 Общение с AI в роли Оданн
• 📚 Сохранение истории разговоров
• 🎭 Создание сценариев для ролевых игр
• ⚙️ Управление множественными чатами

**О персонаже:**
Оданн - главная героиня аниме "Повар небесной гостиницы". Она добрая, отзывчивая девушка-повар, которая работает в небесной гостинице для духов и демонов.

**Команды:**
/start - Главное меню"""
        
        await query.edit_message_text(
            help_text,
            reply_markup=self.keyboards.get_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    # Дополнительные методы для управления чатами
    async def start_rename_chat(self, query, context, chat_id):
        """Начать переименование чата"""
        user_id = query.from_user.id
        
        self.user_states[user_id] = {
            'state': WAITING_RENAME,
            'rename_chat_id': chat_id
        }
        
        await query.edit_message_text(
            "✏️ Введите новое название для чата:",
            reply_markup=self.keyboards.get_back_to_chat_keyboard(chat_id)
        )
    
    async def handle_rename_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, new_title: str):
        """Обработка нового названия чата"""
        user_id = update.effective_user.id
        user_state = self.user_states[user_id]
        chat_id = user_state['rename_chat_id']
        
        # Обновляем название в БД
        self.db.update_chat_title(chat_id, user_id, new_title)
        
        # Возвращаемся к чату
        self.user_states[user_id] = {'active_chat': chat_id}
        
        await update.message.reply_text(
            f"✅ Чат переименован в: '{new_title}'",
            reply_markup=self.keyboards.get_chat_management_keyboard(chat_id)
        )
    
    async def confirm_delete_chat(self, query, chat_id):
        """Подтверждение удаления чата"""
        await query.edit_message_text(
            "⚠️ Вы уверены, что хотите удалить этот чат?\n\nВся история сообщений будет утеряна!",
            reply_markup=self.keyboards.get_confirm_delete_keyboard(chat_id)
        )
    
    async def delete_chat(self, query, user_id, chat_id):
        """Удаление чата"""
        self.db.delete_chat(chat_id, user_id)
        
        # Очищаем состояние пользователя
        if user_id in self.user_states:
            self.user_states[user_id] = {}
        
        await query.edit_message_text(
            "✅ Чат удален!",
            reply_markup=self.keyboards.get_main_menu()
        )

def main():
    """Запуск бота"""
    # Получаем токен бота
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN не найден в переменных окружения!")
        return
    
    # Запускаем keep_alive для Replit
    keep_alive()
    
    # Создаем экземпляр бота
    bot = OdannaBot()
    
    # Создаем приложение
    application = Application.builder().token(bot_token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Запускаем бота
    logger.info("🌸 Бот Оданн запущен и готов к работе!")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()