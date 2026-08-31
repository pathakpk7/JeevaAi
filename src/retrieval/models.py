from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RetrievalResult(BaseModel):
    """
    Structured retrieval result representing a single grounded text chunk
    retrieved from the medical knowledge vector index.
    """
    chunk_id: str = Field(description="Unique deterministic MD5 chunk signature")
    text: str = Field(description="Cleaned text content of the retrieved chunk")
    score: float = Field(description="Normalized similarity score [0.0 to 1.0]")
    source: str = Field(description="Absolute file path to source PDF")
    document_name: str = Field(description="Source PDF filename")
    page: int = Field(description="1-indexed page number in the original PDF")
    article_title: str = Field(description="Detected medical article/topic title")
    section: str = Field(description="Detected section heading (e.g. Definition, Treatment)")
    length: int = Field(description="Character length of chunk text")

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to serializable dictionary."""
        return self.model_dump()

class RetrievalResponse(BaseModel):
    """
    Container object returned by the retrieval engine for a user query.
    """
    query: str = Field(description="Original user search query string")
    top_k: int = Field(description="Top-K parameter used for vector search")
    min_score: float = Field(description="Minimum similarity threshold applied")
    result_count: int = Field(description="Number of chunks matching threshold criteria")
    retrieval_duration_ms: float = Field(description="Retrieval execution latency in milliseconds")
    match_quality: str = Field(description="Qualitative match assessment: Strong, Limited, or None")
    results: List[RetrievalResult] = Field(default_factory=list, description="Ordered list of retrieval results")

    def is_empty(self) -> bool:
        return len(self.results) == 0
