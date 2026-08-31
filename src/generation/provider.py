from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class LLMProvider(ABC):
    """
    Abstract interface for Large Language Model generation providers.
    Decouples application logic from specific LLM vendors (OpenAI, Gemini, Local/Mock).
    """

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generates a completion string given a list of chat message dictionaries.
        Format: [{'role': 'system'|'user'|'assistant', 'content': str}]
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the provider name (e.g. 'openai', 'mock')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the model identifier (e.g. 'gpt-4o-mini', 'mock-v1')."""
        pass
