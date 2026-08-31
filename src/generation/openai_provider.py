import os
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.config import get_config
from src.logging_config import logger
from src.generation.provider import LLMProvider

class OpenAIProvider(LLMProvider):
    """
    OpenAI LLM provider client using ChatOpenAI.
    Fails gracefully with clear configuration error if OPENAI_API_KEY is missing.
    """

    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        config = get_config()
        self._model_name = model_name or config.LLM_MODEL
        self._api_key = api_key or os.getenv("OPENAI_API_KEY") or config.OPENAI_API_KEY

        if not self._api_key:
            logger.warning("OpenAI API Key is missing. Provider will fail if generate() is called.")

        self._default_temp = config.LLM_TEMPERATURE
        self._default_max_tokens = config.LLM_MAX_OUTPUT_TOKENS

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        if not self._api_key:
            raise ValueError(
                "OPENAI_API_KEY is not configured in environment or .env file. "
                "Please configure OPENAI_API_KEY or set LLM_PROVIDER=mock for offline testing."
            )

        temp = temperature if temperature is not None else self._default_temp
        max_tok = max_tokens if max_tokens is not None else self._default_max_tokens

        lc_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            else:
                lc_messages.append(HumanMessage(content=content))

        try:
            llm = ChatOpenAI(
                model=self._model_name,
                api_key=self._api_key,
                temperature=temp,
                max_tokens=max_tok,
            )
            response = llm.invoke(lc_messages)
            return response.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise RuntimeError(f"OpenAI generation failure: {e}") from e

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model_name
