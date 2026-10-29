from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from src.logging_config import logger
from src.vectorstore.chroma_store import ChromaVectorStore
from src.embeddings.provider import EmbeddingProvider

class VectorStoreManager:
    """
    High-level manager for persistent vector store lifecycle operations:
    INDEX, LOAD, REBUILD, RESET.
    """

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        self.store = ChromaVectorStore(
            persist_dir=persist_dir,
            collection_name=collection_name,
            embedding_provider=embedding_provider,
        )

    def load_store(self) -> Dict[str, Any]:
        """Loads and returns vector store status and statistics."""
        stats = self.store.get_stats()
        stats["operation"] = "LOAD"
        stats["status"] = "SUCCESS"
        logger.info(f"Loaded VectorStore '{stats['collection_name']}' with {stats['vector_count']} vectors.")
        return stats

    def index_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Idempotently indexes document chunks using deterministic chunk_ids.
        """
        initial_count = self.store.count()
        added_count = self.store.add_documents(documents)
        final_count = self.store.count()

        stats = self.store.get_stats()
        stats["operation"] = "INDEX"
        stats["chunks_processed"] = len(documents)
        stats["vectors_added"] = added_count
        stats["new_records_created"] = final_count - initial_count
        stats["status"] = "SUCCESS"

        logger.info(f"INDEX operation complete: Processed {len(documents)} chunks -> Total Collection Count: {final_count}")
        return stats

    def rebuild_store(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Resets vector collection and re-indexes all provided document chunks from scratch.
        """
        logger.warning("Executing REBUILD operation: Resetting existing vector collection...")
        self.store.reset()
        added_count = self.store.add_documents(documents)

        stats = self.store.get_stats()
        stats["operation"] = "REBUILD"
        stats["chunks_processed"] = len(documents)
        stats["vectors_added"] = added_count
        stats["status"] = "SUCCESS"

        logger.info(f"REBUILD operation complete: Indexed {added_count} fresh vectors.")
        return stats

    def reset_store(self) -> Dict[str, Any]:
        """
        Clears all records and resets the vector store collection.
        """
        self.store.reset()
        stats = self.store.get_stats()
        stats["operation"] = "RESET"
        stats["status"] = "SUCCESS"
        logger.info("RESET operation complete: Collection cleared.")
        return stats
