"""
Модуль для работы с OpenAI API
"""
import time
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage

from src.utils.config import settings
from src.utils.logger import llm_logger, log_performance
from src.utils.error_handler import (
    OpenAIException,
    handle_exception,
    retry_on_error,
    ErrorCode
)


class LLMClient:
    """Клиент для работы с OpenAI API"""
    
    def __init__(self):
        """Инициализация клиента"""
        self.api_key = settings.openai_api_key
        openai.api_key = self.api_key
        
        # Инициализация клиента OpenAI
        self.client = OpenAI(api_key=self.api_key)
        
        # Настройки модели
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature
        self.max_tokens = settings.openai_max_tokens
        
        # LangChain компоненты
        self.chat_model = ChatOpenAI(
            model_name=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            openai_api_key=self.api_key
        )
        
        self.embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            openai_api_key=self.api_key
        )
        
        llm_logger.info(f"LLM Client initialized with model: {self.model}")
    
    @retry_on_error(max_retries=3, delay=1.0)
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Генерация эмбеддинга для текста
        
        Args:
            text: Текст для векторизации
        
        Returns:
            Вектор эмбеддинга
        """
        start_time = time.time()
        
        try:
            # Очистить и подготовить текст
            text = text.strip()
            if not text:
                raise OpenAIException("Empty text provided for embedding")
            
            # Генерация эмбеддинга
            embedding = await self.embeddings.aembed_query(text)
            
            duration = time.time() - start_time
            log_performance("generate_embedding", duration, success=True)
            
            llm_logger.debug(f"Generated embedding for text (length: {len(text)})")
            
            return embedding
            
        except Exception as e:
            duration = time.time() - start_time
            log_performance("generate_embedding", duration, success=False)
            
            error = handle_exception(e, {
                "operation": "generate_embedding",
                "text_length": len(text)
            })
            llm_logger.error(f"Failed to generate embedding: {str(error)}")
            raise OpenAIException(f"Embedding generation failed: {str(e)}")
    
    @retry_on_error(max_retries=3, delay=1.0)
    async def generate_response(
        self,
        query: str,
        context: List[str],
        system_prompt: str,
        agent_type: str = "general"
    ) -> str:
        """
        Генерация ответа на основе контекста
        
        Args:
            query: Запрос пользователя
            context: Список релевантных фрагментов текста
            system_prompt: Системный промпт для агента
            agent_type: Тип агента (finance, legal, project)
        
        Returns:
            Сгенерированный ответ
        """
        start_time = time.time()
        
        try:
            # Подготовить контекст
            context_text = self._prepare_context(context)
            
            # Создать промпт
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=self._build_prompt(query, context_text))
            ]
            
            # Генерация ответа
            response = await self.chat_model.agenerate([messages])
            answer = response.generations[0][0].text.strip()
            
            duration = time.time() - start_time
            log_performance("generate_response", duration, success=True)
            
            llm_logger.info(
                f"Generated response for agent: {agent_type} | "
                f"Query length: {len(query)} | "
                f"Context chunks: {len(context)} | "
                f"Response length: {len(answer)}"
            )
            
            return answer
            
        except Exception as e:
            duration = time.time() - start_time
            log_performance("generate_response", duration, success=False)
            
            error = handle_exception(e, {
                "operation": "generate_response",
                "agent_type": agent_type,
                "query": query[:100]
            })
            llm_logger.error(f"Failed to generate response: {str(error)}")
            raise OpenAIException(f"Response generation failed: {str(e)}")
    
    @retry_on_error(max_retries=3, delay=1.0)
    async def generate_fallback_response(
        self,
        query: str,
        agent_type: str = "general"
    ) -> str:
        """
        Генерация ответа на основе знаний модели (fallback)
        Используется когда нет данных в векторной базе
        
        Args:
            query: Запрос пользователя
            agent_type: Тип агента
        
        Returns:
            Ответ с предупреждением и ссылкой на источник
        """
        start_time = time.time()
        
        try:
            system_prompt = self._get_fallback_system_prompt(agent_type)
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ]
            
            response = await self.chat_model.agenerate([messages])
            answer = response.generations[0][0].text.strip()
            
            # Добавить предупреждение
            warning = (
                "\n\n⚠️ **Внимание**: Информация по вашему запросу отсутствует в базе знаний компании. "
                "Ответ сформирован на основе общих знаний модели. "
                "Для получения точной информации обратитесь к соответствующему специалисту."
            )
            
            answer = answer + warning
            
            duration = time.time() - start_time
            log_performance("generate_fallback_response", duration, success=True)
            
            llm_logger.warning(
                f"Generated fallback response for agent: {agent_type} | "
                f"Query: {query[:100]}"
            )
            
            return answer
            
        except Exception as e:
            duration = time.time() - start_time
            log_performance("generate_fallback_response", duration, success=False)
            
            error = handle_exception(e, {
                "operation": "generate_fallback_response",
                "agent_type": agent_type
            })
            llm_logger.error(f"Failed to generate fallback response: {str(error)}")
            raise OpenAIException(f"Fallback response generation failed: {str(e)}")
    
    def _prepare_context(self, context: List[str]) -> str:
        """Подготовить контекст для промпта"""
        if not context:
            return "Контекст отсутствует."
        
        context_parts = []
        for i, chunk in enumerate(context, 1):
            context_parts.append(f"[Фрагмент {i}]\n{chunk}\n")
        
        return "\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Построить промпт для генерации ответа"""
        prompt = f"""На основе предоставленного контекста, ответь на вопрос пользователя.

КОНТЕКСТ:
{context}

ВОПРОС ПОЛЬЗОВАТЕЛЯ:
{query}

ИНСТРУКЦИИ:
1. Используй ТОЛЬКО информацию из контекста выше
2. Если в контексте нет прямого ответа, сообщи об этом явно
3. Будь точным и конкретным
4. Структурируй ответ для удобства чтения
5. Если нужно, приведи конкретные цифры и даты из контекста

ОТВЕТ:"""
        
        return prompt
    
    def _get_fallback_system_prompt(self, agent_type: str) -> str:
        """Получить системный промпт для fallback ответа"""
        base_prompt = """Ты - корпоративный ассистент. 
Информация по запросу пользователя отсутствует в базе знаний компании.
Предоставь общий ответ на основе своих знаний, но укажи, что это общая информация.
Будь полезным, но осторожным в рекомендациях.
"""
        
        agent_prompts = {
            "finance": base_prompt + "\nТы специализируешься на финансовых вопросах.",
            "legal": base_prompt + "\nТы специализируешься на юридических вопросах.",
            "project": base_prompt + "\nТы специализируешься на проектном управлении."
        }
        
        return agent_prompts.get(agent_type, base_prompt)


# Глобальный экземпляр клиента
llm_client = LLMClient()
