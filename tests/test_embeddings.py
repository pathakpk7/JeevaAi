import pytest
from src.embeddings.factory import get_embedding_provider
from src.embeddings.huggingface import HuggingFaceEmbeddingProvider

def test_embedding_provider_factory():
    provider = get_embedding_provider("huggingface")
    assert isinstance(provider, HuggingFaceEmbeddingProvider)

def test_embedding_provider_properties():
    provider = get_embedding_provider()
    assert provider.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert provider.dimension == 384

def test_embed_query():
    provider = get_embedding_provider()
    vec = provider.embed_query("What are the symptoms of caffeine overdose?")
    assert isinstance(vec, list)
    assert len(vec) == 384
    assert all(isinstance(val, float) for val in vec)

def test_embed_documents():
    provider = get_embedding_provider()
    texts = [
        "Caffeine is a central nervous system stimulant.",
        "Symptoms of caffeine overdose include restlessness and tachycardia."
    ]
    vectors = provider.embed_documents(texts)
    assert isinstance(vectors, list)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384

def test_empty_input_handling():
    provider = get_embedding_provider()
    assert provider.embed_documents([]) == []
    empty_vec = provider.embed_query("")
    assert len(empty_vec) == 384
