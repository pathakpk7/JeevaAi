from typing import List, Tuple
from langchain_core.documents import Document
from src.retrieval.models import RetrievalResult

def distance_to_similarity(distance: float) -> float:
    """
    Converts Chroma Cosine Distance into a normalized similarity score [0.0 to 1.0].
    Cosine distance range is [0.0 (identical) to 2.0 (opposite)].
    Formula: similarity = max(0.0, 1.0 - distance)
    """
    if distance is None:
        return 0.0
    similarity = 1.0 - float(distance)
    return round(max(0.0, min(1.0, similarity)), 4)

def format_and_rank_results(
    chroma_results: List[Tuple[Document, float]],
    min_score: float = 0.0
) -> List[RetrievalResult]:
    """
    Converts raw Chroma query results into ordered RetrievalResult models,
    sorts descending by similarity score, and filters out results below min_score.
    """
    formatted: List[RetrievalResult] = []

    for doc, sim_score in chroma_results:
        if sim_score < min_score:
            continue

        meta = doc.metadata
        res = RetrievalResult(
            chunk_id=str(meta.get("chunk_id", "")),
            text=doc.page_content,
            score=sim_score,
            source=str(meta.get("source", "")),
            document_name=str(meta.get("document_name", "")),
            page=int(meta.get("page", 0)),
            article_title=str(meta.get("article_title", "General Entry")),
            section=str(meta.get("section", "Overview")),
            length=len(doc.page_content),
        )
        formatted.append(res)

    # Ensure results are strictly ordered descending by score
    formatted.sort(key=lambda r: r.score, reverse=True)
    return formatted

def determine_match_quality(results: List[RetrievalResult]) -> str:
    """
    Evaluates qualitative match strength based on the highest similarity score.
    Returns: 'Strong', 'Limited', or 'None'.
    """
    if not results:
        return "None"

    top_score = results[0].score
    if top_score >= 0.55:
        return "Strong"
    elif top_score >= 0.35:
        return "Limited"
    else:
        return "None"
