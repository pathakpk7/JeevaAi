from typing import List
from src.config import get_config
from src.retrieval.models import RetrievalResult

class ContextBuilder:
    """
    Constructs structured context blocks from retrieved medical chunks.
    Maintains relevance rank order and enforces chunk context budgets.
    """

    def __init__(self, max_chunks: int = None):
        config = get_config()
        self.max_chunks = max_chunks or config.GENERATION_MAX_CONTEXT_CHUNKS

    def build_context_block(self, retrieval_results: List[RetrievalResult]) -> str:
        """
        Formats list of RetrievalResult objects into delimited markdown context string.
        """
        if not retrieval_results:
            return "[RETRIEVED MEDICAL CONTEXT]\nNo relevant medical knowledge chunks found.\n[END RETRIEVED MEDICAL CONTEXT]"

        selected_chunks = retrieval_results[: self.max_chunks]
        context_parts = ["[RETRIEVED MEDICAL CONTEXT]"]

        for idx, res in enumerate(selected_chunks, 1):
            chunk_header = (
                f"--- [Source Chunk {idx}] ---\n"
                f"Document: {res.document_name}\n"
                f"Page: {res.page}\n"
                f"Article Title: {res.article_title}\n"
                f"Section Heading: {res.section}\n"
                f"Chunk ID: {res.chunk_id}\n"
                f"Similarity Score: {res.score:.4f}\n"
                f"Text:\n{res.text}\n"
            )
            context_parts.append(chunk_header)

        context_parts.append("[END RETRIEVED MEDICAL CONTEXT]")
        return "\n".join(context_parts)
