"""
Модуль конфигурации приложения
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # OpenAI Settings
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-mini", env="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", 
        env="OPENAI_EMBEDDING_MODEL"
    )
    openai_temperature: float = Field(default=0.3, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    
    # Pinecone Settings
    pinecone_api_key: str = Field(..., env="PINECONE_API_KEY")
    pinecone_environment: str = Field(..., env="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field(default="corporate-kb", env="PINECONE_INDEX_NAME")
    pinecone_dimension: int = Field(default=1536, env="PINECONE_DIMENSION")
    pinecone_metric: str = Field(default="cosine", env="PINECONE_METRIC")
    
    # Telegram Settings
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    telegram_webhook_url: str = Field(default="", env="TELEGRAM_WEBHOOK_URL")
    
    # n8n Settings
    n8n_webhook_url: str = Field(default="", env="N8N_WEBHOOK_URL")
    n8n_api_key: str = Field(default="", env="N8N_API_KEY")
    
    # Application Settings
    app_env: str = Field(default="development", env="APP_ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    max_response_time: int = Field(default=3, env="MAX_RESPONSE_TIME")
    min_accuracy: float = Field(default=0.85, env="MIN_ACCURACY")
    
    # Agent Settings
    finance_agent_enabled: bool = Field(default=True, env="FINANCE_AGENT_ENABLED")
    legal_agent_enabled: bool = Field(default=True, env="LEGAL_AGENT_ENABLED")
    project_agent_enabled: bool = Field(default=True, env="PROJECT_AGENT_ENABLED")
    
    # Vector Search Settings
    top_k_results: int = Field(default=5, env="TOP_K_RESULTS")
    similarity_threshold: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    
    # Rate Limiting
    max_requests_per_minute: int = Field(default=10, env="MAX_REQUESTS_PER_MINUTE")
    max_requests_per_hour: int = Field(default=100, env="MAX_REQUESTS_PER_HOUR")
    
    # Database
    database_url: str = Field(
        default="sqlite:///./corporate_chatbot.db",
        env="DATABASE_URL"
    )
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Security
    allowed_user_ids: str = Field(default="", env="ALLOWED_USER_IDS")
    admin_user_ids: str = Field(default="", env="ADMIN_USER_IDS")
    
    # Monitoring
    sentry_dsn: str = Field(default="", env="SENTRY_DSN")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_allowed_user_ids(self) -> List[int]:
        """Получить список разрешенных ID пользователей"""
        if not self.allowed_user_ids:
            return []
        return [int(uid.strip()) for uid in self.allowed_user_ids.split(",") if uid.strip()]
    
    def get_admin_user_ids(self) -> List[int]:
        """Получить список ID администраторов"""
        if not self.admin_user_ids:
            return []
        return [int(uid.strip()) for uid in self.admin_user_ids.split(",") if uid.strip()]
    
    def is_production(self) -> bool:
        """Проверить, является ли окружение продакшн"""
        return self.app_env.lower() == "production"


# Глобальный экземпляр настроек
settings = Settings()
