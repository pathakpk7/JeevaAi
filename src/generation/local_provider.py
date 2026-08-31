import os
import requests
from typing import List, Dict, Any, Optional
from src.config import get_config
from src.logging_config import logger
from src.generation.provider import LLMProvider

class OllamaLocalProvider(LLMProvider):
    """
    Local LLM provider using Ollama REST API (100% free, runs offline on local machine).
    Default endpoint: http://localhost:11434/api/chat
    """

    def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None):
        config = get_config()
        self._model_name = model_name or (config.LLM_MODEL if config.LLM_MODEL != "gpt-4o-mini" else "llama3.2")
        self._base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._default_temp = config.LLM_TEMPERATURE
        self._default_max_tokens = config.LLM_MAX_OUTPUT_TOKENS

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        temp = temperature if temperature is not None else self._default_temp
        max_tok = max_tokens if max_tokens is not None else self._default_max_tokens

        url = f"{self._base_url.rstrip('/')}/api/chat"
        payload = {
            "model": self._model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": max_tok,
            }
        }

        try:
            res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
            res.raise_for_status()
            data = res.json()
            return data.get("message", {}).get("content", "").strip()

        except Exception as e:
            logger.error(f"Ollama local LLM call failed ({url}): {e}")
            raise RuntimeError(
                f"Local Ollama generation failure. Please ensure Ollama is installed and running at {self._base_url} "
                f"with model '{self._model_name}' pulled (`ollama run {self._model_name}`). Error details: {e}"
            ) from e

    @property
    def provider_name(self) -> str:
        return "local"

    @property
    def model_name(self) -> str:
        return self._model_name
