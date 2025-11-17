"""
Базовый класс для всех агентов
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import time

from src.core.llm_client import llm_client
from src.core.vector_store import vector_store
from src.utils.logger import agent_logger, log_agent_action, log_performance
from src.utils.error_handler import (
    AgentException,
    NoDataFoundException,
    handle_exception
)


class BaseAgent(ABC):
    """Базовый класс для всех агентов чатбота"""
    
    def __init__(self, agent_type: str, namespace: str):
        """
        Инициализация агента
        
        Args:
            agent_type: Тип агента (finance, legal, project)
            namespace: Namespace в Pinecone для этого агента
        """
        self.agent_type = agent_type
        self.namespace = namespace
        self.system_prompt = self._get_system_prompt()
        
        agent_logger.info(f"Initialized {agent_type} agent with namespace: {namespace}")
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """
        Получить системный промпт для агента
        
        Returns:
            Системный промпт
        """
        pass
    
    @abstractmethod
    def _get_welcome_message(self) -> str:
        """
        Получить приветственное сообщение для агента
        
        Returns:
            Приветственное сообщение
        """
        pass
    
    async def process_query(
        self,
        query: str,
        user_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Обработать запрос пользователя
        
        Args:
            query: Запрос пользователя
            user_id: ID пользователя
            metadata: Дополнительные метаданные
        
        Returns:
            Словарь с ответом и метаинформацией
        """
        start_time = time.time()
        
        try:
            agent_logger.info(
                f"Processing query for {self.agent_type} agent | "
                f"User: {user_id} | Query: {query[:100]}..."
            )
            
            # 1. Генерация эмбеддинга для запроса
            query_embedding = await llm_client.generate_embedding(query)
            
            # 2. Поиск релевантных документов в Pinecone
            matches = await vector_store.search(
                query_embedding=query_embedding,
                namespace=self.namespace,
                filter_dict=metadata.get('filters') if metadata else None
            )
            
            # 3. Извлечение контекста из результатов
            context = vector_store.extract_context_from_matches(matches)
            
            # 4. Генерация ответа
            if context:
                # Ответ на основе найденных документов
                answer = await llm_client.generate_response(
                    query=query,
                    context=context,
                    system_prompt=self.system_prompt,
                    agent_type=self.agent_type
                )
                
                response_type = "knowledge_base"
                
            else:
                # Fallback: ответ на основе знаний модели
                answer = await llm_client.generate_fallback_response(
                    query=query,
                    agent_type=self.agent_type
                )
                
                response_type = "fallback"
                
                agent_logger.warning(
                    f"No context found for query, using fallback response | "
                    f"Agent: {self.agent_type} | User: {user_id}"
                )
            
            # 5. Подготовить результат
            duration = time.time() - start_time
            log_performance(f"{self.agent_type}_query", duration, success=True)
            
            log_agent_action(
                agent_name=self.agent_type,
                action="process_query",
                user_id=user_id,
                query=query,
                result="success"
            )
            
            result = {
                'success': True,
                'answer': answer,
                'agent_type': self.agent_type,
                'response_type': response_type,
                'num_sources': len(context),
                'duration': duration,
                'metadata': {
                    'similarity_scores': [m['score'] for m in matches] if matches else [],
                    'sources': [m['metadata'].get('source') for m in matches] if matches else []
                }
            }
            
            agent_logger.info(
                f"Successfully processed query | Agent: {self.agent_type} | "
                f"Response type: {response_type} | Duration: {duration:.2f}s"
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            log_performance(f"{self.agent_type}_query", duration, success=False)
            
            error = handle_exception(e, {
                "agent_type": self.agent_type,
                "user_id": user_id,
                "query": query[:100]
            })
            
            log_agent_action(
                agent_name=self.agent_type,
                action="process_query",
                user_id=user_id,
                query=query,
                result="error"
            )
            
            agent_logger.error(
                f"Failed to process query | Agent: {self.agent_type} | "
                f"Error: {str(error)}"
            )
            
            # Вернуть структурированную ошибку
            return {
                'success': False,
                'error': str(error),
                'error_code': error.error_code.value if hasattr(error, 'error_code') else 'E001',
                'agent_type': self.agent_type,
                'user_message': error.get_user_message() if hasattr(error, 'get_user_message') else str(error)
            }
    
    def get_welcome_message(self) -> str:
        """
        Получить приветственное сообщение
        
        Returns:
            Приветственное сообщение
        """
        return self._get_welcome_message()
    
    def get_help_message(self) -> str:
        """
        Получить справочное сообщение
        
        Returns:
            Справочное сообщение
        """
        return f"""
**Помощь по работе с {self.agent_type.upper()} агентом**

{self._get_welcome_message()}

**Доступные команды:**
- Просто задайте вопрос естественным языком
- /help - показать эту справку
- /back - вернуться к выбору агента

**Советы для лучших результатов:**
- Формулируйте вопросы максимально конкретно
- Укажите детали: даты, суммы, названия проектов
- Используйте ключевые слова из вашей области

Задайте ваш вопрос!
"""
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику работы агента
        
        Returns:
            Статистика агента
        """
        try:
            index_stats = await vector_store.get_stats()
            
            namespace_stats = index_stats.get('namespaces', {}).get(self.namespace, {})
            
            return {
                'agent_type': self.agent_type,
                'namespace': self.namespace,
                'total_documents': namespace_stats.get('vector_count', 0),
                'status': 'active'
            }
            
        except Exception as e:
            agent_logger.error(f"Failed to get stats for {self.agent_type}: {str(e)}")
            return {
                'agent_type': self.agent_type,
                'namespace': self.namespace,
                'status': 'error',
                'error': str(e)
            }
