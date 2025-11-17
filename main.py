"""
Главный файл запуска корпоративного AI-чатбота
"""
import sys
import asyncio
from pathlib import Path

# Добавить корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from src.core.telegram_bot import telegram_bot
from src.utils.logger import main_logger
from src.utils.config import settings


def print_startup_banner():
    """Вывести информацию о запуске"""
    banner = """
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║     Корпоративный AI-Чатбот                          ║
║     Три специализированных агента                    ║
║                                                       ║
║     💰 Финансовый | ⚖️ Юридический | 📊 Проектный    ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
"""
    print(banner)
    main_logger.info("=" * 60)
    main_logger.info("CORPORATE AI CHATBOT STARTING")
    main_logger.info("=" * 60)
    main_logger.info(f"Environment: {settings.app_env}")
    main_logger.info(f"Log Level: {settings.log_level}")
    main_logger.info(f"OpenAI Model: {settings.openai_model}")
    main_logger.info(f"Pinecone Index: {settings.pinecone_index_name}")
    main_logger.info("=" * 60)


def check_configuration():
    """Проверить конфигурацию перед запуском"""
    main_logger.info("Checking configuration...")
    
    required_settings = [
        ('OPENAI_API_KEY', settings.openai_api_key),
        ('PINECONE_API_KEY', settings.pinecone_api_key),
        ('TELEGRAM_BOT_TOKEN', settings.telegram_bot_token)
    ]
    
    missing_settings = []
    for name, value in required_settings:
        if not value or value == f"your-{name.lower().replace('_', '-')}-here":
            missing_settings.append(name)
    
    if missing_settings:
        main_logger.error(
            f"Missing required configuration: {', '.join(missing_settings)}"
        )
        main_logger.error("Please check your .env file and set all required variables")
        return False
    
    main_logger.info("✓ Configuration check passed")
    return True


async def initialize_services():
    """Инициализировать все сервисы"""
    main_logger.info("Initializing services...")
    
    try:
        # Проверить подключение к Pinecone
        from src.core.vector_store import vector_store
        stats = await vector_store.get_stats()
        main_logger.info(
            f"✓ Pinecone connected: {stats['total_vectors']} vectors in index"
        )
        
        # Проверить OpenAI
        from src.core.llm_client import llm_client
        main_logger.info(f"✓ OpenAI client initialized: model={llm_client.model}")
        
        # Проверить агентов
        from src.agents.finance_agent import finance_agent
        from src.agents.legal_agent import legal_agent
        from src.agents.project_agent import project_agent
        
        main_logger.info("✓ All agents initialized")
        
        main_logger.info("✓ All services initialized successfully")
        return True
        
    except Exception as e:
        main_logger.error(f"✗ Failed to initialize services: {str(e)}")
        return False


def main():
    """Главная функция"""
    # Вывести баннер
    print_startup_banner()
    
    # Проверить конфигурацию
    if not check_configuration():
        main_logger.error("Configuration check failed. Exiting.")
        sys.exit(1)
    
    # Инициализировать сервисы
    loop = asyncio.get_event_loop()
    if not loop.run_until_complete(initialize_services()):
        main_logger.error("Service initialization failed. Exiting.")
        sys.exit(1)
    
    # Запустить бота
    try:
        main_logger.info("Starting Telegram bot...")
        main_logger.info("Bot is ready to accept messages!")
        main_logger.info("Press Ctrl+C to stop")
        
        telegram_bot.run()
        
    except KeyboardInterrupt:
        main_logger.info("\n")
        main_logger.info("Shutting down gracefully...")
        main_logger.info("Bot stopped")
        
    except Exception as e:
        main_logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
