"""
Скрипт загрузки документов в Pinecone
"""
import sys
import asyncio
import hashlib
from pathlib import Path
from typing import List, Dict, Any
import re

# Добавить корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from src.core.vector_store import vector_store
from src.core.llm_client import llm_client
from src.utils.logger import main_logger
from src.utils.config import settings


class DocumentLoader:
    """Загрузчик документов в векторную базу"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.chunk_size = 1000  # Размер чанка в символах
        self.chunk_overlap = 200  # Перекрытие между чанками
    
    def _split_text_into_chunks(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Разбить текст на чанки
        
        Args:
            text: Текст для разбиения
            metadata: Метаданные документа
        
        Returns:
            Список чанков с метаданными
        """
        chunks = []
        
        # Очистить текст
        text = text.strip()
        
        # Разбить на параграфы
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            # Если параграф сам по себе больше chunk_size
            if len(paragraph) > self.chunk_size:
                # Сохранить текущий чанк если есть
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'metadata': {
                            **metadata,
                            'chunk_index': chunk_index,
                            'char_count': len(current_chunk)
                        }
                    })
                    chunk_index += 1
                    current_chunk = ""
                
                # Разбить большой параграф на предложения
                sentences = re.split(r'[.!?]+', paragraph)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    if len(current_chunk) + len(sentence) < self.chunk_size:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk:
                            chunks.append({
                                'text': current_chunk.strip(),
                                'metadata': {
                                    **metadata,
                                    'chunk_index': chunk_index,
                                    'char_count': len(current_chunk)
                                }
                            })
                            chunk_index += 1
                        current_chunk = sentence + ". "
            else:
                # Добавить параграф к текущему чанку
                if len(current_chunk) + len(paragraph) < self.chunk_size:
                    current_chunk += paragraph + "\n\n"
                else:
                    # Сохранить текущий чанк
                    if current_chunk:
                        chunks.append({
                            'text': current_chunk.strip(),
                            'metadata': {
                                **metadata,
                                'chunk_index': chunk_index,
                                'char_count': len(current_chunk)
                            }
                        })
                        chunk_index += 1
                    
                    # Начать новый чанк с перекрытием
                    overlap_text = current_chunk[-self.chunk_overlap:] if current_chunk else ""
                    current_chunk = overlap_text + paragraph + "\n\n"
        
        # Сохранить последний чанк
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'metadata': {
                    **metadata,
                    'chunk_index': chunk_index,
                    'char_count': len(current_chunk)
                }
            })
        
        return chunks
    
    def _generate_doc_id(self, text: str, metadata: Dict[str, Any]) -> str:
        """Генерировать уникальный ID для документа"""
        content = f"{metadata.get('source', '')}_{metadata.get('chunk_index', 0)}_{text[:100]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def load_text_file(
        self,
        file_path: Path,
        namespace: str,
        metadata: Dict[str, Any] = None
    ) -> int:
        """
        Загрузить текстовый файл
        
        Args:
            file_path: Путь к файлу
            namespace: Namespace в Pinecone
            metadata: Дополнительные метаданные
        
        Returns:
            Количество загруженных чанков
        """
        main_logger.info(f"Loading file: {file_path}")
        
        # Читать файл
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Подготовить метаданные
        file_metadata = metadata or {}
        file_metadata['source'] = file_path.name
        file_metadata['file_path'] = str(file_path)
        
        # Разбить на чанки
        chunks = self._split_text_into_chunks(text, file_metadata)
        main_logger.info(f"Split into {len(chunks)} chunks")
        
        # Генерировать эмбеддинги и подготовить документы
        documents = []
        
        for chunk in chunks:
            try:
                # Генерировать эмбеддинг
                embedding = await llm_client.generate_embedding(chunk['text'])
                
                # Подготовить документ
                doc_id = self._generate_doc_id(chunk['text'], chunk['metadata'])
                
                documents.append({
                    'id': doc_id,
                    'embedding': embedding,
                    'metadata': {
                        **chunk['metadata'],
                        'text': chunk['text']
                    }
                })
                
            except Exception as e:
                main_logger.error(f"Failed to process chunk: {str(e)}")
                continue
        
        # Загрузить в Pinecone
        if documents:
            await vector_store.upsert_documents(documents, namespace=namespace)
            main_logger.info(f"✓ Loaded {len(documents)} chunks from {file_path.name}")
        
        return len(documents)
    
    async def load_directory(
        self,
        directory: Path,
        namespace: str,
        file_pattern: str = "*.txt"
    ) -> Dict[str, int]:
        """
        Загрузить все файлы из директории
        
        Args:
            directory: Директория с файлами
            namespace: Namespace в Pinecone
            file_pattern: Паттерн для поиска файлов
        
        Returns:
            Статистика загрузки
        """
        if not directory.exists():
            main_logger.warning(f"Directory does not exist: {directory}")
            return {'total_files': 0, 'total_chunks': 0}
        
        files = list(directory.glob(file_pattern))
        
        if not files:
            main_logger.warning(f"No files found matching {file_pattern} in {directory}")
            return {'total_files': 0, 'total_chunks': 0}
        
        main_logger.info(f"Found {len(files)} files in {directory}")
        
        total_chunks = 0
        
        for file_path in files:
            try:
                chunks_loaded = await self.load_text_file(
                    file_path=file_path,
                    namespace=namespace
                )
                total_chunks += chunks_loaded
                
            except Exception as e:
                main_logger.error(f"Failed to load {file_path}: {str(e)}")
        
        return {
            'total_files': len(files),
            'total_chunks': total_chunks
        }


