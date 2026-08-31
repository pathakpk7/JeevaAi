from typing import List, Tuple, Optional, Dict
from langchain_core.documents import Document
from src.config import get_config
from src.logging_config import logger
from src.vectorstore.chroma_store import ChromaVectorStore
from src.retrieval.bm25 import BM25Retriever

class HybridRetriever:
    """
    Hybrid Retriever combining Dense Vector Similarity Search and Lexical BM25 Search
    using Reciprocal Rank Fusion (RRF) with Article-Aware Context Boosting.
    """

    def __init__(
        self,
        vector_store: Optional[ChromaVectorStore] = None,
        bm25_retriever: Optional[BM25Retriever] = None,
        candidate_pool_size: int = 20,
    ):
        self.config = get_config()
        self.vector_store = vector_store or ChromaVectorStore()
        self.bm25_retriever = bm25_retriever or BM25Retriever(vector_store=self.vector_store)
        self.candidate_pool_size = candidate_pool_size

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        mode: str = "hybrid"
    ) -> List[Tuple[Document, float]]:
        """
        Executes search using mode: 'hybrid' (default), 'dense', or 'lexical'.
        Returns List of (Document, normalized_similarity_score) sorted descending.
        """
        target_top_k = top_k or self.config.RETRIEVAL_TOP_K
        query_str = (query or "").strip()

        if not query_str:
            return []

        search_mode = (mode or "hybrid").lower()

        if search_mode == "dense":
            return self._retrieve_dense(query_str, target_top_k)
        elif search_mode == "lexical":
            return self._retrieve_lexical(query_str, target_top_k)
        else:
            return self._retrieve_hybrid(query_str, target_top_k)

    def _retrieve_dense(self, query: str, top_k: int) -> List[Tuple[Document, float]]:
        return self.vector_store.query(query_text=query, top_k=top_k)

    def _retrieve_lexical(self, query: str, top_k: int) -> List[Tuple[Document, float]]:
        bm25_results = self.bm25_retriever.retrieve(query_text=query, top_k=top_k)
        if not bm25_results:
            return []
        max_score = max(score for _, score in bm25_results) if bm25_results else 1.0
        normalized = []
        for doc, score in bm25_results:
            norm_score = round(min(1.0, score / max_score), 4) if max_score > 0 else 0.0
            normalized.append((doc, norm_score))
        return normalized

    def _retrieve_hybrid(self, query: str, top_k: int) -> List[Tuple[Document, float]]:
        # Fetch candidate pools
        dense_candidates = self.vector_store.query(query_text=query, top_k=self.candidate_pool_size)
        lexical_candidates = self.bm25_retriever.retrieve(query_text=query, top_k=self.candidate_pool_size)

        # Check if top dense similarity score is out-of-domain (< 0.35)
        top_dense_score = dense_candidates[0][1] if dense_candidates else 0.0
        is_out_of_domain = top_dense_score < 0.35

        # Map candidates by chunk_id
        doc_map: Dict[str, Document] = {}
        dense_ranks: Dict[str, int] = {}
        lexical_ranks: Dict[str, int] = {}
        dense_scores: Dict[str, float] = {}

        for rank, (doc, sim_score) in enumerate(dense_candidates, 1):
            chunk_id = doc.metadata.get("chunk_id", f"dense_{rank}")
            doc_map[chunk_id] = doc
            dense_ranks[chunk_id] = rank
            dense_scores[chunk_id] = sim_score

        for rank, (doc, bm25_score) in enumerate(lexical_candidates, 1):
            chunk_id = doc.metadata.get("chunk_id", f"lexical_{rank}")
            if chunk_id not in doc_map:
                doc_map[chunk_id] = doc
            lexical_ranks[chunk_id] = rank

        # Reciprocal Rank Fusion (RRF) with Article-Aware Boost
        rrf_scores: Dict[str, float] = {}
        k_const = 60.0

        query_words = set(w.lower() for w in query.split() if len(w) >= 3)

        for chunk_id, doc in doc_map.items():
            r_dense = dense_ranks.get(chunk_id, 100)
            r_lexical = lexical_ranks.get(chunk_id, 100)

            score_rrf = (1.0 / (k_const + r_dense)) + (1.0 / (k_const + r_lexical))

            # Article-Aware Boost: Check if article title matches query terms
            article_title = doc.metadata.get("article_title", "").lower()
            if article_title and any(kw in article_title for kw in query_words):
                score_rrf *= 1.35  # 35% boost for chunks matching target article title

            rrf_scores[chunk_id] = score_rrf

        # Sort chunk IDs descending by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:top_k]

        if not sorted_ids:
            return []

        max_rrf = max(rrf_scores.values()) if rrf_scores else 1.0

        final_results = []
        for cid in sorted_ids:
            doc = doc_map[cid]
            rrf_val = rrf_scores[cid]
            dense_sim = dense_scores.get(cid, 0.0)

            if is_out_of_domain:
                # Retain original low dense similarity for out-of-domain queries to trigger controlled refusal
                final_sim = dense_sim
            else:
                final_sim = round(max(dense_sim, min(1.0, rrf_val / max_rrf)), 4)

            final_results.append((doc, final_sim))

        return final_results
