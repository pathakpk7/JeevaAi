import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import chromadb
from langchain_core.documents import Document
from src.config import get_config
from src.logging_config import logger
from src.embeddings.provider import EmbeddingProvider
from src.embeddings.factory import get_embedding_provider

class ChromaVectorStore:
    """
    Persistent ChromaDB vector store wrapper.
    Survives application restarts, uses deterministic chunk IDs for idempotent upserts,
    and preserves original chunk content and metadata for citation retrieval.
    """

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        config = get_config()
        self.persist_dir = Path(persist_dir) if persist_dir else config.get_absolute_vectorstore_path()
        self.collection_name = collection_name or config.VECTORSTORE_COLLECTION
        self.embedding_provider = embedding_provider or get_embedding_provider()

        # Ensure persistence directory exists
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing Persistent ChromaDB Client at: {self.persist_dir} (Collection: '{self.collection_name}')")

        try:
            self.client = chromadb.PersistentClient(path=str(self.persist_dir))
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB at '{self.persist_dir}': {e}")
            raise RuntimeError(f"ChromaDB initialization failed: {e}") from e

    def count(self) -> int:
        """Returns total vector count in the collection."""
        return self.collection.count()

    def add_documents(self, documents: List[Document], batch_size: int = 100) -> int:
        """
        Idempotently inserts or updates document chunks using deterministic chunk_ids as Chroma record IDs.
        """
        if not documents:
            logger.warning("No documents provided for vector indexing.")
            return 0

        total_added = 0
        total_docs = len(documents)

        logger.info(f"Indexing {total_docs} document chunks in batches of {batch_size}...")

        for i in range(0, total_docs, batch_size):
            batch_docs = documents[i : i + batch_size]

            batch_texts = [d.page_content for d in batch_docs]
            batch_embeddings = self.embedding_provider.embed_documents(batch_texts)

            batch_ids = []
            batch_metadatas = []

            for idx, doc in enumerate(batch_docs):
                meta = dict(doc.metadata)
                chunk_id = meta.get("chunk_id")
                if not chunk_id:
                    # Fallback to content hash if chunk_id is missing
                    import hashlib
                    chunk_id = hashlib.md5(doc.page_content.encode("utf-8")).hexdigest()
                    meta["chunk_id"] = chunk_id

                # Ensure metadata values are primitive types for ChromaDB compatibility
                clean_meta = {}
                for k, v in meta.items():
                    if isinstance(v, (str, int, float, bool)):
                        clean_meta[k] = v
                    else:
                        clean_meta[k] = str(v)

                batch_ids.append(str(chunk_id))
                batch_metadatas.append(clean_meta)

            self.collection.upsert(
                ids=batch_ids,
                embeddings=batch_embeddings,
                documents=batch_texts,
                metadatas=batch_metadatas,
            )

            total_added += len(batch_docs)
            logger.info(f"Indexed batch {i // batch_size + 1}: {total_added}/{total_docs} chunks stored.")

        logger.info(f"Successfully completed vector indexing. Collection vector count: {self.count()}")
        return total_added

    def query(self, query_text: str, top_k: int = 4) -> List[Tuple[Document, float]]:
        """
        Performs semantic vector search for a query string.
        Returns list of (Document, similarity_score) tuples.
        """
        if self.count() == 0:
            logger.warning("Query attempted on empty vector store collection.")
            return []

        query_embedding = self.embedding_provider.embed_query(query_text)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.count()),
            include=["documents", "metadatas", "distances"]
        )

        matched_docs: List[Tuple[Document, float]] = []
        if results and results["documents"]:
            docs_list = results["documents"][0]
            meta_list = results["metadatas"][0]
            dist_list = results["distances"][0]

            for doc_text, meta, dist in zip(docs_list, meta_list, dist_list):
                # Convert cosine distance to similarity score (1 - distance)
                similarity = round(max(0.0, 1.0 - float(dist)), 4)
                matched_docs.append((Document(page_content=doc_text, metadata=meta), similarity))

        return matched_docs

    def get_stats(self) -> Dict[str, Any]:
        """Returns collection diagnostics and stats."""
        sample_meta = None
        sample_doc = None

        if self.count() > 0:
            sample_data = self.collection.get(limit=1, include=["documents", "metadatas"])
            if sample_data and sample_data["documents"]:
                sample_doc = sample_data["documents"][0][:200] + "..."
                sample_meta = sample_data["metadatas"][0]

        return {
            "collection_name": self.collection_name,
            "vector_count": self.count(),
            "persist_directory": str(self.persist_dir),
            "embedding_model": self.embedding_provider.model_name,
            "embedding_dimension": self.embedding_provider.dimension,
            "sample_metadata": sample_meta,
            "sample_document_preview": sample_doc,
        }

    def reset(self) -> None:
        """Deletes the vector collection and resets storage."""
        logger.warning(f"Resetting vector store collection '{self.collection_name}'...")
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Vector store collection '{self.collection_name}' reset successfully.")
