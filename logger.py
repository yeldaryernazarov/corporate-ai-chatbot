"""
Модуль настройки логирования
"""
import logging
import sys
from typing import Optional
import colorlog
from pythonjsonlogger import jsonlogger

from src.utils.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Кастомный JSON formatter для структурированного логирования"""
    
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName


def setup_logger(
    name: str,
    level: Optional[str] = None,
    use_json: bool = False
) -> logging.Logger:
    """
    Настроить логгер с цветным выводом для разработки или JSON для продакшн
    
    Args:
        name: Имя логгера
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Использовать JSON формат
    
    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    
    # Установить уровень логирования
    log_level = level or settings.log_level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Удалить существующие обработчики
    logger.handlers.clear()
    
    # Создать обработчик для вывода в консоль
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))
    
    if use_json or settings.is_production():
        # JSON формат для продакшн
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            rename_fields={'timestamp': 'timestamp'}
        )
    else:
        # Цветной формат для разработки
        formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Предотвратить дублирование логов
    logger.propagate = False
    
    return logger


# Создать основные логгеры приложения
main_logger = setup_logger("main")
agent_logger = setup_logger("agents")
telegram_logger = setup_logger("telegram")
llm_logger = setup_logger("llm")
vector_logger = setup_logger("vector_store")
error_logger = setup_logger("errors", level="ERROR")


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Optional[dict] = None
) -> None:
    """
    Логировать ошибку с контекстом
    
    Args:
        logger: Логгер для записи
        error: Исключение
        context: Дополнительный контекст
    """
    error_msg = f"{type(error).__name__}: {str(error)}"
    
    if context:
        error_msg += f" | Context: {context}"
    
    logger.error(error_msg, exc_info=True)
    error_logger.error(error_msg, exc_info=True)


def log_agent_action(
    agent_name: str,
    action: str,
    user_id: int,
    query: str,
    result: str = "success"
) -> None:
    """
    Логировать действие агента
    
    Args:
        agent_name: Имя агента
        action: Действие
        user_id: ID пользователя
        query: Запрос пользователя
        result: Результат (success/error)
    """
    agent_logger.info(
        f"Agent: {agent_name} | Action: {action} | User: {user_id} | "
        f"Query: {query[:50]}... | Result: {result}"
    )


def log_performance(
    operation: str,
    duration: float,
    success: bool = True
) -> None:
    """
    Логировать производительность операции
    
    Args:
        operation: Название операции
        duration: Длительность в секундах
        success: Успешность выполнения
    """
    status = "SUCCESS" if success else "FAILED"
    main_logger.info(
        f"Performance: {operation} | Duration: {duration:.3f}s | Status: {status}"
    )
    
    # Предупреждение при превышении максимального времени
    if duration > settings.max_response_time:
        main_logger.warning(
            f"Response time exceeded: {duration:.3f}s > {settings.max_response_time}s "
            f"for operation: {operation}"
        )
