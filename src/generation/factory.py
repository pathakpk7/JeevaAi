import os
from typing import Optional
from src.config import get_config
from src.logging_config import logger
from src.generation.provider import LLMProvider
from src.generation.mock_provider import MockLLMProvider
from src.generation.openai_provider import OpenAIProvider
from src.generation.gemini_provider import GeminiProvider
from src.generation.local_provider import OllamaLocalProvider

def get_llm_provider(provider_type: Optional[str] = None, model_name: Optional[str] = None) -> LLMProvider:
    """
    Factory function retrieving configured LLMProvider instance.
    Supports free alternatives: Google Gemini, Ollama (local), and built-in Mock provider.
    Falls back gracefully to MockLLMProvider if API keys are missing.
    """
    config = get_config()
    provider = (provider_type or config.LLM_PROVIDER).lower()

    if provider in ["mock", "test", "fake"]:
        return MockLLMProvider()

    elif provider in ["gemini", "google"]:
        api_key = config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY is not configured. Falling back to MockLLMProvider for generation.")
            return MockLLMProvider()
        return GeminiProvider(model_name=model_name or (config.LLM_MODEL if "gemini" in config.LLM_MODEL.lower() else "gemini-1.5-flash"))

    elif provider in ["local", "ollama"]:
        return OllamaLocalProvider(model_name=model_name or (config.LLM_MODEL if config.LLM_MODEL != "gpt-4o-mini" else "llama3.2"))

    elif provider in ["openai", "chatgpt"]:
        api_key = config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY is not configured. Falling back to MockLLMProvider for offline generation.")
            return MockLLMProvider()
        return OpenAIProvider(model_name=model_name or config.LLM_MODEL)

    else:
        logger.warning(f"Unrecognized or unconfigured LLM provider '{provider}'. Falling back to MockLLMProvider.")
        return MockLLMProvider()
