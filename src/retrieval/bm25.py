import json
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document
from src.config import get_config
from src.logging_config import logger
from src.vectorstore.chroma_store import ChromaVectorStore
from src.ingestion.pipeline import run_ingestion

def tokenize_text(text: str) -> List[str]:
    """
    Simple, fast alphanumeric tokenizer for BM25.
    Lowercases text and extracts word tokens (length >= 2).
    """
    if not text:
        return []
    return re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())

class BM25Retriever:
    """
    Lexical BM25 search engine built over indexed medical encyclopedia chunks.
    Complements dense vector embeddings by providing exact keyword match scoring.
    """

    def __init__(
        self,
        vector_store: Optional[ChromaVectorStore] = None,
        chunks: Optional[List[Dict[str, Any]]] = None
    ):
        self.config = get_config()
        self.vector_store = vector_store
        self.documents: List[Document] = []
        self.corpus_tokens: List[List[str]] = []

        if chunks:
            self._build_from_chunk_dicts(chunks)
        else:
            self._build_from_vectorstore_or_file()

    def _build_from_chunk_dicts(self, chunks: List[Dict[str, Any]]):
        for item in chunks:
            text = item.get("content") or item.get("text") or ""
            meta = item.get("metadata") or {
                "chunk_id": item.get("chunk_id", ""),
                "article_title": item.get("article_title", "General Entry"),
                "section": item.get("section", "Overview"),
                "page": item.get("page", 0),
                "document_name": item.get("document_name", "The_GALE_ENCYCLOPEDIA_of_MEDICINE_SECOND.pdf"),
                "source": item.get("source", str(self.config.get_absolute_pdf_path())),
            }

            doc = Document(page_content=text, metadata=meta)
            self.documents.append(doc)

            article_title = meta.get("article_title", "")
            section = meta.get("section", "")
            tokens = (
                tokenize_text(article_title) * 3 +
                tokenize_text(section) * 2 +
                tokenize_text(text)
            )
            self.corpus_tokens.append(tokens)

        self.bm25 = BM25Okapi(self.corpus_tokens)

    def _build_from_vectorstore_or_file(self):
        # First attempt: load all indexed documents directly from ChromaDB
        store = self.vector_store or ChromaVectorStore()
        try:
            chroma_data = store.collection.get(include=["documents", "metadatas"])
            docs_list = chroma_data.get("documents", [])
            metas_list = chroma_data.get("metadatas", [])

            if docs_list and len(docs_list) > 0:
                logger.info(f"Building BM25 index over {len(docs_list)} indexed chunks from ChromaDB...")
                for text, meta in zip(docs_list, metas_list):
                    doc = Document(page_content=text, metadata=meta)
                    self.documents.append(doc)

                    article_title = meta.get("article_title", "")
                    section = meta.get("section", "")
                    tokens = (
                        tokenize_text(article_title) * 3 +
                        tokenize_text(section) * 2 +
                        tokenize_text(text)
                    )
                    self.corpus_tokens.append(tokens)

                self.bm25 = BM25Okapi(self.corpus_tokens)
                logger.info("BM25 Okapi index successfully initialized from ChromaDB collection.")
                return
        except Exception as e:
            logger.warning(f"Could not load documents from ChromaDB ({e}). Falling back to file/ingestion...")

        # Second attempt: load from processed chunks JSON file
        project_root = Path(__file__).resolve().parent.parent.parent
        processed_file = project_root / "data" / "processed" / "chunks.json"

        if processed_file.exists():
            try:
                with open(processed_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    chunks = data.get("chunks", data) if isinstance(data, dict) else data
                    if isinstance(chunks, list):
                        self._build_from_chunk_dicts(chunks)
                        logger.info(f"BM25 index built from {len(chunks)} chunks in {processed_file}.")
                        return
            except Exception as e:
                logger.warning(f"Failed to read processed chunks file: {e}")

        # Final fallback: run ingestion pipeline
        logger.info("Executing ingestion pipeline to build BM25 corpus...")
        docs, _ = run_ingestion(save_processed=False)
        self._build_from_chunk_dicts([{"text": d.page_content, "metadata": d.metadata} for d in docs])

    def retrieve(self, query_text: str, top_k: int = 20) -> List[Tuple[Document, float]]:
        """
        Executes lexical BM25 search for a query string.
        Returns List of (Document, float_bm25_score) tuples sorted descending by score.
        """
        q_str = (query_text or "").strip()
        if not q_str or not self.documents:
            return []

        query_tokens = tokenize_text(q_str)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        # Get top-N candidate indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score > 0.0:
                results.append((self.documents[idx], score))

        return results
