"""
Generation package for LLM provider client, grounded prompt templates, context formatting, and citation building.
"""
from src.generation.models import Citation, GenerationMetrics, GenerationResponse
from src.generation.provider import LLMProvider
from src.generation.mock_provider import MockLLMProvider
from src.generation.openai_provider import OpenAIProvider
from src.generation.factory import get_llm_provider
from src.generation.context import ContextBuilder
from src.generation.citation import CitationBuilder
from src.generation.prompts import GroundedPrompts
from src.generation.service import MedicalGenerationService

__all__ = [
    "Citation",
    "GenerationMetrics",
    "GenerationResponse",
    "LLMProvider",
    "MockLLMProvider",
    "OpenAIProvider",
    "get_llm_provider",
    "ContextBuilder",
    "CitationBuilder",
    "GroundedPrompts",
    "MedicalGenerationService",
]
