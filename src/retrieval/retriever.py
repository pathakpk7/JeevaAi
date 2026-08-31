import time
from typing import Optional, List
from src.config import get_config
from src.logging_config import logger
from src.vectorstore.chroma_store import ChromaVectorStore
from src.embeddings.provider import EmbeddingProvider
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.models import RetrievalResult, RetrievalResponse
from src.retrieval.scoring import format_and_rank_results, determine_match_quality

class RetrievalSystemError(Exception):
    """Raised when vector store or embedding infrastructure fails during retrieval."""
    pass

class MedicalRetriever:
    """
    Primary retriever abstraction for search across the persistent medical knowledge index.
    Encapsulates Hybrid RRF search (Dense vector + BM25 Lexical + Article-aware boosting).
    """

    def __init__(
        self,
        vector_store: Optional[ChromaVectorStore] = None,
        bm25_retriever: Optional[BM25Retriever] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        self.config = get_config()
        self.vector_store = vector_store or ChromaVectorStore(embedding_provider=embedding_provider)
        self.hybrid_retriever = HybridRetriever(vector_store=self.vector_store, bm25_retriever=bm25_retriever)
        self.default_top_k = self.config.RETRIEVAL_TOP_K

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
        mode: str = "hybrid",
    ) -> RetrievalResponse:
        """
        Executes hybrid search (or 'dense'/'lexical') for a query string.
        """
        start_time = time.perf_counter()
        query_str = (query or "").strip()

        if not query_str:
            raise ValueError("Retrieval query string cannot be empty.")

        target_top_k = top_k if top_k is not None and top_k > 0 else self.default_top_k
        target_min_score = min_score if min_score is not None else getattr(self.config, "RETRIEVAL_MIN_SCORE", 0.0)

        logger.info(f"Executing retrieval query: '{query_str}' (Mode: {mode}, Top-K: {target_top_k}, Min Score: {target_min_score})")

        try:
            raw_results = self.hybrid_retriever.retrieve(query=query_str, top_k=target_top_k, mode=mode)
        except Exception as e:
            logger.error(f"Retrieval engine failed for query '{query_str}': {e}")
            raise RetrievalSystemError(f"Retrieval system failure: {e}") from e

        # Format, rank, and filter results
        ranked_results = format_and_rank_results(raw_results, min_score=target_min_score)
        match_quality = determine_match_quality(ranked_results)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.info(f"Retrieval finished in {duration_ms} ms: {len(ranked_results)} chunks returned (Match Quality: {match_quality})")

        return RetrievalResponse(
            query=query_str,
            top_k=target_top_k,
            min_score=target_min_score,
            result_count=len(ranked_results),
            retrieval_duration_ms=duration_ms,
            match_quality=match_quality,
            results=ranked_results,
        )
