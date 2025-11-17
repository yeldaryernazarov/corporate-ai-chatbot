"""
Скрипт инициализации Pinecone индекса
"""
import sys
import asyncio
from pathlib import Path

# Добавить корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from src.core.vector_store import vector_store
from src.utils.logger import main_logger
from src.utils.config import settings


async def init_pinecone():
    """Инициализировать Pinecone индекс"""
    main_logger.info("=" * 60)
    main_logger.info("PINECONE INITIALIZATION")
    main_logger.info("=" * 60)
    
    try:
        # Получить статистику индекса
        stats = await vector_store.get_stats()
        
        main_logger.info(f"Index Name: {settings.pinecone_index_name}")
        main_logger.info(f"Environment: {settings.pinecone_environment}")
        main_logger.info(f"Dimension: {stats.get('dimension', settings.pinecone_dimension)}")
        main_logger.info(f"Total Vectors: {stats.get('total_vectors', 0)}")
        
        # Проверить namespaces
        namespaces = stats.get('namespaces', {})
        
        if namespaces:
            main_logger.info("\nNamespaces:")
            for ns_name, ns_info in namespaces.items():
                vector_count = ns_info.get('vector_count', 0)
                main_logger.info(f"  - {ns_name}: {vector_count} vectors")
        else:
            main_logger.info("\nNo namespaces found. Index is empty.")
            main_logger.info("Use load_documents.py to populate the index with data.")
        
        main_logger.info("\n✓ Pinecone initialization successful")
        main_logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        main_logger.error(f"\n✗ Pinecone initialization failed: {str(e)}")
        main_logger.error("=" * 60)
        return False


def main():
    """Главная функция"""
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(init_pinecone())
    
    if success:
        print("\n✓ Pinecone is ready to use!")
        print("Next steps:")
        print("  1. Prepare your documents in data/ directory")
        print("  2. Run: python scripts/load_documents.py")
        print("  3. Start the bot: python src/main.py")
    else:
        print("\n✗ Initialization failed. Please check the logs and configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
