from typing import List, Set, Tuple
from src.retrieval.models import RetrievalResult
from src.generation.models import Citation

class CitationBuilder:
    """
    Programmatic citation builder.
    Constructs deduplicated, verifiable source citations strictly from vector retrieval metadata.
    Never relies on or parses LLM text outputs for citation authority.
    """

    @staticmethod
    def build_citations(retrieval_results: List[RetrievalResult]) -> List[Citation]:
        """
        Extracts deduplicated Citation objects from retrieval results while maintaining relevance rank order.
        """
        citations: List[Citation] = []
        seen_keys: Set[Tuple[str, int, str, str]] = set()

        for res in retrieval_results:
            dedup_key = (
                res.document_name,
                res.page,
                res.article_title.lower(),
                res.section.lower()
            )

            if dedup_key not in seen_keys:
                seen_keys.add(dedup_key)
                citations.append(
                    Citation(
                        document_name=res.document_name,
                        page=res.page,
                        article_title=res.article_title,
                        section=res.section,
                        chunk_id=res.chunk_id,
                        snippet=res.text,
                    )
                )

        return citations
