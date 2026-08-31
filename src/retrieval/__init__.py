"""
Retrieval package for searching vector indexes and metadata retrieval.
"""
from src.retrieval.models import RetrievalResult, RetrievalResponse
from src.retrieval.scoring import distance_to_similarity, format_and_rank_results, determine_match_quality
from src.retrieval.retriever import MedicalRetriever, RetrievalSystemError

__all__ = [
    "RetrievalResult",
    "RetrievalResponse",
    "MedicalRetriever",
    "RetrievalSystemError",
    "distance_to_similarity",
    "format_and_rank_results",
    "determine_match_quality",
]
