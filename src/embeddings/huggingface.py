from typing import List
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from src.config import get_config
from src.logging_config import logger
from src.embeddings.provider import EmbeddingProvider

class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """
    Local Sentence Transformers embedding provider powered by Hugging Face models.
    Runs 100% locally on CPU or GPU without requiring external API keys.
    """

    def __init__(self, model_name: str = None):
        config = get_config()
        self._model_name = model_name or config.EMBEDDING_MODEL
        logger.info(f"Initializing local HuggingFace embedding provider: {self._model_name}")

        try:
            try:
                import torch
                torch.set_num_threads(1)
                torch.set_grad_enabled(False)
            except Exception:
                pass

            # Fast local loading without hanging on HF Hub network checks
            try:
                self._embeddings_client = HuggingFaceEmbeddings(
                    model_name=self._model_name,
                    model_kwargs={"device": "cpu", "local_files_only": True},
                    encode_kwargs={"normalize_embeddings": True}
                )
            except Exception as cache_err:
                logger.warning(f"Could not load '{self._model_name}' from local cache only ({cache_err}). Falling back to online download.")
                self._embeddings_client = HuggingFaceEmbeddings(
                    model_name=self._model_name,
                    model_kwargs={"device": "cpu"},
                    encode_kwargs={"normalize_embeddings": True}
                )

            # Avoid extra inference pass on cold start for standard MiniLM models
            if "minilm" in self._model_name.lower() or "384" in self._model_name:
                self._dimension = 384
            else:
                sample_vector = self._embeddings_client.embed_query("test dimension query")
                self._dimension = len(sample_vector)
            logger.info(f"Successfully loaded embedding model '{self._model_name}' (Vector dimension: {self._dimension})")
        except Exception as e:
            logger.error(f"Failed to load HuggingFace embedding model '{self._model_name}': {e}")
            raise RuntimeError(f"Embedding model initialization failed: {e}") from e

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return self._embeddings_client.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self._dimension
        return self._embeddings_client.embed_query(text)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def get_langchain_embeddings(self) -> Embeddings:
        return self._embeddings_client
