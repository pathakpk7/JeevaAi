import os
import requests
from typing import List, Dict, Any, Optional
from src.config import get_config
from src.logging_config import logger
from src.generation.provider import LLMProvider

class GeminiProvider(LLMProvider):
    """
    Google Gemini LLM provider using direct REST API.
    Supports free tier Gemini models with automatic fallback for deprecated model names.
    """

    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        config = get_config()
        self._model_name = model_name or (config.LLM_MODEL if "gemini" in config.LLM_MODEL.lower() else "gemini-3.6-flash")
        self._api_key = api_key or os.getenv("GEMINI_API_KEY") or config.GEMINI_API_KEY
        self._default_temp = config.LLM_TEMPERATURE
        self._default_max_tokens = config.LLM_MAX_OUTPUT_TOKENS

        if not self._api_key:
            logger.warning("Gemini API key is missing. Provider will fail if generate() is called.")

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        if not self._api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in .env file or environment."
            )

        temp = temperature if temperature is not None else self._default_temp
        max_tok = max_tokens if max_tokens is not None else self._default_max_tokens

        # Format messages for Gemini API
        contents = []
        system_instruction = None

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            else:
                gemini_role = "model" if role == "assistant" else "user"
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temp,
                "maxOutputTokens": max_tok,
            }
        }

        if system_instruction:
            payload["systemInstruction"] = system_instruction

        # Fallback candidate models if requested model returns 404
        candidate_models = [self._model_name]
        for fallback in ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-flash-latest"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        last_exception = None
        for model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self._api_key}"
            try:
                res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=8)
                if res.status_code == 404:
                    logger.warning(f"Gemini model '{model}' returned 404 Not Found. Trying fallback model...")
                    continue

                res.raise_for_status()
                data = res.json()

                candidates = data.get("candidates", [])
                if not candidates:
                    raise RuntimeError("Gemini returned empty response candidates.")

                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    raise RuntimeError("Gemini returned candidate without text content.")

                self._model_name = model
                return parts[0].get("text", "").strip()

            except Exception as e:
                last_exception = e
                if isinstance(e, requests.HTTPError) and e.response is not None and e.response.status_code == 404:
                    continue
                logger.error(f"Gemini API call failed for model '{model}': {e}")
                raise RuntimeError(f"Gemini generation failure ({model}): {e}") from e

        raise RuntimeError(f"All Gemini models failed ({candidate_models}). Last error: {last_exception}")

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name