async def load_all_documents():
    """Загрузить все документы из data директории"""
    main_logger.info("=" * 60)
    main_logger.info("DOCUMENT LOADING")
    main_logger.info("=" * 60)
    
    loader = DocumentLoader()
    
    # Агенты и их директории
    agents = {
        'finance': 'finance',
        'legal': 'legal',
        'project': 'project'
    }
    
    total_stats = {
        'total_files': 0,
        'total_chunks': 0
    }
    
    for agent_name, directory_name in agents.items():
        main_logger.info(f"\n>>> Loading documents for {agent_name.upper()} agent")
        
        directory = loader.data_dir / directory_name
        
        # Загрузить .txt файлы
        stats = await loader.load_directory(
            directory=directory,
            namespace=agent_name,
            file_pattern="*.txt"
        )
        
        # Загрузить .md файлы
        md_stats = await loader.load_directory(
            directory=directory,
            namespace=agent_name,
            file_pattern="*.md"
        )
        
        agent_total_files = stats['total_files'] + md_stats['total_files']
        agent_total_chunks = stats['total_chunks'] + md_stats['total_chunks']
        
        main_logger.info(
            f"✓ {agent_name.upper()}: "
            f"{agent_total_files} files, "
            f"{agent_total_chunks} chunks"
        )
        
        total_stats['total_files'] += agent_total_files
        total_stats['total_chunks'] += agent_total_chunks
    
    main_logger.info("\n" + "=" * 60)
    main_logger.info("LOADING COMPLETE")
    main_logger.info(f"Total Files: {total_stats['total_files']}")
    main_logger.info(f"Total Chunks: {total_stats['total_chunks']}")
    main_logger.info("=" * 60)
    
    return total_stats


async def main():
    """Главная функция"""
    try:
        stats = await load_all_documents()
        
        if stats['total_chunks'] > 0:
            print("\n✓ Documents loaded successfully!")
            print(f"  Files processed: {stats['total_files']}")
            print(f"  Chunks created: {stats['total_chunks']}")
            print("\nNext step: python src/main.py")
        else:
            print("\n⚠️  No documents were loaded.")
            print("Please add documents to data/ directory:")
            print("  - data/finance/")
            print("  - data/legal/")
            print("  - data/project/")
        
    except Exception as e:
        main_logger.error(f"Failed to load documents: {str(e)}", exc_info=True)
        print(f"\n✗ Loading failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
