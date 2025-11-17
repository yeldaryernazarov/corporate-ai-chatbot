"""
Telegram бот для взаимодействия с пользователями
"""
import asyncio
from typing import Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from src.agents.finance_agent import finance_agent
from src.agents.legal_agent import legal_agent
from src.agents.project_agent import project_agent
from src.utils.config import settings
from src.utils.logger import telegram_logger, log_agent_action
from src.utils.error_handler import ChatbotException, handle_exception, ErrorCode


class TelegramBot:
    """Telegram бот для корпоративного чатбота"""
    
    def __init__(self):
        """Инициализация бота"""
        self.token = settings.telegram_bot_token
        self.application = Application.builder().token(self.token).build()
        
        # Хранилище активных агентов для пользователей
        self.user_agents: Dict[int, str] = {}
        
        # Доступные агенты
        self.agents = {
            'finance': finance_agent,
            'legal': legal_agent,
            'project': project_agent
        }
        
        # Настроить обработчики
        self._setup_handlers()
        
        telegram_logger.info("Telegram bot initialized")
    
    def _setup_handlers(self):
        """Настроить обработчики команд и сообщений"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("finance", self.finance_command))
        self.application.add_handler(CommandHandler("legal", self.legal_command))
        self.application.add_handler(CommandHandler("project", self.project_command))
        self.application.add_handler(CommandHandler("back", self.back_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        
        # Callback queries (для inline кнопок)
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Обработчик текстовых сообщений
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        telegram_logger.info("Handlers configured")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать команду /start"""
        user = update.effective_user
        user_id = user.id
        
        telegram_logger.info(f"User {user_id} ({user.username}) started bot")
        
        # Проверить авторизацию если настроена
        if not self._is_authorized(user_id):
            await update.message.reply_text(
                "❌ У вас нет доступа к этому боту.\n"
                "Пожалуйста, свяжитесь с администратором."
            )
            telegram_logger.warning(f"Unauthorized access attempt from user {user_id}")
            return
        
        # Приветственное сообщение
        welcome_text = f"""👋 **Добро пожаловать, {user.first_name}!**

Я корпоративный AI-ассистент с тремя специализированными агентами:

💰 **Финансовый ассистент** - бюджеты, оплаты, лимиты
⚖️ **Юридический ассистент** - документы, контракты, НПА
📊 **Проектный ассистент** - задачи, дедлайны, статусы

Выберите агента, чтобы начать работу:"""
        
        keyboard = self._get_agent_selection_keyboard()
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать команду /help"""
        user_id = update.effective_user.id
        
        # Если у пользователя выбран агент, показать справку агента
        if user_id in self.user_agents:
            agent_type = self.user_agents[user_id]
            agent = self.agents[agent_type]
            help_text = agent.get_help_message()
        else:
            # Общая справка
            help_text = """
📖 **Справка по использованию бота**

**Доступные команды:**
/start - Начать работу и выбрать агента
/finance - Переключиться на финансового ассистента
/legal - Переключиться на юридического ассистента
/project - Переключиться на проектного ассистента
/back - Вернуться к выбору агента
/stats - Статистика работы агентов
/help - Показать эту справку

**Как пользоваться:**
1. Выберите нужного агента командой или через кнопки
2. Задайте вопрос естественным языком
3. Получите ответ на основе корпоративной базы знаний

**Советы:**
✓ Формулируйте вопросы конкретно
✓ Указывайте детали: даты, суммы, названия
✓ Используйте ключевые слова

