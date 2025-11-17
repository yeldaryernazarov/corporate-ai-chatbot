"""
Модуль обработки ошибок
"""
from typing import Optional, Dict, Any
from enum import Enum
import traceback

from src.utils.logger import error_logger


class ErrorCode(Enum):
    """Коды ошибок системы"""
    # Общие ошибки
    UNKNOWN_ERROR = "E001"
    CONFIGURATION_ERROR = "E002"
    
    # Ошибки API
    OPENAI_API_ERROR = "E101"
    OPENAI_RATE_LIMIT = "E102"
    OPENAI_TIMEOUT = "E103"
    
    PINECONE_API_ERROR = "E201"
    PINECONE_CONNECTION_ERROR = "E202"
    
    TELEGRAM_API_ERROR = "E301"
    TELEGRAM_SEND_ERROR = "E302"
    
    # Ошибки данных
    NO_DATA_FOUND = "E401"
    INVALID_QUERY = "E402"
    EMPTY_RESPONSE = "E403"
    
    # Ошибки агентов
    AGENT_NOT_FOUND = "E501"
    AGENT_EXECUTION_ERROR = "E502"
    
    # Ошибки аутентификации
    UNAUTHORIZED_USER = "E601"
    ACCESS_DENIED = "E602"


class ChatbotException(Exception):
    """Базовое исключение для чатбота"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать исключение в словарь"""
        return {
            "error": True,
            "code": self.error_code.value,
            "message": self.message,
            "details": self.details
        }
    
    def get_user_message(self) -> str:
        """Получить сообщение для пользователя"""
        user_messages = {
            ErrorCode.NO_DATA_FOUND: (
                "К сожалению, я не нашел информацию по вашему запросу в базе знаний. "
                "Попробуйте переформулировать вопрос или обратитесь к специалисту."
            ),
            ErrorCode.OPENAI_API_ERROR: (
                "Произошла ошибка при обработке запроса. "
                "Пожалуйста, попробуйте еще раз через некоторое время."
            ),
            ErrorCode.OPENAI_RATE_LIMIT: (
                "Превышен лимит запросов. "
                "Пожалуйста, подождите немного и попробуйте снова."
            ),
            ErrorCode.PINECONE_API_ERROR: (
                "Ошибка при поиске в базе знаний. "
                "Пожалуйста, попробуйте еще раз."
            ),
            ErrorCode.INVALID_QUERY: (
                "Не удалось понять ваш запрос. "
                "Пожалуйста, сформулируйте вопрос более подробно."
            ),
            ErrorCode.UNAUTHORIZED_USER: (
                "У вас нет доступа к этому боту. "
                "Пожалуйста, свяжитесь с администратором."
            ),
            ErrorCode.AGENT_NOT_FOUND: (
                "Выбранный агент не найден. "
                "Используйте команды /finance, /legal или /project."
            )
        }
        
        return user_messages.get(
            self.error_code,
            "Произошла ошибка. Пожалуйста, попробуйте еще раз или обратитесь в поддержку."
        )


class OpenAIException(ChatbotException):
    """Исключение для ошибок OpenAI API"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.OPENAI_API_ERROR, details)


class PineconeException(ChatbotException):
    """Исключение для ошибок Pinecone"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.PINECONE_API_ERROR, details)


class TelegramException(ChatbotException):
    """Исключение для ошибок Telegram API"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.TELEGRAM_API_ERROR, details)


class NoDataFoundException(ChatbotException):
    """Исключение когда данные не найдены в базе знаний"""
    
    def __init__(self, query: str, details: Optional[Dict[str, Any]] = None):
        message = f"No data found for query: {query}"
        super().__init__(message, ErrorCode.NO_DATA_FOUND, details)


class AgentException(ChatbotException):
    """Исключение для ошибок агентов"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.AGENT_EXECUTION_ERROR, details)


def handle_exception(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    log_traceback: bool = True
) -> ChatbotException:
    """
    Обработать исключение и преобразовать в ChatbotException
    
    Args:
        error: Исходное исключение
        context: Контекст ошибки
        log_traceback: Логировать traceback
    
    Returns:
        ChatbotException с соответствующими данными
    """
    # Если уже ChatbotException, вернуть как есть
    if isinstance(error, ChatbotException):
        error_logger.error(f"ChatbotException: {error.message}", extra=context)
        return error
    
    # Логировать traceback
    if log_traceback:
        error_logger.error(
            f"Unhandled exception: {type(error).__name__}: {str(error)}",
            exc_info=True,
            extra=context
        )
    
    # Преобразовать в ChatbotException
    details = context or {}
    details["original_error"] = str(error)
    details["error_type"] = type(error).__name__
    
    return ChatbotException(
        message=str(error),
        error_code=ErrorCode.UNKNOWN_ERROR,
        details=details
    )


def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """
    Декоратор для повторной попытки выполнения функции при ошибке
    
    Args:
        max_retries: Максимальное количество попыток
        delay: Задержка между попытками в секундах
    """
    import time
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}"
                    )
                    
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
            
            # Если все попытки неудачны, выбросить последнее исключение
            raise handle_exception(last_exception, {
                "function": func.__name__,
                "max_retries": max_retries,
                "attempts": max_retries
            })
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}"
                    )
                    
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
            
            raise handle_exception(last_exception, {
                "function": func.__name__,
                "max_retries": max_retries,
                "attempts": max_retries
            })
        
        # Проверить, является ли функция асинхронной
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


import asyncio
