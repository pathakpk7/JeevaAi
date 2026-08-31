from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from src.retrieval.models import RetrievalResult

class Citation(BaseModel):
    """
    Programmatically constructed source citation object.
    Never generated or modified by the LLM.
    """
    document_name: str = Field(description="Source PDF filename")
    page: int = Field(description="1-indexed page number")
    article_title: str = Field(description="Medical entry topic title")
    section: str = Field(description="Section heading (Definition, Treatment, etc.)")
    chunk_id: str = Field(description="Deterministic chunk MD5 signature")
    snippet: str = Field(default="", description="Text excerpt extracted from the specific section")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

class GenerationMetrics(BaseModel):
    """
    Execution metrics and latency diagnostic parameters.
    """
    retrieval_latency_ms: float = Field(description="Retrieval vector search duration in ms")
    generation_latency_ms: float = Field(description="LLM generation duration in ms")
    total_latency_ms: float = Field(description="Total end-to-end processing duration in ms")
    chunks_used: int = Field(description="Number of context chunks passed to LLM")
    llm_provider: str = Field(description="Configured LLM provider name")
    llm_model: str = Field(description="Configured LLM model identifier")

class GenerationResponse(BaseModel):
    """
    Complete grounded response container returned by MedicalGenerationService.
    """
    question: str = Field(description="Original user question string")
    answer: str = Field(description="Grounded educational response text")
    match_quality: str = Field(description="Retrieval match quality: Strong, Limited, or None")
    citations: List[Citation] = Field(default_factory=list, description="Deduplicated programmatic citations")
    retrieval_results: List[RetrievalResult] = Field(default_factory=list, description="Original retrieved chunks")
    metrics: GenerationMetrics = Field(description="Execution latency and diagnostic metrics")
    medical_disclaimer: str = Field(
        default="Informational Medical Knowledge Assistant. For educational purposes only. Not a substitute for professional medical advice, diagnosis, or treatment.",
        description="Standard medical safety disclaimer"
    )

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
