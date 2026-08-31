from src.config import get_config
from src.embeddings.provider import EmbeddingProvider
from src.embeddings.huggingface import HuggingFaceEmbeddingProvider

def get_embedding_provider(provider_type: str = None, model_name: str = None) -> EmbeddingProvider:
    """
    Factory function to retrieve configured embedding provider instance.
    """
    config = get_config()
    provider = (provider_type or config.EMBEDDING_PROVIDER).lower()

    if provider in ["huggingface", "sentence-transformers", "local"]:
        return HuggingFaceEmbeddingProvider(model_name=model_name or config.EMBEDDING_MODEL)
    else:
        raise ValueError(f"Unsupported embedding provider: '{provider}'. Defaulting to 'huggingface'.")
