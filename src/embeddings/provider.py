from abc import ABC, abstractmethod
from typing import List, Any
from langchain_core.embeddings import Embeddings

class EmbeddingProvider(ABC):
    """
    Abstract interface for vector embedding providers.
    Decouples vector representation generation from specific underlying AI/ML libraries or API services.
    """

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for a list of document strings.
        """
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Generate an embedding vector for a single search query string.
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Returns the name/identifier of the embedding model.
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        Returns the dimensionality of the generated embedding vectors.
        """
        pass

    @abstractmethod
    def get_langchain_embeddings(self) -> Embeddings:
        """
        Returns a LangChain-compatible Embeddings object instance.
        """
        pass
