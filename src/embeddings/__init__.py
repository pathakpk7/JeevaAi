"""
Embeddings package for generating local sentence embeddings.
"""
from src.embeddings.provider import EmbeddingProvider
from src.embeddings.huggingface import HuggingFaceEmbeddingProvider
from src.embeddings.factory import get_embedding_provider

__all__ = [
    "EmbeddingProvider",
    "HuggingFaceEmbeddingProvider",
    "get_embedding_provider",
]
