"""
Модуль для работы с Pinecone векторной базой данных
"""
import time
from typing import List, Dict, Any, Optional, Tuple
from pinecone import Pinecone, ServerlessSpec
import asyncio

from src.utils.config import settings
from src.utils.logger import vector_logger, log_performance
from src.utils.error_handler import (
    PineconeException,
    NoDataFoundException,
    handle_exception,
    retry_on_error
)


class VectorStore:
    """Клиент для работы с Pinecone векторной базой"""
    
    def __init__(self):
        """Инициализация клиента Pinecone"""
        try:
            # Инициализация Pinecone
            self.pc = Pinecone(api_key=settings.pinecone_api_key)
            
            self.index_name = settings.pinecone_index_name
            self.dimension = settings.pinecone_dimension
            self.metric = settings.pinecone_metric
            
            # Подключение к индексу
            self._ensure_index_exists()
            self.index = self.pc.Index(self.index_name)
            
            vector_logger.info(f"VectorStore initialized with index: {self.index_name}")
            
        except Exception as e:
            error_msg = f"Failed to initialize Pinecone: {str(e)}"
            vector_logger.error(error_msg)
            raise PineconeException(error_msg)
    
    def _ensure_index_exists(self):
        """Проверить существование индекса, создать если нужно"""
        try:
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                vector_logger.info(f"Creating new index: {self.index_name}")
                
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric=self.metric,
                    spec=ServerlessSpec(
                        cloud='aws',
                        region=settings.pinecone_environment
                    )
                )
                
                # Подождать создания индекса
                time.sleep(10)
                vector_logger.info(f"Index {self.index_name} created successfully")
            else:
                vector_logger.info(f"Using existing index: {self.index_name}")
                
        except Exception as e:
            error_msg = f"Failed to ensure index exists: {str(e)}"
            vector_logger.error(error_msg)
            raise PineconeException(error_msg)
    
    @retry_on_error(max_retries=3, delay=1.0)
    async def upsert_documents(
        self,
        documents: List[Dict[str, Any]],
        namespace: str = "default"
    ) -> int:
        """
        Загрузить документы в векторную базу
        
        Args:
            documents: Список документов с полями: id, embedding, metadata
            namespace: Namespace для разделения данных по агентам
        
        Returns:
            Количество загруженных документов
        """
        start_time = time.time()
        
        try:
            if not documents:
                raise PineconeException("No documents provided for upsert")
            
            # Подготовить векторы для загрузки
            vectors = []
            for doc in documents:
                if not all(k in doc for k in ['id', 'embedding', 'metadata']):
                    raise PineconeException(f"Invalid document format: {doc.keys()}")
                
                vectors.append({
                    'id': doc['id'],
                    'values': doc['embedding'],
                    'metadata': doc['metadata']
                })
            
            # Загрузить векторы батчами
            batch_size = 100
            total_upserted = 0
            
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                
                # Выполнить в executor для асинхронности
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.index.upsert(
                        vectors=batch,
                        namespace=namespace
                    )
                )
                
                total_upserted += len(batch)
                vector_logger.debug(f"Upserted batch {i // batch_size + 1}: {len(batch)} vectors")
            
            duration = time.time() - start_time
            log_performance("upsert_documents", duration, success=True)
            
            vector_logger.info(
                f"Successfully upserted {total_upserted} documents to namespace: {namespace}"
            )
            
            return total_upserted
            
        except Exception as e:
            duration = time.time() - start_time
            log_performance("upsert_documents", duration, success=False)
            
            error = handle_exception(e, {
                "operation": "upsert_documents",
                "namespace": namespace,
                "num_documents": len(documents)
            })
            vector_logger.error(f"Failed to upsert documents: {str(error)}")
            raise PineconeException(f"Failed to upsert documents: {str(e)}")
    
    @retry_on_error(max_retries=3, delay=1.0)
    async def search(
        self,
        query_embedding: List[float],
        namespace: str = "default",
        top_k: int = None,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Поиск похожих документов
        
        Args:
            query_embedding: Вектор запроса
            namespace: Namespace для поиска
            top_k: Количество результатов
            filter_dict: Дополнительные фильтры
        
        Returns:
            Список найденных документов с метаданными и scores
        """
        start_time = time.time()
        
        try:
            top_k = top_k or settings.top_k_results
            
            # Выполнить поиск
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.index.query(
                    vector=query_embedding,
                    top_k=top_k,
                    namespace=namespace,
                    filter=filter_dict,
                    include_metadata=True
                )
            )
            
            # Обработать результаты
            matches = []
            for match in results.matches:
                # Фильтровать по threshold
                if match.score >= settings.similarity_threshold:
                    matches.append({
                        'id': match.id,
                        'score': match.score,
                        'metadata': match.metadata
                    })
            
            duration = time.time() - start_time
            log_performance("vector_search", duration, success=True)
            
            vector_logger.info(
                f"Search completed: namespace={namespace}, "
                f"top_k={top_k}, found={len(matches)}, "
                f"threshold={settings.similarity_threshold}"
            )
            
            # Если ничего не найдено
            if not matches:
                vector_logger.warning(
                    f"No results found above threshold {settings.similarity_threshold} "
                    f"in namespace {namespace}"
                )
            
            return matches
            
        except Exception as e:
            duration = time.time() - start_time
            log_performance("vector_search", duration, success=False)
            
            error = handle_exception(e, {
                "operation": "vector_search",
                "namespace": namespace,
                "top_k": top_k
            })
            vector_logger.error(f"Search failed: {str(error)}")
            raise PineconeException(f"Vector search failed: {str(e)}")
    
    async def delete_namespace(self, namespace: str):
        """
        Удалить все векторы в namespace
        
        Args:
            namespace: Namespace для удаления
        """
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.index.delete(delete_all=True, namespace=namespace)
            )
            
            vector_logger.info(f"Deleted all vectors in namespace: {namespace}")
            
        except Exception as e:
            error_msg = f"Failed to delete namespace {namespace}: {str(e)}"
            vector_logger.error(error_msg)
            raise PineconeException(error_msg)
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику по индексу
        
        Returns:
            Статистика индекса
        """
        try:
            stats = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.index.describe_index_stats()
            )
            
            vector_logger.info(f"Index stats retrieved: {stats}")
            
            return {
                'total_vectors': stats.total_vector_count,
                'namespaces': stats.namespaces,
                'dimension': stats.dimension
            }
            
        except Exception as e:
            error_msg = f"Failed to get index stats: {str(e)}"
            vector_logger.error(error_msg)
            raise PineconeException(error_msg)
    
    def extract_context_from_matches(
        self,
        matches: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Извлечь текстовый контекст из результатов поиска
        
        Args:
            matches: Результаты поиска
        
        Returns:
            Список текстовых фрагментов
        """
        context = []
        
        for match in matches:
            metadata = match.get('metadata', {})
            text = metadata.get('text', '')
            
            if text:
                # Добавить метаинформацию
                source = metadata.get('source', 'Неизвестный источник')
                score = match.get('score', 0)
                
                context_item = f"{text}\n(Источник: {source}, релевантность: {score:.2f})"
                context.append(context_item)
        
        return context


# Глобальный экземпляр векторного хранилища
vector_store = VectorStore()