Для выбора агента нажмите /start
"""
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def finance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Переключиться на финансового агента"""
        await self._switch_agent(update, 'finance')
    
    async def legal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Переключиться на юридического агента"""
        await self._switch_agent(update, 'legal')
    
    async def project_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Переключиться на проектного агента"""
        await self._switch_agent(update, 'project')
    
    async def back_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Вернуться к выбору агента"""
        user_id = update.effective_user.id
        
        # Удалить выбранного агента
        if user_id in self.user_agents:
            del self.user_agents[user_id]
        
        text = "Выберите агента для работы:"
        keyboard = self._get_agent_selection_keyboard()
        
        await update.message.reply_text(
            text,
            reply_markup=keyboard
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику работы агентов"""
        user_id = update.effective_user.id
        
        # Проверить права администратора
        if not self._is_admin(user_id):
            await update.message.reply_text(
                "❌ Эта команда доступна только администраторам."
            )
            return
        
        await update.message.reply_text("📊 Собираю статистику...")
        
        try:
            stats_text = "📊 **Статистика работы агентов:**\n\n"
            
            for agent_name, agent in self.agents.items():
                agent_stats = await agent.get_stats()
                
                emoji = {
                    'finance': '💰',
                    'legal': '⚖️',
                    'project': '📊'
                }.get(agent_name, '📌')
                
                stats_text += (
                    f"{emoji} **{agent_name.upper()}**\n"
                    f"└ Документов: {agent_stats.get('total_documents', 0)}\n"
                    f"└ Статус: {agent_stats.get('status', 'unknown')}\n\n"
                )
            
            await update.message.reply_text(stats_text, parse_mode='Markdown')
            
        except Exception as e:
            error = handle_exception(e)
            await update.message.reply_text(
                f"❌ Ошибка при получении статистики: {str(error)}"
            )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать нажатие inline кнопок"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        agent_type = query.data
        
        if agent_type in self.agents:
            self.user_agents[user_id] = agent_type
            agent = self.agents[agent_type]
            
            welcome_message = agent.get_welcome_message()
            
            await query.edit_message_text(
                text=welcome_message,
                parse_mode='Markdown'
            )
            
            telegram_logger.info(f"User {user_id} switched to {agent_type} agent")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать текстовое сообщение от пользователя"""
        user = update.effective_user
        user_id = user.id
        query = update.message.text
        
        telegram_logger.info(f"Received message from user {user_id}: {query[:100]}...")
        
        # Проверить авторизацию
        if not self._is_authorized(user_id):
            await update.message.reply_text(
                "❌ У вас нет доступа к этому боту."
            )
            return
        
        # Проверить, выбран ли агент
        if user_id not in self.user_agents:
            await update.message.reply_text(
                "Пожалуйста, сначала выберите агента с помощью команды /start"
            )
            return
        
        # Показать индикатор "печатает"
        await update.message.chat.send_action("typing")
        
        try:
            # Получить агента
            agent_type = self.user_agents[user_id]
            agent = self.agents[agent_type]
            
            # Обработать запрос
            result = await agent.process_query(
                query=query,
                user_id=user_id
            )
            
            if result['success']:
                # Успешный ответ
                answer = result['answer']
                response_type = result['response_type']
                
                # Добавить информацию об источниках если есть
                if result['num_sources'] > 0:
                    footer = f"\n\n📚 Использовано источников: {result['num_sources']}"
                    answer += footer
                
                await update.message.reply_text(
                    answer,
                    parse_mode='Markdown'
                )
                
            else:
                # Ошибка
                error_message = result.get('user_message', 'Произошла ошибка при обработке запроса.')
                await update.message.reply_text(
                    f"❌ {error_message}"
                )
        
        except Exception as e:
            error = handle_exception(e, {
                "user_id": user_id,
                "query": query[:100]
            })
            
            telegram_logger.error(f"Error handling message: {str(error)}")
            
            if isinstance(error, ChatbotException):
                error_message = error.get_user_message()
            else:
                error_message = "Произошла ошибка. Пожалуйста, попробуйте еще раз."
            
            await update.message.reply_text(f"❌ {error_message}")
    
    async def _switch_agent(self, update: Update, agent_type: str):
        """Переключиться на другого агента"""
        user_id = update.effective_user.id
        
        if agent_type not in self.agents:
            await update.message.reply_text(
                f"❌ Агент '{agent_type}' не найден."
            )
            return
        
        self.user_agents[user_id] = agent_type
        agent = self.agents[agent_type]
        
        welcome_message = agent.get_welcome_message()
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown'
        )
        
        telegram_logger.info(f"User {user_id} switched to {agent_type} agent")
    
    def _get_agent_selection_keyboard(self) -> InlineKeyboardMarkup:
        """Получить клавиатуру для выбора агента"""
        keyboard = [
            [InlineKeyboardButton("💰 Финансовый", callback_data="finance")],
            [InlineKeyboardButton("⚖️ Юридический", callback_data="legal")],
            [InlineKeyboardButton("📊 Проектный", callback_data="project")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _is_authorized(self, user_id: int) -> bool:
        """Проверить авторизацию пользователя"""
        allowed_users = settings.get_allowed_user_ids()
        
        # Если список пустой, доступ открыт для всех
        if not allowed_users:
            return True
        
        return user_id in allowed_users
    
    def _is_admin(self, user_id: int) -> bool:
        """Проверить права администратора"""
        admin_users = settings.get_admin_user_ids()
        return user_id in admin_users
    
    def run(self):
        """Запустить бота"""
        telegram_logger.info("Starting Telegram bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


# Создать глобальный экземпляр бота
telegram_bot = TelegramBot()
